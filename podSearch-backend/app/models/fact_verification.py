from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class VerificationStatus(str, Enum):
    VERIFIED = "✅ Verified"
    PARTIALLY_VERIFIED = "⚠️ Partially Verified"
    FALSE = "❌ False"
    UNCLEAR = "🔍 Unclear/Insufficient Evidence"

class SourceType(str, Enum):
    WIKIPEDIA = "Wikipedia"
    PUBMED = "PubMed"
    SEMANTIC_SCHOLAR = "Semantic Scholar"
    NEWS = "News"
    SEARCH_ENGINE = "Search Engine"
    ACADEMIC = "Academic"

class VerificationSource(BaseModel):
    title: str = Field(..., description="Title of the source")
    url: str = Field(..., description="URL of the source")
    source_type: SourceType = Field(..., description="Type of source")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    excerpt: str = Field(..., description="Relevant excerpt from the source")
    publication_date: Optional[str] = Field(None, description="Publication date if available")
    author: Optional[str] = Field(None, description="Author if available")

class ClaimVerification(BaseModel):
    claim: str = Field(..., description="The original claim being verified")
    status: VerificationStatus = Field(..., description="Verification status")
    confidence: float = Field(..., description="Confidence level (0-1)")
    explanation: str = Field(..., description="Explanation of how the fact was verified")
    sources: List[VerificationSource] = Field(default_factory=list, description="Supporting sources")
    verification_date: datetime = Field(default_factory=datetime.now, description="When verification was performed")
    agent_reasoning: str = Field(..., description="Agent's reasoning process")

class FactVerificationRequest(BaseModel):
    claims: List[str] = Field(..., description="List of claims to verify", min_items=1)
    video_id: Optional[str] = Field(None, description="Video ID if claims are from a specific video")
    context: Optional[str] = Field(None, description="Additional context for verification")
    search_depth: int = Field(3, description="Number of sources to search per tool", ge=1, le=10)
    include_academic: bool = Field(True, description="Whether to include academic sources")
    include_news: bool = Field(True, description="Whether to include news sources")

class FactVerificationResponse(BaseModel):
    success: bool = Field(..., description="Whether verification was successful")
    verifications: List[ClaimVerification] = Field(default_factory=list, description="Verification results")
    total_claims: int = Field(..., description="Total number of claims processed")
    processing_time: float = Field(..., description="Processing time in seconds")
    error: Optional[str] = Field(None, description="Error message if verification failed")

class BatchVerificationRequest(BaseModel):
    transcript_id: str = Field(..., description="Transcript ID to extract and verify claims from")
    auto_extract_claims: bool = Field(True, description="Whether to automatically extract claims")
    custom_claims: List[str] = Field(default_factory=list, description="Additional custom claims to verify")
    max_claims: int = Field(10, description="Maximum number of claims to extract", ge=1, le=50)
    search_depth: int = Field(3, description="Number of sources to search per tool", ge=1, le=10)

class BatchVerificationResponse(BaseModel):
    success: bool = Field(..., description="Whether batch verification was successful")
    transcript_id: str = Field(..., description="Transcript ID that was processed")
    extracted_claims: List[str] = Field(default_factory=list, description="Claims extracted from transcript")
    verifications: List[ClaimVerification] = Field(default_factory=list, description="Verification results")
    summary: Dict[str, int] = Field(default_factory=dict, description="Summary of verification results")
    processing_time: float = Field(..., description="Total processing time in seconds")
    error: Optional[str] = Field(None, description="Error message if verification failed")

class VerificationStatsResponse(BaseModel):
    total_verifications: int = Field(..., description="Total number of verifications performed")
    verification_breakdown: Dict[VerificationStatus, int] = Field(default_factory=dict, description="Breakdown by status")
    source_breakdown: Dict[SourceType, int] = Field(default_factory=dict, description="Breakdown by source type")
    average_confidence: float = Field(..., description="Average confidence score")
    most_recent_verification: Optional[datetime] = Field(None, description="Most recent verification timestamp") 