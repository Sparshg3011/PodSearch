from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..models.youtube import TranscriptWithTimestampsResponse
from ..core.transcript_service import TranscriptService

router = APIRouter()
transcript_service = TranscriptService()

@router.get("/transcript-supadata/{video_id}", response_model=TranscriptWithTimestampsResponse)
async def get_transcript_supadata(
    video_id: str,
    language: str = Query("en"),
    save_to_file: bool = Query(True),
    save_to_db: bool = Query(True)
):
    try:
        result = transcript_service.extract_transcript(video_id, language)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        response_data = TranscriptWithTimestampsResponse(
            video_id=video_id,
            segments=result["segments"],
            metadata=result["metadata"]
        )
        
        # Save to file if requested
        if save_to_file and result["segments"]:
            file_path = transcript_service.save_transcript_to_file(response_data, video_id)
            if file_path:
                response_data.metadata["file_path"] = file_path
                response_data.metadata["file_saved"] = True
            else:
                response_data.metadata["file_saved"] = False
                response_data.metadata["file_error"] = "Failed to save file"
        
        # Save to database with timestamps if requested
        if save_to_db and result["segments"]:
            try:
                # Save video ID and transcript segments to database
                db_result = await transcript_service.save_transcript_to_db(
                    video_id=video_id,
                    segments=result["segments"]
                )
                
                response_data.metadata["db_saved"] = db_result["success"]
                if db_result["success"]:
                    response_data.metadata["segments_saved"] = db_result["segments_saved"]
                else:
                    response_data.metadata["db_error"] = db_result["error"]
                    
            except Exception as e:
                response_data.metadata["db_saved"] = False
                response_data.metadata["db_error"] = f"Database save failed: {str(e)}"
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/db/{video_id}")
async def get_transcript_from_db(video_id: str):
    """Get transcript segments from database by video ID."""
    try:
        segments = await transcript_service.get_transcript_from_db(video_id)
        if not segments:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        return {
            "video_id": video_id,
            "segments_count": len(segments),
            "segments": segments
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_transcripts(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results")
):
    """Search transcript segments by text content."""
    try:
        results = await transcript_service.search_transcripts_in_db(query, limit)
        return {
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))