from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging
import time
from ..models.fact_verification import (
    FactVerificationRequest, FactVerificationResponse,
    BatchVerificationRequest, BatchVerificationResponse,
    VerificationStatsResponse, VerificationStatus
)
from ..core.fact_verification_service import FactVerificationService
from ..core.transcript_service import TranscriptService
import openai
import os
import re

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
fact_verification_service = FactVerificationService()
transcript_service = TranscriptService()

@router.post("/verify", response_model=FactVerificationResponse)
async def verify_claims(request: FactVerificationRequest):
    """Verify a list of claims using the simplified fact verification agent"""
    try:
        logger.info(f"Received verification request for {len(request.claims)} claims")
        
        # Validate claims
        if not request.claims:
            raise HTTPException(status_code=400, detail="No claims provided for verification")
        
        if len(request.claims) > 20:
            raise HTTPException(status_code=400, detail="Too many claims. Maximum 20 claims per request")
        
        # Verify the claims
        response = await fact_verification_service.verify_facts(request)
        
        logger.info(f"Completed verification for {len(request.claims)} claims in {response.processing_time:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in claim verification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/{video_id}", response_model=BatchVerificationResponse)
async def batch_verify_transcript(video_id: str, request: BatchVerificationRequest = None):
    """Extract claims from a transcript and verify them automatically"""
    try:
        start_time = time.time()
        
        if request is None:
            request = BatchVerificationRequest(transcript_id=video_id)
        
        # Get transcript data from database
        segments = await transcript_service.get_transcript_from_db(video_id)
        
        if not segments:
            raise HTTPException(status_code=404, detail="Transcript not found in database")
        
        # Combine transcript segments into full text
        full_transcript = " ".join([segment.get("text", "") for segment in segments])
        
        # Extract claims from transcript if auto_extract is enabled
        extracted_claims = []
        if request.auto_extract_claims:
            extracted_claims = await _extract_claims_from_transcript(full_transcript, request.max_claims)
        
        # Combine with custom claims
        all_claims = extracted_claims + request.custom_claims
        
        if not all_claims:
            return BatchVerificationResponse(
                success=True,
                transcript_id=video_id,
                extracted_claims=[],
                verifications=[],
                summary={},
                processing_time=time.time() - start_time,
                error="No claims found or provided for verification"
            )
        
        # Create verification request
        verification_request = FactVerificationRequest(
            claims=all_claims[:request.max_claims],  # Limit to max_claims
            video_id=video_id,
            context=full_transcript[:1000],  # Provide context
            search_depth=request.search_depth
        )
        
        # Verify claims
        verification_response = await fact_verification_service.verify_facts(verification_request)
        
        # Create summary
        summary = _create_verification_summary(verification_response.verifications)
        
        processing_time = time.time() - start_time
        
        return BatchVerificationResponse(
            success=True,
            transcript_id=video_id,
            extracted_claims=extracted_claims,
            verifications=verification_response.verifications,
            summary=summary,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch verification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=VerificationStatsResponse)
async def get_verification_stats():
    """Get statistics about fact verification history"""
    try:
        stats = fact_verification_service.get_verification_stats()
        
        return VerificationStatsResponse(
            service_status=stats["service_status"],
            available_sources=stats["available_sources"],
            openai_client_available=stats["openai_client_available"],
            last_check=stats["last_check"]
        )
        
    except Exception as e:
        logger.error(f"Error getting verification stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def fact_verification_health_check():
    """Health check for fact verification service"""
    try:
        # Check if OpenAI API key is configured
        openai_configured = bool(os.getenv("OPENAI_API_KEY"))
        
        # Get basic stats
        stats = fact_verification_service.get_verification_stats()
        
        return {
            "status": "healthy",
            "service": "Fact Verification",
            "openai_configured": openai_configured,
            "available_sources": stats["available_sources"],
            "available_tools": [
                "Wikipedia Search",
                "PubMed Search", 
                "Semantic Scholar Search",
                "DuckDuckGo Search"
            ],
            "agent_type": "simplified"
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "Fact Verification",
            "error": str(e)
        }

@router.post("/extract-claims")
async def extract_claims_from_text(text: str, max_claims: int = 10):
    """Extract potential factual claims from text"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text provided")
        
        claims = await _extract_claims_from_transcript(text, max_claims)
        
        return {
            "success": True,
            "text_length": len(text),
            "extracted_claims": claims,
            "total_claims": len(claims)
        }
        
    except Exception as e:
        logger.error(f"Error extracting claims: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

async def _extract_claims_from_transcript(transcript: str, max_claims: int = 10) -> List[str]:
    """Extract factual claims from transcript using OpenAI API"""
    try:
        # Check if OpenAI is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OpenAI API key not found. Using basic claim extraction")
            return _basic_claim_extraction(transcript, max_claims)
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        prompt = f"""
        Extract factual claims from the following transcript that can be fact-checked.
        Focus on specific, verifiable statements about facts, statistics, historical events, scientific claims, etc.
        Ignore opinions, subjective statements, and conversational filler.
        
        Return only the top {max_claims} most important factual claims, one per line.
        
        Transcript:
        {transcript[:3000]}
        
        Extracted Claims:
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at extracting factual claims from text that can be verified."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        claims = [claim.strip() for claim in content.split('\n') if claim.strip() and not claim.strip().startswith('-')]
        
        # Filter and clean claims
        filtered_claims = []
        for claim in claims[:max_claims]:
            if len(claim) > 10 and any(char.isalpha() for char in claim):
                filtered_claims.append(claim)
        
        return filtered_claims[:max_claims]
        
    except Exception as e:
        logger.error(f"Error in LLM claim extraction: {str(e)}")
        return _basic_claim_extraction(transcript, max_claims)

def _basic_claim_extraction(transcript: str, max_claims: int = 10) -> List[str]:
    """Basic pattern-based claim extraction as fallback"""
    claims = []
    
    # Patterns for different types of factual claims
    patterns = [
        r'[A-Z][^.!?]*(?:is|are|was|were|has|have|had)\s+(?:about|approximately|over|under|more than|less than)?\s*\d+(?:\.\d+)?(?:%|percent|million|billion|thousand)',
        r'[A-Z][^.!?]*(?:study|research|survey|report)\s+(?:shows|found|discovered|concluded|revealed)[^.!?]*[.!?]',
        r'[A-Z][^.!?]*(?:founded|established|created|invented|discovered)\s+in\s+\d{4}[^.!?]*[.!?]',
        r'[A-Z][^.!?]*(?:located|situated|based)\s+in\s+[A-Z][^.!?]*[.!?]',
        r'[A-Z][^.!?]*(?:contains|includes|comprises)\s+[^.!?]*[.!?]'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        claims.extend(matches)
        if len(claims) >= max_claims:
            break
    
    return claims[:max_claims]

def _create_verification_summary(verifications: List) -> dict:
    """Create summary statistics from verification results"""
    if not verifications:
        return {}
    
    total = len(verifications)
    status_counts = {}
    total_confidence = 0
    
    for verification in verifications:
        status = verification.status.value if hasattr(verification.status, 'value') else str(verification.status)
        status_counts[status] = status_counts.get(status, 0) + 1
        total_confidence += verification.confidence
    
    return {
        "total_claims": total,
        "status_breakdown": status_counts,
        "average_confidence": round(total_confidence / total, 2) if total > 0 else 0,
        "verification_rate": round(100 * status_counts.get("VERIFIED", 0) / total, 1) if total > 0 else 0
    } 