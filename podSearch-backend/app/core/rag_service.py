import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import re

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

# Simple text splitter implementation
def simple_text_splitter(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Simple text splitter that divides text into chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to break at a sentence or word boundary
        chunk = text[start:end]
        if '.' in chunk[-100:]:
            last_period = chunk.rfind('.')
            chunk = chunk[:last_period + 1]
            end = start + len(chunk)
        elif ' ' in chunk[-50:]:
            last_space = chunk.rfind(' ')
            chunk = chunk[:last_space]
            end = start + len(chunk)
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return [c for c in chunks if c.strip()]

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
    
    def query_collection(self, collection_name: str, query_embedding: List[float], 
                        n_results: int = 5) -> Dict[str, Any]:
        if collection_name not in self.collections:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        
        collection = self.collections[collection_name]
        if not collection['embeddings']:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        
        # Simple cosine similarity search
        import numpy as np
        query_vector = np.array(query_embedding)
        similarities = []
        
        for embedding in collection['embeddings']:
            similarity = np.dot(query_vector, np.array(embedding)) / (
                np.linalg.norm(query_vector) * np.linalg.norm(embedding)
            )
            similarities.append(1 - similarity)  # Convert to distance
        
        # Get top results
        top_indices = np.argsort(similarities)[:n_results]
        
        return {
            'documents': [[collection['documents'][i] for i in top_indices]],
            'metadatas': [[collection['metadatas'][i] for i in top_indices]],
            'distances': [[similarities[i] for i in top_indices]]
        }
    
    def delete_collection(self, name: str):
        if name in self.collections:
            del self.collections[name]
    
    def list_collections(self) -> List[str]:
        return list(self.collections.keys())

class RAGService:
    """Service for Retrieval-Augmented Generation using transcript data"""
    
    def __init__(self):
        # Initialize embedding model
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
        """Process transcript segments and store them in vector database"""
        try:
            collection_name = f"transcript_{video_id}"
            
            # Prepare chunks for embedding
            chunks = []
            metadatas = []
            ids = []
            
            for i, segment in enumerate(segments):
                text = segment.get('text', '')
                timestamp = segment.get('timestamp', 0)
                
                # Split longer segments into smaller chunks
                segment_chunks = simple_text_splitter(text, 500, 50)
                
                for j, chunk in enumerate(segment_chunks):
                    if len(chunk.strip()) < 10:  # Skip very small chunks
                        continue
                        
                    chunks.append(chunk.strip())
                    metadatas.append({
                        "video_id": video_id,
                        "segment_index": i,
                        "chunk_index": j,
                        "timestamp": timestamp,
                        "original_text": text
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
    
    def search_transcript(self, video_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search for relevant segments in a video's transcript"""
        try:
            collection_name = f"transcript_{video_id}"
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Search in vector database
            if self.use_chromadb:
                collection = self.get_or_create_collection(video_id)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )
            else:
                results = self.vector_store.query_collection(
                    collection_name, query_embedding, top_k
                )
            
            # Format results
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    search_results.append({
                        "text": doc,
                        "timestamp": metadata.get("timestamp", 0),
                        "segment_index": metadata.get("segment_index", 0),
                        "relevance_score": 1 - distance,  # Convert distance to similarity
                        "metadata": metadata
                    })
            
            return {
                "success": True,
                "query": query,
                "results": search_results,
                "video_id": video_id
            }
            
        except Exception as e:
            logger.error(f"Error searching transcript for {video_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def generate_rag_response(self, video_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Generate a response using RAG: retrieve relevant segments and generate answer"""
        try:
            # First, search for relevant content
            search_results = self.search_transcript(video_id, query, top_k)
            
            if not search_results["success"]:
                return search_results
            
            if not self.openai_client:
                return {
                    "success": True,
                    "query": query,
                    "video_id": video_id,
                    "answer": "LLM not available. Here are the relevant transcript segments:",
                    "sources": search_results["results"],
                    "retrieval_only": True
                }
            
            # Prepare context from retrieved segments
            context_parts = []
            for result in search_results["results"]:
                timestamp = result.get("timestamp", 0)
                timestamp_str = f"[{int(timestamp // 60):02d}:{int(timestamp % 60):02d}]" if timestamp else "[00:00]"
                context_parts.append(f"{timestamp_str} {result['text']}")
            
            context = "\n\n".join(context_parts)
            
            # Generate response using OpenAI
            system_prompt = """You are a helpful assistant that answers questions about video transcripts. 
            Use the provided transcript segments to answer the user's question. Be accurate and cite specific parts of the transcript when relevant.
            If the transcript doesn't contain enough information to answer the question, say so clearly.
            Always be helpful and provide timestamps when referring to specific parts of the video."""
            
            user_prompt = f"""Question: {query}

Relevant transcript segments:
{context}

Please answer the question based on the provided transcript segments."""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            return {
                "success": True,
                "query": query,
                "video_id": video_id,
                "answer": response.choices[0].message.content,
                "sources": search_results["results"],
                "retrieval_only": False
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response for {video_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def list_video_collections(self) -> List[str]:
        """List all video collections in the database"""
        try:
            if self.use_chromadb:
                collections = self.chroma_client.list_collections()
                video_ids = []
                # Handle both old and new ChromaDB versions
                if isinstance(collections, list):
                    for collection in collections:
                        # New version returns collection names as strings
                        if isinstance(collection, str):
                            if collection.startswith("transcript_"):
                                video_id = collection.replace("transcript_", "")
                                video_ids.append(video_id)
                        # Old version returns collection objects
                        else:
                            collection_name = getattr(collection, 'name', str(collection))
                            if collection_name.startswith("transcript_"):
                                video_id = collection_name.replace("transcript_", "")
                                video_ids.append(video_id)
                return video_ids
            else:
                collections = self.vector_store.list_collections()
                return [c.replace("transcript_", "") for c in collections if c.startswith("transcript_")]
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
    
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
