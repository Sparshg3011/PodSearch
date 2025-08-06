import os
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Try to import ChromaDB, but make it optional
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("ChromaDB imported successfully")
except ImportError as e:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None
    logger = logging.getLogger(__name__)
    logger.warning(f"ChromaDB not available: {str(e)}. RAG service will use in-memory storage.")

# Enhanced text splitter with better sentence boundary awareness
def enhanced_text_splitter(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Enhanced text splitter that respects sentence boundaries and maintains context"""
    if len(text) <= chunk_size:
        return [text]
    
    # Split into sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) <= 1:
        # Fallback to word splitting if no sentence boundaries
        words = text.split()
        if len(words) <= chunk_size // 10:  # Rough estimate
            return [text]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                # Keep some words for overlap
                overlap_words = min(overlap // 10, len(current_chunk) // 2)
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_length = sum(len(w) + 1 for w in current_chunk)
            
            current_chunk.append(word)
            current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return [c for c in chunks if c.strip()]
    
    # Group sentences into chunks
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        # If adding this sentence would exceed chunk size and we have content
        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            
            # Calculate overlap in sentences
            overlap_sentences = []
            overlap_length = 0
            for i in range(len(current_chunk) - 1, -1, -1):
                sentence_len = len(current_chunk[i])
                if overlap_length + sentence_len <= overlap:
                    overlap_sentences.insert(0, current_chunk[i])
                    overlap_length += sentence_len
                else:
                    break
            
            current_chunk = overlap_sentences
            current_length = overlap_length
        
        current_chunk.append(sentence)
        current_length += sentence_length + 1  # +1 for space
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return [c.strip() for c in chunks if c.strip()]

def enhance_query(query: str) -> List[str]:
    """Enhance query with related terms and variations"""
    enhanced_queries = [query]
    
    # Always add question mark if not present
    if not query.endswith('?'):
        enhanced_queries.append(query + "?")
    
    query_lower = query.lower().strip()
    
    # Generate semantic variations based on query type
    if 'main topic' in query_lower or 'about' in query_lower:
        enhanced_queries.extend([
            f"main subject discussed",
            f"primary focus of content",
            f"central theme"
        ])
    elif 'concept' in query_lower or 'explain' in query_lower:
        enhanced_queries.extend([
            f"key ideas explained",
            f"important principles",
            f"fundamental concepts"
        ])
    elif 'summary' in query_lower or 'summarize' in query_lower:
        enhanced_queries.extend([
            f"main points covered",
            f"key takeaways",
            f"important highlights"
        ])
    else:
        # Generic enhancements for any query
        enhanced_queries.extend([
            f"discuss {query_lower}",
            f"information about {query_lower}",
            f"details regarding {query_lower}"
        ])
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for q in enhanced_queries:
        if q.lower() not in seen:
            seen.add(q.lower())
            result.append(q)
    
    return result[:4]  # Limit to 4 variations for performance

# Simple OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

load_dotenv()

class InMemoryVectorStore:
    """Simple in-memory vector store as ChromaDB fallback"""
    
    def __init__(self):
        self.collections = {}
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def get_or_create_collection(self, name: str):
        if name not in self.collections:
            self.collections[name] = {
                'documents': [],
                'embeddings': [],
                'metadatas': [],
                'ids': []
            }
        return self.collections[name]
    
    def add_to_collection(self, collection_name: str, documents: List[str], 
                         embeddings: List[List[float]], metadatas: List[Dict], ids: List[str]):
        collection = self.get_or_create_collection(collection_name)
        collection['documents'].extend(documents)
        collection['embeddings'].extend(embeddings)
        collection['metadatas'].extend(metadatas)
        collection['ids'].extend(ids)
        collection['last_updated'] = datetime.now()
    
    def query_collection(self, collection_name: str, query_embedding: List[float], 
                        n_results: int = 5) -> Dict[str, Any]:
        if collection_name not in self.collections:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        
        collection = self.collections[collection_name]
        if not collection['embeddings']:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        
        # Fixed cosine similarity search
        import numpy as np
        query_vector = np.array(query_embedding)
        similarities = []
        
        for embedding in collection['embeddings']:
            doc_vector = np.array(embedding)
            
            # Calculate cosine similarity properly
            dot_product = np.dot(query_vector, doc_vector)
            query_norm = np.linalg.norm(query_vector)
            doc_norm = np.linalg.norm(doc_vector)
            
            if query_norm == 0 or doc_norm == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (query_norm * doc_norm)
            
            # Convert similarity ([-1, 1]) to distance ([0, 2]) where 0 is most similar
            distance = 1 - similarity
            similarities.append(distance)
        
        # Get top results (smallest distances)
        top_indices = np.argsort(similarities)[:n_results]
        
        return {
            'documents': [[collection['documents'][i] for i in top_indices]],
            'metadatas': [[collection['metadatas'][i] for i in top_indices]],
            'distances': [[similarities[i] for i in top_indices]]
        }
    
    def delete_collection(self, name: str):
        if name in self.collections:
            del self.collections[name]
    
    def list_collections(self) -> List[Dict[str, Any]]:
        detailed_collections = []
        for name, collection in self.collections.items():
            detailed_collections.append({
                "name": name.replace("transcript_", ""),
                "count": len(collection['documents']),
                "last_updated": collection.get('last_updated')
            })
        return detailed_collections

class RAGService:
    """Enhanced Service for Retrieval-Augmented Generation using transcript data"""
    
    def __init__(self):
        # Initialize with better embedding model for improved accuracy
        try:
            # Use a more accurate embedding model
            self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
            logger.info("Using all-mpnet-base-v2 embedding model for better accuracy")
        except Exception as e:
            logger.warning(f"Failed to load all-mpnet-base-v2, falling back to all-MiniLM-L6-v2: {e}")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize vector store (ChromaDB or fallback)
        if CHROMADB_AVAILABLE:
            try:
                self.chroma_client = chromadb.Client(Settings(
                    persist_directory="./chroma_db",
                    anonymized_telemetry=False
                ))
                self.use_chromadb = True
                logger.info("Using ChromaDB for vector storage")
            except Exception as e:
                logger.warning(f"ChromaDB initialization failed: {str(e)}. Using in-memory fallback.")
                self.vector_store = InMemoryVectorStore()
                self.use_chromadb = False
        else:
            self.vector_store = InMemoryVectorStore()
            self.use_chromadb = False
            logger.info("Using in-memory vector storage")
        
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key and OPENAI_AVAILABLE:
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not found or OpenAI not available. RAG responses will be limited to retrieval only.")
        
    def get_or_create_collection(self, video_id: str):
        """Get or create a collection for a specific video"""
        collection_name = f"transcript_{video_id}"
        
        if self.use_chromadb:
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except:
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"video_id": video_id, "created_at": datetime.now().isoformat()}
                )
            return collection
        else:
            return self.vector_store.get_or_create_collection(collection_name)
    
    def process_and_store_transcript(self, video_id: str, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process transcript segments and store them in vector database with enhanced chunking"""
        try:
            collection_name = f"transcript_{video_id}"
            
            # Update collection metadata with last updated time
            if self.use_chromadb:
                collection = self.get_or_create_collection(video_id)
                collection.modify(metadata={"last_updated": datetime.now().isoformat()})

            # Prepare chunks for embedding with enhanced strategy
            chunks = []
            metadatas = []
            ids = []
            
            for i, segment in enumerate(segments):
                text = segment.get('text', '')
                timestamp = segment.get('timestamp', 0)
                
                # Use enhanced text splitter with larger chunks for better context
                segment_chunks = enhanced_text_splitter(text, 800, 100)
                
                for j, chunk in enumerate(segment_chunks):
                    if len(chunk.strip()) < 20:  # Skip very small chunks
                        continue
                        
                    chunks.append(chunk.strip())
                    metadatas.append({
                        "video_id": video_id,
                        "segment_index": i,
                        "chunk_index": j,
                        "timestamp": timestamp,
                        "original_text": text,
                        "chunk_length": len(chunk)
                    })
                    ids.append(f"{video_id}_{i}_{j}")
            
            if not chunks:
                return {"success": False, "error": "No valid chunks to process"}
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks).tolist()
            
            # Store in vector database
            if self.use_chromadb:
                collection = self.get_or_create_collection(video_id)
                collection.add(
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                self.vector_store.add_to_collection(
                    collection_name, chunks, embeddings, metadatas, ids
                )
            
            return {
                "success": True,
                "chunks_stored": len(chunks),
                "collection_name": collection_name
            }
            
        except Exception as e:
            logger.error(f"Error processing transcript for {video_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def search_transcript(self, video_id: str, query: str, top_k: int = 100) -> Dict[str, Any]:
        """Enhanced search for relevant segments with query enhancement and relevance filtering"""
        try:
            collection_name = f"transcript_{video_id}"
            
            # Enhance query for better retrieval
            enhanced_queries = enhance_query(query)
            logger.info(f"Enhanced queries for '{query}': {enhanced_queries}")
            all_results = []
            
            for enhanced_query in enhanced_queries:  # Use all query variations
                # Generate query embedding
                query_embedding = self.embedding_model.encode([enhanced_query]).tolist()[0]
                
                # Search in vector database
                if self.use_chromadb:
                    collection = self.get_or_create_collection(video_id)
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=min(top_k * 2, 500),  # Get more results for filtering
                        include=["documents", "metadatas", "distances"]
                    )
                else:
                    results = self.vector_store.query_collection(
                        collection_name, query_embedding, min(top_k * 2, 500)
                    )
                
                # Add results with query variant info
                if results['documents'] and results['documents'][0]:
                    for doc, metadata, distance in zip(
                        results['documents'][0],
                        results['metadatas'][0],
                        results['distances'][0]
                    ):
                        # ChromaDB returns squared L2 distance, convert to similarity score
                        # For L2 distance: smaller distance = higher similarity
                        # Convert to 0-1 scale where 1 is most similar
                        if self.use_chromadb:
                            # For ChromaDB's L2 distance, convert to similarity
                            relevance_score = 1 / (1 + distance)  # Higher similarity for smaller distance
                        else:
                            # For our custom cosine distance implementation
                            relevance_score = 1 - distance
                        
                        all_results.append({
                            "text": doc,
                            "timestamp": metadata.get("timestamp", 0),
                            "segment_index": metadata.get("segment_index", 0),
                            "relevance_score": relevance_score,
                            "metadata": metadata,
                            "query_variant": enhanced_query
                        })
            
            # Remove duplicates and apply relevance filtering
            seen_chunks = set()
            filtered_results = []
            
            # Sort by relevance score
            all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            for result in all_results:
                chunk_id = f"{result['metadata'].get('segment_index')}_{result['metadata'].get('chunk_index')}"
                
                # Skip duplicates and low relevance results  
                # Debug: temporarily removed threshold to see all results
                if (chunk_id not in seen_chunks and 
                    len(filtered_results) < top_k):
                    
                    seen_chunks.add(chunk_id)
                    filtered_results.append(result)

            return {
                "success": True,
                "query": query,
                "results": filtered_results,
                "video_id": video_id,
                "total_variants_searched": len(enhanced_queries)
            }
            
        except Exception as e:
            logger.error(f"Error searching transcript for {video_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def generate_rag_response(self, video_id: str, query: str, top_k: int = 100) -> Dict[str, Any]:
        """Generate enhanced response using improved RAG with better prompts and context organization"""
        try:
            # First, search for relevant content
            search_results = self.search_transcript(video_id, query, top_k)
            
            if not search_results["success"]:
                return search_results
            
            if not self.openai_client:
                # Create a better formatted fallback response
                segments = search_results["results"][:5]  # Top 5 most relevant
                fallback_answer = "Based on the most relevant transcript segments:\n\n"
                
                for i, segment in enumerate(segments, 1):
                    timestamp = segment.get("timestamp", 0)
                    timestamp_str = f"[{int(timestamp // 60):02d}:{int(timestamp % 60):02d}]"
                    fallback_answer += f"- {timestamp_str} {segment['text']}\n"
                
                fallback_answer += "\nNote: AI analysis unavailable - showing raw transcript segments"
                
                return {
                    "success": True,
                    "query": query,
                    "video_id": video_id,
                    "answer": fallback_answer,
                    "sources": search_results["results"],
                    "retrieval_only": True
                }
            
            # Organize context more intelligently with adaptive thresholds
            all_results = search_results["results"]
            
            if not all_results:
                return {
                    "success": True,
                    "query": query,
                    "video_id": video_id,
                    "answer": "No Results Found\n\nThis video doesn't appear to contain information related to your question.\n\nTry:\n- Rephrasing your query with different keywords\n- Asking about the general topic or theme\n- Checking if this is the correct video",
                    "sources": [],
                    "retrieval_only": False,
                    "high_relevance_count": 0,
                    "total_sources": 0
                }
            
            # Calculate dynamic thresholds based on actual scores
            scores = [r["relevance_score"] for r in all_results]
            max_score = max(scores) if scores else 0
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Adaptive thresholds
            high_threshold = max(0.3, avg_score + 0.1)  # At least 0.3 or above average
            medium_threshold = max(0.1, avg_score - 0.1)  # At least 0.1 or below average
            
            high_relevance = [r for r in all_results if r["relevance_score"] >= high_threshold]
            medium_relevance = [r for r in all_results if medium_threshold <= r["relevance_score"] < high_threshold]
            
            # Build context with priority structure
            context_parts = []
            
            if high_relevance:
                context_parts.append("=== MOST RELEVANT SEGMENTS ===")
                for result in high_relevance[:10]:  # Top 10 most relevant
                    timestamp = result.get("timestamp", 0)
                    timestamp_str = f"[{int(timestamp // 60):02d}:{int(timestamp % 60):02d}]"
                    context_parts.append(f"{timestamp_str} {result['text']}")
            
            if medium_relevance and len(context_parts) < 15:  # Add more context if needed
                context_parts.append("\n=== ADDITIONAL CONTEXT ===")
                for result in medium_relevance[:5]:
                    timestamp = result.get("timestamp", 0)
                    timestamp_str = f"[{int(timestamp // 60):02d}:{int(timestamp % 60):02d}]"
                    context_parts.append(f"{timestamp_str} {result['text']}")
            
            # Fallback: if no context, use top results regardless of score
            if not context_parts and all_results:
                context_parts.append("=== AVAILABLE TRANSCRIPT SEGMENTS ===")
                for result in all_results[:5]:  # Use top 5 results
                    timestamp = result.get("timestamp", 0)
                    timestamp_str = f"[{int(timestamp // 60):02d}:{int(timestamp % 60):02d}]"
                    context_parts.append(f"{timestamp_str} {result['text']}")
            
            context = "\n\n".join(context_parts)
            
            # Enhanced system prompt for video transcripts
            system_prompt = """You are a helpful assistant that analyzes podcast transcripts. Provide clear, concise, and actionable answers.

FORMATTING RULES:
- Start with the direct answer (1-2 sentences)
- Use line breaks and clear spacing for readability
- Use simple text formatting with proper spacing
- Be confident and definitive based on evidence
- Skip unnecessary hedging ("it's difficult to determine")
- Use timestamps strategically when they add value

STRUCTURE:
1. Direct answer first
2. Blank line
3. "Key Points:" (followed by list items with dashes)
4. Blank line  
5. "Evidence:" (if timestamps add value)

KEEP IT CONCISE: 150-300 words maximum. Use clear line breaks and spacing for readability."""
            
            user_prompt = f"""Question: {query}

Transcript Segments:
{context}

Provide a clear, concise answer following this format:

Direct answer (1-2 sentences)

Key Points:
- First key point
- Second key point
- Third key point

Evidence:
- [timestamp] relevant detail (only if timestamps add value)

Use simple text with line breaks. No markdown formatting."""

            # Use GPT-4 for better accuracy if available, otherwise GPT-3.5-turbo
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",  # More capable model
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,  # Lower temperature for more consistent answers
                    max_tokens=1500
                )
            except Exception as e:
                # Fallback to GPT-3.5-turbo if GPT-4 is not available
                logger.warning(f"GPT-4 not available, falling back to GPT-3.5-turbo: {e}")
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500
                )
            
            return {
                "success": True,
                "query": query,
                "video_id": video_id,
                "answer": response.choices[0].message.content,
                "sources": search_results["results"],
                "retrieval_only": False,
                "high_relevance_count": len(high_relevance),
                "total_sources": len(search_results["results"])
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response for {video_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def list_video_collections(self) -> List[Dict[str, Any]]:
        """List all video collections with details"""
        if self.use_chromadb:
            try:
                collections = self.chroma_client.list_collections()
                detailed_collections = []
                for collection in collections:
                    if collection.name.startswith("transcript_"):
                        metadata = collection.metadata or {}
                        last_updated_str = metadata.get("last_updated") or metadata.get("created_at")
                        last_updated = None
                        if last_updated_str:
                            try:
                                last_updated = datetime.fromisoformat(last_updated_str)
                            except (ValueError, TypeError):
                                last_updated = None

                        detailed_collections.append({
                            "name": collection.name.replace("transcript_", ""),
                            "count": collection.count(),
                            "last_updated": last_updated
                        })
                return detailed_collections
            except Exception as e:
                logger.error(f"Failed to list ChromaDB collections: {e}")
                return []
        else:
            # This is for the in-memory fallback
            return self.vector_store.list_collections()
    
    def delete_video_collection(self, video_id: str) -> bool:
        """Delete a video's collection from the database"""
        try:
            collection_name = f"transcript_{video_id}"
            if self.use_chromadb:
                self.chroma_client.delete_collection(collection_name)
            else:
                self.vector_store.delete_collection(collection_name)
            return True
        except Exception as e:
            logger.error(f"Error deleting collection for {video_id}: {str(e)}")
            return False
