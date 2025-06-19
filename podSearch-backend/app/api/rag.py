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
        # Get transcript data from database
        segments = await transcript_service.get_transcript_from_db(video_id)
        
        if not segments:
            raise HTTPException(status_code=404, detail="Transcript not found in database")
        
        # Convert segments to the format expected by RAG service
        formatted_segments = []
        for segment in segments:
            formatted_segments.append({
                "text": segment.get("text", ""),
                "timestamp": segment.get("timestamp", 0)
            })
        
        # Check if collection already exists and handle overwrite
        existing_videos = rag_service.list_video_collections()
        if video_id in existing_videos:
            if request and not request.overwrite:
                return RAGProcessResponse(
                    success=False,
                    video_id=video_id,
                    error="Video already processed. Use overwrite=true to reprocess."
                )
            else:
                # Delete existing collection
                rag_service.delete_video_collection(video_id)
        
        # Process and store transcript
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
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/{video_id}", response_model=RAGSearchResponse)
async def search_transcript(video_id: str, request: RAGSearchRequest):
    """Search for relevant segments in a video's transcript"""
    try:
        # Check if video has been processed
        existing_videos = rag_service.list_video_collections()
        if video_id not in existing_videos:
            raise HTTPException(
                status_code=404, 
                detail=f"Video {video_id} not processed for RAG. Use /process/{video_id} first."
            )
        
        # Perform search
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
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/{video_id}", response_model=RAGGenerateResponse) 
async def generate_rag_response(video_id: str, request: RAGGenerateRequest):
    """Generate an AI response based on transcript content"""
    try:
        # Check if video has been processed
        existing_videos = rag_service.list_video_collections()
        if video_id not in existing_videos:
            raise HTTPException(
                status_code=404,
                detail=f"Video {video_id} not processed for RAG. Use /process/{video_id} first."
            )
        
        # Generate response
        result = rag_service.generate_rag_response(video_id, request.query, request.top_k)
        
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
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=RAGListResponse)
async def list_processed_videos():
    """List all videos that have been processed for RAG"""
    try:
        video_ids = rag_service.list_video_collections()
        return RAGListResponse(
            video_ids=video_ids,
            count=len(video_ids)
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
    """Health check for RAG service"""
    try:
        video_count = len(rag_service.list_video_collections())
        return {
            "status": "healthy",
            "service": "RAG",
            "processed_videos": video_count,
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_store": "ChromaDB"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        } 