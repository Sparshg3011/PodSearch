from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class RAGSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for transcript content")
    top_k: int = Field(100, description="Number of top results to return", ge=1, le=200)

class RAGSearchResult(BaseModel):
    text: str = Field(..., description="Retrieved text segment")
    timestamp: Optional[float] = Field(None, description="Timestamp in seconds")
    segment_index: int = Field(..., description="Index of the original segment")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class RAGSearchResponse(BaseModel):
    success: bool = Field(..., description="Whether the search was successful")
    query: str = Field(..., description="Original search query")
    video_id: str = Field(..., description="Video ID that was searched")
    results: List[RAGSearchResult] = Field(default_factory=list, description="Search results")
    error: Optional[str] = Field(None, description="Error message if search failed")

class RAGGenerateRequest(BaseModel):
    query: str = Field(..., description="Question to ask about the transcript")
    top_k: int = Field(100, description="Number of context segments to use", ge=1, le=200)

class RAGGenerateResponse(BaseModel):
    success: bool = Field(..., description="Whether the generation was successful")
    query: str = Field(..., description="Original question")
    video_id: str = Field(..., description="Video ID that was queried")
    answer: str = Field(..., description="Generated answer")
    sources: List[RAGSearchResult] = Field(default_factory=list, description="Source segments used")
    retrieval_only: bool = Field(False, description="Whether only retrieval was performed (no LLM)")
    error: Optional[str] = Field(None, description="Error message if generation failed")

class RAGProcessRequest(BaseModel):
    overwrite: bool = Field(False, description="Whether to overwrite existing data")

class RAGProcessResponse(BaseModel):
    success: bool = Field(..., description="Whether processing was successful")
    video_id: str = Field(..., description="Video ID that was processed")
    chunks_stored: Optional[int] = Field(None, description="Number of chunks stored")
    collection_name: Optional[str] = Field(None, description="Name of the created collection")
    error: Optional[str] = Field(None, description="Error message if processing failed")

class RAGCollection(BaseModel):
    name: str = Field(..., description="Name of the collection (video_id)")
    count: int = Field(..., description="Number of chunks in the collection")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")

class RAGListResponse(BaseModel):
    collections: List[RAGCollection] = Field(default_factory=list, description="List of RAG collections")
    count: int = Field(..., description="Number of videos with RAG data") 