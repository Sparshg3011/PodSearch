from fastapi import APIRouter
from ..models.verification import VerifyRequest, VerifyResponse, ClaimVerification, VerificationSource
from ..core.verification_service import VerificationService

router = APIRouter()
service = VerificationService()

@router.post("/", response_model=VerifyResponse)
async def verify_claim(request: VerifyRequest):
    try:
        result = await service.verify_claim(request.claim_text, max_sources=request.max_sources)
        sources = [VerificationSource(**s) for s in result["sources"]]
        claim = ClaimVerification(
            text=request.claim_text,
            verdict=result["verdict"],
            confidence=result["confidence"],
            sources=sources
        )
        return VerifyResponse(success=True, claim=request.claim_text, result=claim)
    except Exception as e:
        return VerifyResponse(success=False, claim=request.claim_text, error=str(e))
