import os
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# Try to import LangGraph implementation
try:
    from .langgraph_fact_verification import LangGraphFactVerificationService
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    LangGraphFactVerificationService = None
    logger = logging.getLogger(__name__)
    logger.warning(f"LangGraph not available: {str(e)}. Using simplified implementation.")

# Simple OpenAI imports without LangChain
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Tool imports - with error handling
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

try:
    from pymed import PubMed
    PUBMED_AVAILABLE = True
except ImportError:
    PUBMED_AVAILABLE = False
    PubMed = None

try:
    from scholarly import scholarly
    SEMANTIC_SCHOLAR_AVAILABLE = True
except ImportError:
    SEMANTIC_SCHOLAR_AVAILABLE = False
    scholarly = None

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None
    BeautifulSoup = None

# Local imports
from ..models.fact_verification import (
    VerificationStatus, SourceType, VerificationSource, ClaimVerification,
    FactVerificationRequest, FactVerificationResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FactVerificationAgent:
    """Simplified fact verification agent using direct OpenAI API"""
    
    def __init__(self):
        self.client = None
        if os.getenv("OPENAI_API_KEY") and OPENAI_AVAILABLE:
            try:
                self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
        
        self.pubmed = None
        if PUBMED_AVAILABLE:
            try:
                self.pubmed = PubMed(tool="PodSearch", email="verification@podsearch.com")
            except Exception as e:
                logger.warning(f"Failed to initialize PubMed: {str(e)}")
    
    def wikipedia_search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search Wikipedia for information about a query"""
        if not WIKIPEDIA_AVAILABLE:
            return []
            
        try:
            wikipedia.set_lang("en")
            search_results = wikipedia.search(query, results=max_results)
            sources = []
            
            for title in search_results[:max_results]:
                try:
                    page = wikipedia.page(title)
                    sources.append({
                        "title": page.title,
                        "url": page.url,
                        "summary": page.summary[:500],
                        "source_type": "Wikipedia"
                    })
                except wikipedia.exceptions.DisambiguationError as e:
                    if e.options:
                        try:
                            page = wikipedia.page(e.options[0])
                            sources.append({
                                "title": page.title,
                                "url": page.url,
                                "summary": page.summary[:500],
                                "source_type": "Wikipedia"
                            })
                        except:
                            continue
                except:
                    continue
                    
            return sources
        except Exception as e:
            logger.error(f"Wikipedia search error: {str(e)}")
            return []
    
    def duckduckgo_search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search DuckDuckGo for general information"""
        if not DUCKDUCKGO_AVAILABLE:
            return []
            
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                sources = []
                
                for result in results:
                    sources.append({
                        "title": result.get('title', ''),
                        "url": result.get('href', ''),
                        "summary": result.get('body', '')[:500],
                        "source_type": "Web Search"
                    })
                    
                return sources
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return []
    
    def pubmed_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search PubMed for scientific articles about a query"""
        if not PUBMED_AVAILABLE or not self.pubmed:
            return []
            
        try:
            results = self.pubmed.query(query, max_results=max_results)
            sources = []
            
            for article in results:
                if hasattr(article, 'title') and hasattr(article, 'abstract'):
                    sources.append({
                        "title": article.title,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/",
                        "summary": article.abstract[:500] if article.abstract else "",
                        "authors": getattr(article, 'authors', []),
                        "publication_date": getattr(article, 'publication_date', None),
                        "source_type": "PubMed"
                    })
                    
            return sources
        except Exception as e:
            logger.error(f"PubMed search error: {str(e)}")
            return []
    
    def semantic_scholar_search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search Semantic Scholar for academic papers"""
        if not SEMANTIC_SCHOLAR_AVAILABLE:
            return []
            
        try:
            search_results = scholarly.search_pubs(query)
            sources = []
            
            for i, paper in enumerate(search_results):
                if i >= max_results:
                    break
                    
                try:
                    filled_paper = scholarly.fill(paper)
                    sources.append({
                        "title": filled_paper.get('bib', {}).get('title', 'Unknown Title'),
                        "url": filled_paper.get('pub_url', filled_paper.get('eprint_url', '')),
                        "summary": filled_paper.get('bib', {}).get('abstract', '')[:500],
                        "authors": filled_paper.get('bib', {}).get('author', []),
                        "publication_date": filled_paper.get('bib', {}).get('pub_year', None),
                        "source_type": "Semantic Scholar"
                    })
                except Exception as e:
                    logger.warning(f"Error processing Semantic Scholar result: {str(e)}")
                    continue
                    
            return sources
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {str(e)}")
            return []
    
    def _search_multiple_sources(self, claim: str) -> List[Dict[str, Any]]:
        """Search multiple sources for information about a claim"""
        all_sources = []
        
        # Search Wikipedia for all claims
        wiki_sources = self.wikipedia_search(claim, max_results=2)
        all_sources.extend(wiki_sources)
        
        # Search DuckDuckGo for all claims
        web_sources = self.duckduckgo_search(claim, max_results=2)
        all_sources.extend(web_sources)
        
        # Search PubMed for scientific claims OR any claim with factual content
        if any(keyword in claim.lower() for keyword in ['study', 'research', 'percent', '%', 'shows', 'medical', 'health', 'discovered', 'invented', 'created', 'founded', 'theory', 'evidence', 'data']):
            pubmed_sources = self.pubmed_search(claim, max_results=2)
            all_sources.extend(pubmed_sources)
        
        # Search Semantic Scholar for academic/scientific claims
        if any(keyword in claim.lower() for keyword in ['theory', 'research', 'study', 'discovered', 'invented', 'scientific', 'academic', 'university', 'professor']):
            scholar_sources = self.semantic_scholar_search(claim, max_results=2)
            all_sources.extend(scholar_sources)
        
        return all_sources
    
    def _analyze_sources_and_verify(self, claim: str, sources: List[Dict[str, Any]]) -> ClaimVerification:
        """Analyze sources and verify the claim using OpenAI API directly"""
        if not self.client or not sources:
            return self._fallback_verification(claim, sources)
        
        try:
            # Prepare sources summary
            sources_text = ""
            for i, source in enumerate(sources[:5], 1):
                sources_text += f"\nSource {i} ({source.get('source_type', 'Unknown')}):\n"
                sources_text += f"Title: {source.get('title', 'N/A')}\n"
                sources_text += f"URL: {source.get('url', 'N/A')}\n"
                sources_text += f"Summary: {source.get('summary', 'N/A')}\n"
            
            prompt = f"""
            As a fact-checking expert, analyze the following claim against the provided sources:

            CLAIM: "{claim}"

            SOURCES:
            {sources_text}

            Please provide your analysis in the following format:

            VERIFICATION STATUS: [Choose one: VERIFIED, PARTIALLY_VERIFIED, FALSE, or UNCLEAR]
            CONFIDENCE: [0.0-1.0]
            EXPLANATION: [Detailed explanation of your reasoning, citing specific sources]

            Guidelines:
            - VERIFIED: Claim is supported by reliable sources
            - PARTIALLY_VERIFIED: Claim has some truth but needs context/clarification  
            - FALSE: Claim is contradicted by reliable sources
            - UNCLEAR: Insufficient evidence or conflicting information

            Consider source reliability, recency, and relevance in your analysis.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert fact-checker who analyzes claims against provided sources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
            # Extract verification components
            status = self._extract_status_from_analysis(analysis)
            confidence = self._extract_confidence_from_analysis(analysis)
            explanation = self._extract_explanation_from_analysis(analysis)
            
            # Convert sources to VerificationSource objects
            verification_sources = []
            for source in sources[:5]:
                # Determine source type based on source_type field
                source_type_mapping = {
                    'PubMed': SourceType.PUBMED,
                    'Wikipedia': SourceType.WIKIPEDIA,
                    'Semantic Scholar': SourceType.ACADEMIC,
                    'Web Search': SourceType.SEARCH_ENGINE
                }
                
                verification_sources.append(VerificationSource(
                    title=source.get('title', 'Unknown'),
                    url=source.get('url', ''),
                    excerpt=source.get('summary', '')[:200],
                    source_type=source_type_mapping.get(source.get('source_type'), SourceType.SEARCH_ENGINE),
                    relevance_score=0.8
                ))
            
            return ClaimVerification(
                claim=claim,
                status=status,
                confidence=confidence,
                explanation=explanation,
                sources=verification_sources,
                verification_date=datetime.now(),
                agent_reasoning=f"Analyzed {len(sources)} sources using OpenAI GPT-4. {explanation[:200]}..."
            )
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {str(e)}")
            return self._fallback_verification(claim, sources)
    
    def _extract_status_from_analysis(self, analysis: str) -> VerificationStatus:
        """Extract verification status from analysis"""
        analysis_lower = analysis.lower()
        if "verified" in analysis_lower and "partially" not in analysis_lower:
            return VerificationStatus.VERIFIED
        elif "partially" in analysis_lower or "partial" in analysis_lower:
            return VerificationStatus.PARTIALLY_VERIFIED
        elif "false" in analysis_lower or "incorrect" in analysis_lower:
            return VerificationStatus.FALSE
        else:
            return VerificationStatus.UNCLEAR
    
    def _extract_confidence_from_analysis(self, analysis: str) -> float:
        """Extract confidence score from analysis"""
        confidence_match = re.search(r'confidence[:\s]*([0-9]*\.?[0-9]+)', analysis.lower())
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                return min(max(confidence, 0.0), 1.0)
            except ValueError:
                pass
        
        # Fallback based on status keywords
        analysis_lower = analysis.lower()
        if "high confidence" in analysis_lower or "very confident" in analysis_lower:
            return 0.9
        elif "confident" in analysis_lower:
            return 0.8
        elif "moderate" in analysis_lower or "somewhat" in analysis_lower:
            return 0.6
        elif "low confidence" in analysis_lower or "uncertain" in analysis_lower:
            return 0.4
        else:
            return 0.5
    
    def _extract_explanation_from_analysis(self, analysis: str) -> str:
        """Extract explanation from analysis"""
        explanation_match = re.search(r'explanation[:\s]*(.+?)(?:\n\n|\Z)', analysis, re.IGNORECASE | re.DOTALL)
        if explanation_match:
            return explanation_match.group(1).strip()
        
        # Fallback: return the analysis after removing the status and confidence lines
        lines = analysis.split('\n')
        explanation_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['verification status', 'confidence:', 'explanation:']):
                if 'explanation:' in line_lower:
                    explanation_lines.append(line.split(':', 1)[-1].strip())
                continue
            explanation_lines.append(line)
        
        return '\n'.join(explanation_lines).strip() or "Analysis completed based on available sources."
    
    async def verify_claims(self, claims: List[str], search_depth: int = 3) -> List[ClaimVerification]:
        """Verify multiple claims"""
        results = []
        
        for claim in claims:
            start_time = time.time()
            
            try:
                # Search for sources
                sources = self._search_multiple_sources(claim)
                
                # Verify the claim
                verification = self._analyze_sources_and_verify(claim, sources)
                
                # Processing time is tracked at response level
                
                results.append(verification)
                
            except Exception as e:
                logger.error(f"Error verifying claim '{claim}': {str(e)}")
                results.append(ClaimVerification(
                    claim=claim,
                    status=VerificationStatus.UNCLEAR,
                    confidence=0.0,
                    explanation=f"Error during verification: {str(e)}",
                    sources=[],
                    verification_date=datetime.now(),
                    agent_reasoning=""
                ))
        
        return results
    
    def _fallback_verification(self, claim: str, sources: List[Dict[str, Any]]) -> ClaimVerification:
        """Fallback verification when OpenAI is not available"""
        verification_sources = []
        for source in sources[:3]:
            verification_sources.append(VerificationSource(
                title=source.get('title', 'Unknown'),
                url=source.get('url', ''),
                excerpt=source.get('summary', '')[:200],
                source_type=SourceType.SEARCH_ENGINE,
                relevance_score=0.5
            ))
        
        # Simple heuristic based on number of sources
        if len(sources) >= 3:
            status = VerificationStatus.PARTIALLY_VERIFIED
            confidence = 0.6
            explanation = f"Found {len(sources)} sources. Manual review recommended for full verification."
        elif len(sources) >= 1:
            status = VerificationStatus.UNCLEAR
            confidence = 0.4
            explanation = f"Found {len(sources)} source(s). Insufficient evidence for verification."
        else:
            status = VerificationStatus.UNCLEAR
            confidence = 0.1
            explanation = "No sources found. Unable to verify claim."
        
        return ClaimVerification(
            claim=claim,
            status=status,
            confidence=confidence,
            explanation=explanation,
            sources=verification_sources,
            verification_date=datetime.now(),
            agent_reasoning=""
        )

class FactVerificationService:
    """Main fact verification service with LangGraph support"""
    
    def __init__(self, use_langgraph: bool = True):
        self.use_langgraph = use_langgraph and LANGGRAPH_AVAILABLE
        self.agent = FactVerificationAgent()  # Fallback agent
        
        if self.use_langgraph:
            try:
                self.langgraph_service = LangGraphFactVerificationService()
                logger.info("🚀 LangGraph fact verification service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LangGraph service: {str(e)}. Using fallback.")
                self.use_langgraph = False
                self.langgraph_service = None
        else:
            self.langgraph_service = None
            logger.info("📋 Using simplified fact verification service")
    
    async def verify_facts(self, request: FactVerificationRequest) -> FactVerificationResponse:
        """Verify a list of claims using LangGraph or fallback implementation"""
        start_time = time.time()
        
        try:
            # Use LangGraph if available and enabled
            if self.use_langgraph and self.langgraph_service:
                logger.info(f"🎯 Using LangGraph workflow for {len(request.claims)} claims")
                
                result = await self.langgraph_service.verify_claims(request.claims)
                
                if result["success"]:
                    # Convert LangGraph results to our standard format
                    verifications = self._convert_langgraph_results(result["verifications"])
                    
                    return FactVerificationResponse(
                        success=True,
                        verifications=verifications,
                        total_claims=len(request.claims),
                        processing_time=result["processing_time"]
                    )
                else:
                    logger.warning("LangGraph verification failed, falling back to simplified method")
                    # Fall through to simplified method
            
            # Fallback to simplified method
            logger.info(f"📋 Using simplified workflow for {len(request.claims)} claims")
            verifications = await self.agent.verify_claims(
                request.claims, 
                search_depth=request.search_depth
            )
            
            processing_time = time.time() - start_time
            
            return FactVerificationResponse(
                success=True,
                verifications=verifications,
                total_claims=len(request.claims),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Fact verification error: {str(e)}")
            processing_time = time.time() - start_time
            
            return FactVerificationResponse(
                success=False,
                verifications=[],
                total_claims=len(request.claims),
                processing_time=processing_time,
                error=str(e)
            )
    
    def _convert_langgraph_results(self, langgraph_results: List[Dict[str, Any]]) -> List[ClaimVerification]:
        """Convert LangGraph results to our standard ClaimVerification format"""
        verifications = []
        
        for result in langgraph_results:
            try:
                # Parse the verification response
                claim = result.get("claim", "")
                verification_text = result.get("verification_response", "")
                
                # Extract status, confidence, and explanation from LangGraph response
                status = self._parse_status_from_text(verification_text)
                confidence = self._parse_confidence_from_text(verification_text)
                explanation = verification_text
                
                # Create sources (simplified for now)
                sources = []
                evidence_sources = result.get("evidence_sources", 0)
                if evidence_sources > 0:
                    sources.append(VerificationSource(
                        title="LangGraph Multi-Source Analysis",
                        url="",
                        source_type=SourceType.SEARCH_ENGINE,
                        relevance_score=0.8,
                        excerpt=f"Analysis from {evidence_sources} sources"
                    ))
                
                verification = ClaimVerification(
                    claim=claim,
                    status=status,
                    confidence=confidence,
                    explanation=explanation,
                    sources=sources,
                    agent_reasoning=f"LangGraph workflow with {evidence_sources} sources analyzed"
                )
                
                verifications.append(verification)
                
            except Exception as e:
                logger.error(f"Error converting LangGraph result: {str(e)}")
                # Create a fallback verification
                verification = ClaimVerification(
                    claim=result.get("claim", "Unknown claim"),
                    status=VerificationStatus.UNCLEAR,
                    confidence=0.0,
                    explanation=f"Error processing LangGraph result: {str(e)}",
                    sources=[],
                    agent_reasoning="LangGraph processing error"
                )
                verifications.append(verification)
        
        return verifications
    
    def _parse_status_from_text(self, text: str) -> VerificationStatus:
        """Parse verification status from LangGraph response text"""
        text_lower = text.lower()
        
        if "✅" in text or ("verified" in text_lower and "false" not in text_lower):
            return VerificationStatus.VERIFIED
        elif "❌" in text or "false" in text_lower:
            return VerificationStatus.FALSE
        elif "⚠️" in text or "partially" in text_lower:
            return VerificationStatus.PARTIALLY_VERIFIED
        else:
            return VerificationStatus.UNCLEAR
    
    def _parse_confidence_from_text(self, text: str) -> float:
        """Parse confidence score from LangGraph response text"""
        import re
        
        # Look for confidence patterns
        confidence_patterns = [
            r"confidence[:\s]*(\d*\.?\d+)",
            r"(\d*\.?\d+)[:\s]*confidence",
            r"score[:\s]*(\d*\.?\d+)",
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    score = float(match.group(1))
                    return min(max(score, 0.0), 1.0)  # Clamp between 0-1
                except ValueError:
                    continue
        
        # Default confidence based on status keywords
        text_lower = text.lower()
        if "definitely" in text_lower or "certain" in text_lower:
            return 0.9
        elif "likely" in text_lower or "probably" in text_lower:
            return 0.7
        elif "possibly" in text_lower or "might" in text_lower:
            return 0.5
        else:
            return 0.6  # Default moderate confidence
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification service statistics"""
        return {
            "service_status": "active",
            "available_sources": {
                "wikipedia": WIKIPEDIA_AVAILABLE,
                "duckduckgo": DUCKDUCKGO_AVAILABLE,
                "pubmed": PUBMED_AVAILABLE,
                "semantic_scholar": SEMANTIC_SCHOLAR_AVAILABLE,
                "openai": OPENAI_AVAILABLE,
                "langgraph": LANGGRAPH_AVAILABLE
            },
            "workflow_type": "LangGraph" if self.use_langgraph else "Simplified",
            "openai_client_available": self.agent.client is not None,
            "last_check": datetime.now().isoformat()
        } 