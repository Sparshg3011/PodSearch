"""
LangGraph-based Fact Verification Workflow
Real implementation using LangGraph agents and state management
"""

import os
import time
import logging
from typing import List, Dict, Any, TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
# Import available tools with fallbacks
try:
    from langchain_community.utilities import WikipediaAPIWrapper
    WIKIPEDIA_WRAPPER_AVAILABLE = True
except ImportError:
    WIKIPEDIA_WRAPPER_AVAILABLE = False
    WikipediaAPIWrapper = None

try:
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
    DUCKDUCKGO_WRAPPER_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_WRAPPER_AVAILABLE = False
    DuckDuckGoSearchAPIWrapper = None

# Use simple implementations for tools not available
try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False
    wikipedia = None

try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    DDGS = None
import asyncio
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FactVerificationState(TypedDict):
    """State for the LangGraph fact verification workflow"""
    input_claims: List[str]
    current_claim: str
    claim_index: int
    
    # Search results from different agents
    wikipedia_results: Dict[str, Any]
    pubmed_results: Dict[str, Any]
    semantic_scholar_results: Dict[str, Any]
    duckduckgo_results: Dict[str, Any]
    
    # Analysis results
    evidence_analysis: Dict[str, Any]
    verification_result: Dict[str, Any]
    
    # Final output
    all_verifications: List[Dict[str, Any]]
    processing_errors: List[str]
    
    # Workflow control
    completed_claims: int
    total_claims: int

class LangGraphFactVerificationService:
    """LangGraph-based fact verification with multiple agents"""
    
    def __init__(self):
        self.llm = self._setup_llm()
        self.search_tools = self._setup_search_tools()
        self.graph = self._build_workflow()
        
    def _setup_llm(self):
        """Initialize OpenAI LLM"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        
        return ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            api_key=api_key
        )
    
    def _setup_search_tools(self):
        """Initialize search tools for different sources"""
        tools = {}
        
        # Wikipedia setup
        if WIKIPEDIA_WRAPPER_AVAILABLE:
            try:
                tools["wikipedia"] = WikipediaAPIWrapper()
            except Exception as e:
                logger.warning(f"Wikipedia wrapper unavailable: {e}")
                tools["wikipedia"] = None
        elif WIKIPEDIA_AVAILABLE:
            tools["wikipedia"] = "simple_wikipedia"  # Use simple implementation
        else:
            tools["wikipedia"] = None
            
        # DuckDuckGo setup
        if DUCKDUCKGO_WRAPPER_AVAILABLE:
            try:
                tools["duckduckgo"] = DuckDuckGoSearchAPIWrapper()
            except Exception as e:
                logger.warning(f"DuckDuckGo wrapper unavailable: {e}")
                tools["duckduckgo"] = None
        elif DUCKDUCKGO_AVAILABLE:
            tools["duckduckgo"] = "simple_duckduckgo"  # Use simple implementation
        else:
            tools["duckduckgo"] = None
        
        # For now, disable complex tools that have import issues
        tools["pubmed"] = None
        tools["semantic_scholar"] = None
            
        return tools
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        # Create workflow
        workflow = StateGraph(FactVerificationState)
        
        # Add nodes (agents)
        workflow.add_node("initialize", self.initialize_verification)
        workflow.add_node("wikipedia_search", self.wikipedia_search_agent)
        workflow.add_node("pubmed_search", self.pubmed_search_agent)
        workflow.add_node("semantic_search", self.semantic_scholar_agent)
        workflow.add_node("duckduckgo_search", self.duckduckgo_search_agent)
        workflow.add_node("evidence_analyzer", self.evidence_analysis_agent)
        workflow.add_node("final_verifier", self.final_verification_agent)
        workflow.add_node("claim_processor", self.process_next_claim)
        
        # Define the workflow edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "wikipedia_search")
        workflow.add_edge("wikipedia_search", "pubmed_search")
        workflow.add_edge("pubmed_search", "semantic_search")
        workflow.add_edge("semantic_search", "duckduckgo_search")
        workflow.add_edge("duckduckgo_search", "evidence_analyzer")
        workflow.add_edge("evidence_analyzer", "final_verifier")
        workflow.add_edge("final_verifier", "claim_processor")
        
        # Conditional edge for continuing or ending
        workflow.add_conditional_edges(
            "claim_processor",
            self.should_continue,
            {
                "continue": "wikipedia_search",
                "end": END
            }
        )
        
        # Compile the graph
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def initialize_verification(self, state: FactVerificationState):
        """Initialize the verification process"""
        logger.info(f"🚀 Initializing verification for {len(state['input_claims'])} claims")
        
        return {
            **state,
            "current_claim": state["input_claims"][0] if state["input_claims"] else "",
            "claim_index": 0,
            "completed_claims": 0,
            "total_claims": len(state["input_claims"]),
            "all_verifications": [],
            "processing_errors": []
        }
    
    async def wikipedia_search_agent(self, state: FactVerificationState):
        """Wikipedia search agent"""
        claim = state["current_claim"]
        logger.info(f"🔍 Wikipedia searching: {claim}")
        
        results = {"source": "wikipedia", "results": [], "error": None}
        
        tool = self.search_tools["wikipedia"]
        if tool:
            try:
                if tool == "simple_wikipedia":
                    # Use simple wikipedia implementation
                    search_results = self._simple_wikipedia_search(claim)
                else:
                    # Use LangChain wrapper
                    search_results = tool.run(claim)
                
                results["results"] = [{"content": search_results, "relevance": 0.8}]
                logger.info(f"✅ Wikipedia found results")
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"❌ Wikipedia search failed: {e}")
        else:
            results["error"] = "Wikipedia tool not available"
            
        return {**state, "wikipedia_results": results}
    
    def _simple_wikipedia_search(self, query: str) -> str:
        """Simple Wikipedia search implementation"""
        if not WIKIPEDIA_AVAILABLE:
            return "Wikipedia not available"
        
        try:
            wikipedia.set_lang("en")
            search_results = wikipedia.search(query, results=3)
            
            if not search_results:
                return f"No Wikipedia results found for '{query}'"
            
            # Get the first result
            page = wikipedia.page(search_results[0])
            return f"Title: {page.title}\nSummary: {page.summary[:500]}..."
            
        except wikipedia.exceptions.DisambiguationError as e:
            if e.options:
                try:
                    page = wikipedia.page(e.options[0])
                    return f"Title: {page.title}\nSummary: {page.summary[:500]}..."
                except:
                    return f"Wikipedia disambiguation error for '{query}'"
            return f"Wikipedia disambiguation error for '{query}'"
        except Exception as e:
            return f"Wikipedia search error: {str(e)}"
    
    async def pubmed_search_agent(self, state: FactVerificationState):
        """PubMed search agent for medical/scientific claims"""
        claim = state["current_claim"]
        logger.info(f"🧬 PubMed searching: {claim}")
        
        results = {"source": "pubmed", "results": [], "error": None}
        
        if self.search_tools["pubmed"]:
            try:
                search_results = self.search_tools["pubmed"].run(claim)
                results["results"] = [{"content": search_results, "relevance": 0.9}]
                logger.info(f"✅ PubMed found results")
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"❌ PubMed search failed: {e}")
        else:
            results["error"] = "PubMed tool not available"
            
        return {**state, "pubmed_results": results}
    
    async def semantic_scholar_agent(self, state: FactVerificationState):
        """Semantic Scholar search agent for academic papers"""
        claim = state["current_claim"]
        logger.info(f"📚 Semantic Scholar searching: {claim}")
        
        results = {"source": "semantic_scholar", "results": [], "error": None}
        
        if self.search_tools["semantic_scholar"]:
            try:
                search_results = self.search_tools["semantic_scholar"].run(claim)
                results["results"] = [{"content": search_results, "relevance": 0.85}]
                logger.info(f"✅ Semantic Scholar found results")
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"❌ Semantic Scholar search failed: {e}")
        else:
            results["error"] = "Semantic Scholar tool not available"
            
        return {**state, "semantic_scholar_results": results}
    
    async def duckduckgo_search_agent(self, state: FactVerificationState):
        """DuckDuckGo search agent for general web search"""
        claim = state["current_claim"]
        logger.info(f"🦆 DuckDuckGo searching: {claim}")
        
        results = {"source": "duckduckgo", "results": [], "error": None}
        
        tool = self.search_tools["duckduckgo"]
        if tool:
            try:
                if tool == "simple_duckduckgo":
                    # Use simple DuckDuckGo implementation
                    search_results = self._simple_duckduckgo_search(claim)
                else:
                    # Use LangChain wrapper
                    search_results = tool.run(claim)
                
                results["results"] = [{"content": search_results, "relevance": 0.7}]
                logger.info(f"✅ DuckDuckGo found results")
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"❌ DuckDuckGo search failed: {e}")
        else:
            results["error"] = "DuckDuckGo tool not available"
            
        return {**state, "duckduckgo_results": results}
    
    def _simple_duckduckgo_search(self, query: str) -> str:
        """Simple DuckDuckGo search implementation"""
        if not DUCKDUCKGO_AVAILABLE:
            return "DuckDuckGo search not available"
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                
                if not results:
                    return f"No DuckDuckGo results found for '{query}'"
                
                # Format results
                formatted_results = []
                for result in results:
                    title = result.get('title', 'No title')
                    body = result.get('body', 'No content')[:200]
                    formatted_results.append(f"Title: {title}\nContent: {body}...")
                
                return "\n\n".join(formatted_results)
                
        except Exception as e:
            return f"DuckDuckGo search error: {str(e)}"
    
    async def evidence_analysis_agent(self, state: FactVerificationState):
        """Analyze all evidence from different sources"""
        claim = state["current_claim"]
        logger.info(f"🔬 Analyzing evidence for: {claim}")
        
        # Collect all search results
        all_evidence = {
            "wikipedia": state.get("wikipedia_results", {}),
            "pubmed": state.get("pubmed_results", {}), 
            "semantic_scholar": state.get("semantic_scholar_results", {}),
            "duckduckgo": state.get("duckduckgo_results", {})
        }
        
        # Use LLM to analyze evidence
        analysis_prompt = f"""
        Analyze the following evidence for the claim: "{claim}"
        
        Evidence from different sources:
        {json.dumps(all_evidence, indent=2)}
        
        Provide a structured analysis including:
        1. Quality of evidence from each source
        2. Consistency across sources
        3. Reliability assessment
        4. Key supporting/contradicting points
        
        Return analysis as structured data.
        """
        
        try:
            analysis_response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert evidence analyst. Analyze evidence objectively and thoroughly."),
                HumanMessage(content=analysis_prompt)
            ])
            
            analysis = {
                "claim": claim,
                "evidence_summary": analysis_response.content,
                "sources_analyzed": len([s for s in all_evidence.values() if s.get("results")]),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            analysis = {
                "claim": claim,
                "error": f"Analysis failed: {str(e)}",
                "sources_analyzed": 0
            }
            logger.error(f"❌ Evidence analysis failed: {e}")
        
        return {**state, "evidence_analysis": analysis}
    
    async def final_verification_agent(self, state: FactVerificationState):
        """Final verification decision based on all evidence"""
        claim = state["current_claim"]
        evidence_analysis = state.get("evidence_analysis", {})
        
        logger.info(f"⚖️ Making final verification decision for: {claim}")
        
        verification_prompt = f"""
        Make a final verification decision for this claim: "{claim}"
        
        Based on the evidence analysis:
        {evidence_analysis.get('evidence_summary', 'No analysis available')}
        
        Provide a final verdict with:
        1. Status: ✅ Verified, ⚠️ Partially Verified, ❌ False, or 🔍 Unclear
        2. Confidence score (0-1)
        3. Reasoning for the decision
        4. Key supporting evidence
        
        Be strict but fair in your assessment.
        """
        
        try:
            verification_response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert fact-checker. Make accurate, evidence-based decisions."),
                HumanMessage(content=verification_prompt)
            ])
            
            verification = {
                "claim": claim,
                "verification_response": verification_response.content,
                "timestamp": datetime.now().isoformat(),
                "evidence_sources": state.get("evidence_analysis", {}).get("sources_analyzed", 0)
            }
            
        except Exception as e:
            verification = {
                "claim": claim,
                "error": f"Verification failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ Final verification failed: {e}")
        
        return {**state, "verification_result": verification}
    
    async def process_next_claim(self, state: FactVerificationState):
        """Process the next claim or finish if done"""
        # Save current verification result
        current_verification = state.get("verification_result", {})
        all_verifications = state.get("all_verifications", [])
        all_verifications.append(current_verification)
        
        completed = state["completed_claims"] + 1
        total = state["total_claims"]
        
        logger.info(f"📊 Completed {completed}/{total} claims")
        
        # Check if more claims to process
        if completed < total:
            next_claim = state["input_claims"][completed]
            return {
                **state,
                "current_claim": next_claim,
                "claim_index": completed,
                "completed_claims": completed,
                "all_verifications": all_verifications,
                # Reset search results for next claim
                "wikipedia_results": {},
                "pubmed_results": {},
                "semantic_scholar_results": {},
                "duckduckgo_results": {},
                "evidence_analysis": {},
                "verification_result": {}
            }
        else:
            return {
                **state,
                "completed_claims": completed,
                "all_verifications": all_verifications
            }
    
    def should_continue(self, state: FactVerificationState):
        """Decide whether to continue processing more claims"""
        if state["completed_claims"] < state["total_claims"]:
            return "continue"
        else:
            return "end"
    
    async def verify_claims(self, claims: List[str]) -> Dict[str, Any]:
        """Main entry point for LangGraph fact verification"""
        logger.info(f"🚀 Starting LangGraph fact verification for {len(claims)} claims")
        start_time = time.time()
        
        try:
            # Initialize state
            initial_state = {
                "input_claims": claims,
                "current_claim": "",
                "claim_index": 0,
                "wikipedia_results": {},
                "pubmed_results": {},
                "semantic_scholar_results": {},
                "duckduckgo_results": {},
                "evidence_analysis": {},
                "verification_result": {},
                "all_verifications": [],
                "processing_errors": [],
                "completed_claims": 0,
                "total_claims": len(claims)
            }
            
            # Run the workflow
            config = {"configurable": {"thread_id": f"fact_check_{int(time.time())}"}}
            result = await self.graph.ainvoke(initial_state, config)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "verifications": result["all_verifications"],
                "total_claims": len(claims),
                "processing_time": processing_time,
                "workflow_type": "LangGraph",
                "error": None
            }
            
        except Exception as e:
            logger.error(f"❌ LangGraph workflow failed: {e}")
            return {
                "success": False,
                "verifications": [],
                "total_claims": len(claims),
                "processing_time": time.time() - start_time,
                "workflow_type": "LangGraph",
                "error": str(e)
            } 