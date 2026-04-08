from pydantic import BaseModel, Field
from typing import List, Optional

class VerifyRequest(BaseModel):
    video_id: Optional[str] = None
    claim_text: str = Field(..., min_length=8)
    start_ts: Optional[float] = None
    end_ts: Optional[float] = None
    max_sources: int = 3

class VerificationSource(BaseModel):
    url: str
    domain: str
    title: Optional[str] = None
    published_at: Optional[str] = None
    snippet: str
    screenshot_b64: Optional[str] = None
    url_with_text_fragment: Optional[str] = None
    similarity: float
    entailment_score: Optional[float] = None

class ClaimVerification(BaseModel):
    text: str
    verdict: str
    confidence: float
    sources: List[VerificationSource]

class VerifyResponse(BaseModel):
    success: bool
    claim: str
    result: Optional[ClaimVerification] = None
    error: Optional[str] = None
