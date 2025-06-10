from fastapi import APIRouter, HTTPException, Query
from ..models.youtube import TranscriptWithTimestampsResponse
from ..core.transcript_service import TranscriptService

router = APIRouter()
transcript_service = TranscriptService()

@router.get("/transcript-supadata/{video_id}", response_model=TranscriptWithTimestampsResponse)
async def get_transcript_supadata(
    video_id: str,
    language: str = Query("en"),
    save_to_file: bool = Query(True)
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
        
        if save_to_file and result["segments"]:
            file_path = transcript_service.save_transcript_to_file(response_data, video_id)
            if file_path:
                response_data.metadata["file_path"] = file_path
                response_data.metadata["file_saved"] = True
            else:
                response_data.metadata["file_saved"] = False
                response_data.metadata["file_error"] = "Failed to save file"
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))