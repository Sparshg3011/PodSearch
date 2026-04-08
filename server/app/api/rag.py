from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models.rag import (
    RAGSearchRequest, RAGSearchResponse, 
    RAGGenerateRequest, RAGGenerateResponse,
    RAGProcessRequest, RAGProcessResponse,
    RAGListResponse
)
from ..core.rag_service import RAGService
from ..core.transcript_service import TranscriptService

router = APIRouter()
rag_service = RAGService()
transcript_service = TranscriptService()

@router.post("/process/{video_id}", response_model=RAGProcessResponse)
async def process_transcript_for_rag(video_id: str, request: RAGProcessRequest = None):
    """Process a video's transcript data for RAG functionality"""
    try:

        segments = await transcript_service.get_transcript_from_db(video_id)
        

        if not segments:
            print(f"Transcript not found in database for {video_id}, fetching directly...")
            transcript_result = transcript_service.extract_transcript(video_id)
            
            if not transcript_result["success"]:
                return RAGProcessResponse(
                    success=False,
                    video_id=video_id,
                    error=f"Could not fetch transcript: {transcript_result['error']}"
                )
            

            formatted_segments = []
            for segment in transcript_result["segments"]:
                formatted_segments.append({
                    "text": segment.text,
                    "timestamp": segment.timestamp
                })
        else:

            formatted_segments = []
            for segment in segments:
                formatted_segments.append({
                    "text": segment.get("text", ""),
                    "timestamp": segment.get("timestamp", 0)
                })
        

        existing_collections = rag_service.list_video_collections()
        if video_id in [c['name'] for c in existing_collections]:
            if request and not request.overwrite:
                return RAGProcessResponse(
                    success=False,
                    video_id=video_id,
                    error="Video already processed. Use overwrite=true to reprocess."
                )
            else:

                rag_service.delete_video_collection(video_id)
        

        result = rag_service.process_and_store_transcript(video_id, formatted_segments)
        
        if result["success"]:
            return RAGProcessResponse(
                success=True,
                video_id=video_id,
                chunks_stored=result["chunks_stored"],
                collection_name=result["collection_name"]
            )
        else:
            return RAGProcessResponse(
                success=False,
                video_id=video_id,
                error=result["error"]
            )
            
    except Exception as e:
        return RAGProcessResponse(
            success=False,
            video_id=video_id,
            error=f"Processing failed: {str(e)}"
        )

@router.post("/search/{video_id}", response_model=RAGSearchResponse)
async def search_transcript(video_id: str, request: RAGSearchRequest):
    """Search for relevant segments in a video's transcript"""
    try:

        existing_collections = rag_service.list_video_collections()
        if video_id not in [c['name'] for c in existing_collections]:
            return RAGSearchResponse(
                success=False,
                query=request.query,
                video_id=video_id,
                error=f"Video {video_id} not processed for RAG. Use /process/{video_id} first."
            )
        

        result = rag_service.search_transcript(video_id, request.query, request.top_k)
        
        if result["success"]:
            return RAGSearchResponse(
                success=True,
                query=request.query,
                video_id=video_id,
                results=[
                    {
                        "text": r["text"],
                        "timestamp": r["timestamp"],
                        "segment_index": r["segment_index"],
                        "relevance_score": r["relevance_score"],
                        "metadata": r["metadata"]
                    }
                    for r in result["results"]
                ]
            )
        else:
            return RAGSearchResponse(
                success=False,
                query=request.query,
                video_id=video_id,
                error=result["error"]
            )
            
    except Exception as e:
        return RAGSearchResponse(
            success=False,
            query=request.query,
            video_id=video_id,
            error=f"Search failed: {str(e)}"
        )

@router.post("/generate/{video_id}", response_model=RAGGenerateResponse) 
async def generate_rag_response(video_id: str, request: RAGGenerateRequest):
    """Generate an AI response based on transcript content"""
    try:

        existing_collections = rag_service.list_video_collections()
        if video_id not in [c['name'] for c in existing_collections]:
            return RAGGenerateResponse(
                success=False,
                query=request.query,
                video_id=video_id,
                answer="",
                error=f"Video {video_id} not processed for RAG. Use /process/{video_id} first."
            )
        

        result = rag_service.generate_rag_response(video_id, request.query, request.top_k, request.max_context_chunks)
        
        if result["success"]:
            return RAGGenerateResponse(
                success=True,
                query=request.query,
                video_id=video_id,
                answer=result["answer"],
                sources=[
                    {
                        "text": r["text"],
                        "timestamp": r["timestamp"],
                        "segment_index": r["segment_index"],
                        "relevance_score": r["relevance_score"],
                        "metadata": r["metadata"]
                    }
                    for r in result["sources"]
                ],
                retrieval_only=result.get("retrieval_only", False)
            )
        else:
            return RAGGenerateResponse(
                success=False,
                query=request.query,
                video_id=video_id,
                answer="",
                error=result["error"]
            )
            
    except Exception as e:
        return RAGGenerateResponse(
            success=False,
            query=request.query,
            video_id=video_id,
            answer="",
            error=f"Generation failed: {str(e)}"
        )

@router.get("/list", response_model=RAGListResponse)
async def list_processed_videos():
    """List all videos that have been processed for RAG"""
    try:
        collections = rag_service.list_video_collections()
        return RAGListResponse(
            collections=collections,
            count=len(collections)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{video_id}")
async def delete_video_rag_data(video_id: str):
    """Delete RAG data for a specific video"""
    try:
        success = rag_service.delete_video_collection(video_id)
        
        if success:
            return {"message": f"RAG data for video {video_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"No RAG data found for video {video_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def rag_health_check():
    try:
        video_count = len(rag_service.list_video_collections())
        embedding_model_name = getattr(rag_service.embedding_model, 'model_name', 'unknown')
        openai_available = rag_service.openai_client is not None
        vector_store_type = "ChromaDB" if rag_service.use_chromadb else "In-Memory"
        
        return {
            "status": "healthy",
            "processed_videos": video_count,
            "embedding_model": embedding_model_name,
            "vector_store": vector_store_type,
            "openai_available": openai_available
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        } 