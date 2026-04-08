from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime

class TranscriptSegmentDB(Document):
    video_id: str = Field(..., description="YouTube video ID")
    sequence: int = Field(..., description="Order of segment in the transcript")
    text: str = Field(..., description="Transcript text for this segment")
    timestamp: Optional[float] = Field(None, description="Timestamp in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "transcript_segments"
        indexes = [
            "video_id",
            [("video_id", 1), ("sequence", 1)],
            "timestamp"
        ] 