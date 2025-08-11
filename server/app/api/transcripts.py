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

            return TranscriptWithTimestampsResponse(
                success=False,
                video_id=video_id,
                segments=[],
                metadata={"error": result["error"]}
            )
        
        response_data = TranscriptWithTimestampsResponse(
            success=True,
            video_id=video_id,
            segments=result["segments"],
            metadata=result["metadata"]
        )
        

        
        if save_to_db and result["segments"]:
            try:
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
        
    except Exception as e:
        return TranscriptWithTimestampsResponse(
            success=False,
            video_id=video_id,
            segments=[],
            metadata={"error": f"Unexpected error: {str(e)}"}
        )

@router.get("/search/{video_id}")
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

