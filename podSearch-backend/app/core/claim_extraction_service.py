import os
import logging
import re
from typing import List, Dict, Any
import openai

OPENAI_AVAILABLE = True
try:
    import openai
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class ClaimExtractionService:
    """Service for extracting factual claims from text using OpenAI API"""
    
    def __init__(self):
        """Initialize the claim extraction service"""
        self.client = None
        if os.getenv("OPENAI_API_KEY") and OPENAI_AVAILABLE:
            try:
                self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info("OpenAI client initialized for claim extraction")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
        else:
            logger.warning("OpenAI API key not found or OpenAI not available. Using pattern-based extraction.")
    
    async def extract_claims(self, text: str, max_claims: int = 10) -> List[str]:
        """Extract factual claims from text"""
        try:
            if self.client:
                return await self._extract_claims_with_openai(text, max_claims)
            else:
                return self._extract_claims_with_patterns(text, max_claims)
        except Exception as e:
            logger.error(f"Error extracting claims: {str(e)}")
            return []
    
    async def _extract_claims_with_openai(self, text: str, max_claims: int = 10) -> List[str]:
        """Extract claims using OpenAI API"""
        try:
            prompt = f"""
            Extract factual claims from the following text that can be fact-checked.
            Focus on specific, verifiable statements including:
            - Scientific facts and research findings
            - Historical events and dates
            - Statistics and numerical data
            - Specific claims about people, places, or organizations
            - Medical or health-related statements
            
            Avoid extracting:
            - Opinions or subjective statements
            - General observations
            - Questions or hypothetical scenarios
            - Personal anecdotes
            
            Text to analyze:
            {text[:4000]}
            
            Please return up to {max_claims} factual claims, one per line:
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying factual claims that can be verified."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            claims = [claim.strip() for claim in content.split('\n') if claim.strip()]
            
            # Clean and filter claims
            filtered_claims = []
            for claim in claims:
                # Remove numbering and bullet points
                claim = re.sub(r'^\d+\.?\s*', '', claim)
                claim = re.sub(r'^[-•*]\s*', '', claim)
                
                # Skip very short or very long claims
                if 15 <= len(claim) <= 300 and any(char.isalpha() for char in claim):
                    filtered_claims.append(claim)
            
            return filtered_claims[:max_claims]
            
        except Exception as e:
            logger.error(f"OpenAI claim extraction error: {str(e)}")
            return self._extract_claims_with_patterns(text, max_claims)
    
    def _extract_claims_with_patterns(self, text: str, max_claims: int = 10) -> List[str]:
        """Extract claims using pattern matching as fallback"""
        claims = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Patterns for factual claims
        fact_patterns = [
            r'(?:study|research|survey|report|data)\s+(?:shows?|indicates?|reveals?|found|discovered)',
            r'(?:according to|research shows|studies show|data shows|scientists found)',
            r'\d+(?:,\d+)*(?:\.\d+)?\s*(?:%|percent|million|billion|thousand|years?)',
            r'(?:was|were|is|are)\s+(?:discovered|invented|created|founded|established)\s+in\s+\d{4}',
            r'(?:causes?|leads? to|results? in|increases?|decreases?|reduces?|improves?)',
            r'(?:contains?|includes?|comprises?|consists? of)\s+\d+',
            r'(?:located|situated|based|found)\s+in\s+[A-Z][a-zA-Z\s]+',
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip very short sentences
            if len(sentence) < 20:
                continue
            
            # Check if sentence matches any fact pattern
            for pattern in fact_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claims.append(sentence)
                    break
            
            if len(claims) >= max_claims:
                break
        
        return claims[:max_claims]
    
    def categorize_claims(self, claims: List[str]) -> Dict[str, List[str]]:
        """Categorize claims by type"""
        categories = {
            "scientific": [],
            "historical": [],
            "statistical": [],
            "geographical": [],
            "medical": [],
            "other": []
        }
        
        for claim in claims:
            claim_lower = claim.lower()
            
            if any(keyword in claim_lower for keyword in ['study', 'research', 'scientist', 'experiment']):
                categories["scientific"].append(claim)
            elif any(keyword in claim_lower for keyword in ['founded', 'established', 'invented', 'discovered']):
                categories["historical"].append(claim)
            elif re.search(r'\d+(?:\.\d+)?\s*(?:%|percent|million|billion)', claim):
                categories["statistical"].append(claim)
            elif any(keyword in claim_lower for keyword in ['located', 'situated', 'country', 'city']):
                categories["geographical"].append(claim)
            elif any(keyword in claim_lower for keyword in ['health', 'medical', 'disease', 'treatment']):
                categories["medical"].append(claim)
            else:
                categories["other"].append(claim)
        
        return categories 