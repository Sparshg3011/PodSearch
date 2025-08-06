from pydantic import BaseModel
from typing import Optional, List

class YouTubeVideo(BaseModel):
    id: str
    title: str
    duration: Optional[int] = None
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    uploader: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    available_languages: List[str] = []
    has_captions: bool = False
    url: str

class YouTubeSearchResponse(BaseModel):
    results: List[YouTubeVideo]
    query: str

class TranscriptSegment(BaseModel):
    text: str
    timestamp: Optional[float] = None

class TranscriptWithTimestampsResponse(BaseModel):
    success: bool = True
    video_id: str
    segments: List[TranscriptSegment]
    metadata: dict

class TranscriptResponse(BaseModel):
    video_id: str
    title: str
    transcript: Optional[str] = None
    available_languages: List[str] = []
    has_manual_captions: bool = False
    has_auto_captions: bool = False 