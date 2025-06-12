from fastapi import APIRouter, HTTPException, Query
from ..models.youtube import YouTubeSearchResponse
from ..core.youtube_service import YouTubeService
from ..core.transcript_service import TranscriptService

router = APIRouter()
transcript_service = TranscriptService()

@router.get("/search", response_model=YouTubeSearchResponse)
async def search_youtube(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(5, ge=1, le=20)
):
    try:
        search_query = f"{q} popular podcast" 
        videos = YouTubeService.search_videos(search_query, max_results)
        return YouTubeSearchResponse(results=videos, query=search_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/video/{video_id}")
async def get_video_info(video_id: str):
    """Get detailed info about a specific video"""
    try:
        video = YouTubeService.get_video_info(video_id)
        return video
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")
