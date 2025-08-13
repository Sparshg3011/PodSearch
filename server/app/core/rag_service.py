import os
import logging
import re
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

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

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

load_dotenv()

def simple_text_splitter(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    if len(text) <= chunk_size:
        return [text]
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) <= 1:
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                overlap_words = min(overlap // 10, len(current_chunk) // 3)
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_length = sum(len(w) + 1 for w in current_chunk)
            
            current_chunk.append(word)
            current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        return [c for c in chunks if c.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else []
            current_chunk = overlap_sentences
            current_length = sum(len(s) + 1 for s in current_chunk)
        
        current_chunk.append(sentence)
        current_length += sentence_length + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return [c.strip() for c in chunks if c.strip()]

def enhance_query(query: str) -> List[str]:
    queries = [query]
    
    if not query.endswith('?'):
        queries.append(query + "?")
    
    query_lower = query.lower().strip()
    
    if 'main topic' in query_lower or 'about' in query_lower:
        queries.extend(["main subject discussed", "primary focus", "central theme"])
    elif 'concept' in query_lower or 'explain' in query_lower:
        queries.extend(["key ideas", "important principles", "concepts"])
    elif 'summary' in query_lower or 'summarize' in query_lower:
        queries.extend(["main points", "key takeaways", "highlights"])
    else:
        queries.extend([f"discuss {query_lower}", f"about {query_lower}"])
    
    return list(dict.fromkeys(queries))[:4]

class InMemoryVectorStore:
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
        
        query_vector = np.array(query_embedding)
        similarities = []
        
        for embedding in collection['embeddings']:
            doc_vector = np.array(embedding)
            dot_product = np.dot(query_vector, doc_vector)
            query_norm = np.linalg.norm(query_vector)
            doc_norm = np.linalg.norm(doc_vector)
            
            if query_norm == 0 or doc_norm == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (query_norm * doc_norm)
            
            distance = 1 - similarity
            similarities.append(distance)
        
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
        return [{
            "name": name.replace("transcript_", ""),
            "count": len(collection['documents']),
            "last_updated": collection.get('last_updated')
        } for name, collection in self.collections.items()]

class RAGService:
    def __init__(self):
        try:
            self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        except Exception:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        if CHROMADB_AVAILABLE:
            try:
                self.chroma_client = chromadb.Client(Settings(
                    persist_directory="./chroma_db",
                    anonymized_telemetry=False
                ))
                self.use_chromadb = True
            except Exception:
                self.vector_store = InMemoryVectorStore()
                self.use_chromadb = False
        else:
            self.vector_store = InMemoryVectorStore()
            self.use_chromadb = False
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key and OPENAI_AVAILABLE:
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None
        
    def get_or_create_collection(self, video_id: str):
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
        try:
            collection_name = f"transcript_{video_id}"
            
            if self.use_chromadb:
                collection = self.get_or_create_collection(video_id)
                collection.modify(metadata={"last_updated": datetime.now().isoformat()})

            chunks = []
            metadatas = []
            ids = []
            
            for i, segment in enumerate(segments):
                text = segment.get('text', '')
                timestamp = segment.get('timestamp', 0)
                
                segment_chunks = simple_text_splitter(text, 800, 100)
                
                for j, chunk in enumerate(segment_chunks):
                    if len(chunk.strip()) < 20:
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
            
            embeddings = self.embedding_model.encode(chunks).tolist()
            
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
        try:
            collection_name = f"transcript_{video_id}"
            enhanced_queries = enhance_query(query)
            all_results = []
            
            for enhanced_query in enhanced_queries:
                query_embedding = self.embedding_model.encode([enhanced_query]).tolist()[0]
                
                if self.use_chromadb:
                    collection = self.get_or_create_collection(video_id)
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=min(top_k * 2, 500),
                        include=["documents", "metadatas", "distances"]
                    )
                else:
                    results = self.vector_store.query_collection(
                        collection_name, query_embedding, min(top_k * 2, 500)
                    )
                
                if results['documents'] and results['documents'][0]:
                    for doc, metadata, distance in zip(
                        results['documents'][0],
                        results['metadatas'][0],
                        results['distances'][0]
                    ):
                        relevance_score = 1 / (1 + distance) if self.use_chromadb else 1 - distance
                        
                        all_results.append({
                            "text": doc,
                            "timestamp": metadata.get("timestamp", 0),
                            "segment_index": metadata.get("segment_index", 0),
                            "relevance_score": relevance_score,
                            "metadata": metadata,
                            "query_variant": enhanced_query
                        })
            
            seen_chunks = set()
            filtered_results = []
            all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            for result in all_results:
                chunk_id = f"{result['metadata'].get('segment_index')}_{result['metadata'].get('chunk_index')}"
                if chunk_id not in seen_chunks and len(filtered_results) < top_k:
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
        try:
            search_results = self.search_transcript(video_id, query, top_k)
            
            if not search_results["success"]:
                return search_results
            
            if not self.openai_client:
                segments = search_results["results"][:5]
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
            
            all_results = search_results["results"]
            
            if not all_results:
                return {
                    "success": True,
                    "query": query,
                    "video_id": video_id,
                    "answer": "No relevant information found in this video for your query. Try rephrasing your question or asking about the general topic.",
                    "sources": [],
                    "retrieval_only": False
                }
            
            scores = [r["relevance_score"] for r in all_results]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            high_threshold = max(0.3, avg_score + 0.1)
            high_relevance = [r for r in all_results if r["relevance_score"] >= high_threshold]
            medium_relevance = [r for r in all_results if 0.2 <= r["relevance_score"] < high_threshold]
            
            context_parts = []
            
            if high_relevance:
                context_parts.append("=== MOST RELEVANT SEGMENTS ===")
                for result in high_relevance[:10]:
                    timestamp = result.get("timestamp", 0)
                    timestamp_str = f"[{int(timestamp // 60):02d}:{int(timestamp % 60):02d}]"
                    context_parts.append(f"{timestamp_str} {result['text']}")
            
            if medium_relevance and len(context_parts) < 15:
                context_parts.append("\n=== ADDITIONAL CONTEXT ===")
                for result in medium_relevance[:5]:
                    timestamp = result.get("timestamp", 0)
                    timestamp_str = f"[{int(timestamp // 60):02d}:{int(timestamp % 60):02d}]"
                    context_parts.append(f"{timestamp_str} {result['text']}")
            
            if not context_parts:
                context_parts.append("=== AVAILABLE TRANSCRIPT SEGMENTS ===")
                for result in all_results[:5]:
                    timestamp = result.get("timestamp", 0)
                    timestamp_str = f"[{int(timestamp // 60):02d}:{int(timestamp % 60):02d}]"
                    context_parts.append(f"{timestamp_str} {result['text']}")
            
            context = "\n\n".join(context_parts)
            
            system_prompt = """You are a helpful assistant that analyzes podcast transcripts. Provide clear, concise answers.

FORMATTING RULES:
- Start with the direct answer (1-2 sentences)
- Use line breaks and clear spacing for readability
- Be confident and definitive based on evidence
- Use timestamps strategically when they add value

STRUCTURE:
1. Direct answer first
2. Blank line
3. "Key Points:" (followed by list items with dashes)
4. Blank line  
5. "Evidence:" (if timestamps add value)

KEEP IT CONCISE: 150-300 words maximum."""
            
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

            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500
                )
            except Exception:
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.1,
                        max_tokens=1500
                    )
                except Exception:
                    segments = all_results[:5]
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
                        "sources": all_results,
                        "retrieval_only": True
                    }
            
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
        if self.use_chromadb:
            try:
                collections = self.chroma_client.list_collections()
                return [{
                    "name": collection.name.replace("transcript_", ""),
                    "count": collection.count(),
                    "last_updated": collection.metadata.get("last_updated") or collection.metadata.get("created_at")
                } for collection in collections if collection.name.startswith("transcript_")]
            except Exception as e:
                logger.error(f"Failed to list ChromaDB collections: {e}")
                return []
        else:
            return self.vector_store.list_collections()
    
    def delete_video_collection(self, video_id: str) -> bool:
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