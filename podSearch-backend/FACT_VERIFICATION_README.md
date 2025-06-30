# Fact Verification System

## Overview

The Fact Verification System is an AI-powered, agent-driven solution for verifying factual claims using multiple authoritative sources. Built with LangGraph, it employs a sophisticated multi-tool approach to cross-reference information and provide accuracy ratings with detailed explanations.

## Features

### 🔍 Multi-Source Verification
- **Wikipedia API**: For general knowledge verification
- **PubMed API**: For medical and scientific claims
- **Semantic Scholar API**: For academic research verification
- **DuckDuckGo Search**: For current events and general web search
- **News APIs**: For recent news and current affairs

### 🤖 LangGraph Agent
- Intelligent claim processing workflow
- Automated source selection based on claim type
- Cross-referencing multiple sources for accuracy
- Confidence scoring and reasoning explanation

### 📊 Verification Ratings
- ✅ **Verified**: Strong evidence supports the claim
- ⚠️ **Partially Verified**: Limited or mixed evidence
- ❌ **False**: Evidence contradicts the claim
- 🔍 **Unclear/Insufficient Evidence**: Not enough reliable sources

### 🎯 Contextual Explanations
- Detailed reasoning for each verification decision
- Source citations and references
- Confidence levels (0.0 - 1.0)
- Agent reasoning process documentation

## API Endpoints

### Manual Fact Verification

#### POST `/api/fact-verification/verify`
Verify a list of claims manually.

**Request Body:**
```json
{
  "claims": [
    "The Great Wall of China is visible from space",
    "Caffeine can improve cognitive performance"
  ],
  "video_id": "optional_video_id",
  "context": "Additional context for verification",
  "search_depth": 3,
  "include_academic": true,
  "include_news": true
}
```

**Response:**
```json
{
  "success": true,
  "verifications": [
    {
      "claim": "The Great Wall of China is visible from space",
      "status": "❌ False",
      "confidence": 0.85,
      "explanation": "Multiple NASA sources and astronauts confirm...",
      "sources": [
        {
          "title": "NASA - Great Wall of China",
          "url": "https://nasa.gov/...",
          "source_type": "Search Engine",
          "relevance_score": 0.9,
          "excerpt": "The Great Wall is not visible...",
          "publication_date": "2023-05-15",
          "author": "NASA"
        }
      ],
      "verification_date": "2024-01-15T10:30:00",
      "agent_reasoning": "Analyzed 5 sources using multi-tool search approach."
    }
  ],
  "total_claims": 2,
  "processing_time": 12.5
}
```

### Batch Verification from Transcripts

#### POST `/api/fact-verification/batch/{video_id}`
Automatically extract and verify claims from a video transcript.

**Request Body:**
```json
{
  "transcript_id": "video_123",
  "auto_extract_claims": true,
  "custom_claims": [
    "Additional claim to verify"
  ],
  "max_claims": 10,
  "search_depth": 3
}
```

**Response:**
```json
{
  "success": true,
  "transcript_id": "video_123",
  "extracted_claims": [
    "Extracted claim 1",
    "Extracted claim 2"
  ],
  "verifications": [...],
  "summary": {
    "✅ Verified": 3,
    "⚠️ Partially Verified": 2,
    "❌ False": 1,
    "🔍 Unclear/Insufficient Evidence": 4
  },
  "processing_time": 45.2
}
```

### Claim Extraction

#### POST `/api/fact-verification/extract-claims`
Extract potential factual claims from text.

**Request Body:**
```json
{
  "text": "Your text content here...",
  "max_claims": 10
}
```

### Statistics

#### GET `/api/fact-verification/stats`
Get verification statistics and history.

**Response:**
```json
{
  "total_verifications": 150,
  "verification_breakdown": {
    "✅ Verified": 45,
    "⚠️ Partially Verified": 60,
    "❌ False": 25,
    "🔍 Unclear/Insufficient Evidence": 20
  },
  "source_breakdown": {
    "Wikipedia": 80,
    "PubMed": 45,
    "Search Engine": 120,
    "News": 30
  },
  "average_confidence": 0.72,
  "most_recent_verification": "2024-01-15T10:30:00"
}
```

### Health Check

#### GET `/api/fact-verification/health`
Check the health and status of the fact verification service.

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Add the following to your `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Optional Dependencies
For enhanced claim extraction:
```bash
# Install spaCy model for better text processing
python -m spacy download en_core_web_sm
```

## Usage Examples

### Python Client Example
```python
import requests
import json

# Verify claims manually
claims_data = {
    "claims": [
        "The human brain uses 20% of the body's energy",
        "Goldfish have a 3-second memory"
    ],
    "search_depth": 5
}

response = requests.post(
    "http://localhost:8000/api/fact-verification/verify",
    json=claims_data
)

results = response.json()
for verification in results["verifications"]:
    print(f"Claim: {verification['claim']}")
    print(f"Status: {verification['status']}")
    print(f"Confidence: {verification['confidence']}")
    print(f"Explanation: {verification['explanation']}")
    print("-" * 50)
```

### JavaScript/Fetch Example
```javascript
async function verifyClaims(claims) {
    const response = await fetch('/api/fact-verification/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            claims: claims,
            search_depth: 3
        })
    });
    
    const results = await response.json();
    return results.verifications;
}

// Usage
const claims = [
    "Antarctica is the largest continent",
    "Coffee is the second most traded commodity after oil"
];

verifyClaims(claims).then(verifications => {
    verifications.forEach(v => {
        console.log(`${v.status}: ${v.claim}`);
        console.log(`Confidence: ${v.confidence}`);
    });
});
```

### Batch Processing Example
```python
# Verify claims from a video transcript
video_id = "abc123"
batch_request = {
    "transcript_id": video_id,
    "auto_extract_claims": True,
    "max_claims": 15,
    "search_depth": 4
}

response = requests.post(
    f"http://localhost:8000/api/fact-verification/batch/{video_id}",
    json=batch_request
)

results = response.json()
print(f"Extracted {len(results['extracted_claims'])} claims")
print(f"Verification Summary: {results['summary']}")
```

## Configuration

### Search Depth
Controls how many sources each tool searches:
- `1-3`: Fast, basic verification
- `4-6`: Balanced speed and accuracy
- `7-10`: Thorough, comprehensive verification

### Claim Extraction Settings
- **Auto Extract**: Automatically find factual claims in transcripts
- **Max Claims**: Limit the number of claims to process
- **Custom Claims**: Add specific claims to verify alongside extracted ones

## System Architecture

```
User Request
     ↓
API Endpoint
     ↓
Fact Verification Service
     ↓
LangGraph Agent
     ↓
┌─────────────────────────────────────────┐
│            Tool Orchestration           │
├─────────────┬─────────────┬─────────────┤
│  Wikipedia  │   PubMed    │   Scholar   │
│   Search    │   Search    │   Search    │
├─────────────┼─────────────┼─────────────┤
│ DuckDuckGo  │    News     │  Additional │
│   Search    │   Search    │    Tools    │
└─────────────┴─────────────┴─────────────┘
     ↓
Source Analysis & Verification
     ↓
Confidence Scoring & Explanation
     ↓
Formatted Response
```

## Error Handling

The system includes comprehensive error handling:

- **Network timeouts**: Automatic retry with fallback sources
- **API rate limits**: Intelligent throttling and queuing
- **Invalid claims**: Graceful handling with error messages
- **Source unavailability**: Fallback to alternative sources
- **LLM failures**: Pattern-based fallback for claim extraction

## Performance Optimization

- **Parallel processing**: Multiple tools search simultaneously
- **Caching**: Recent verification results cached temporarily
- **Batch processing**: Efficient handling of multiple claims
- **Source prioritization**: Higher-quality sources searched first

## Best Practices

1. **Claim Quality**: More specific claims yield better verification results
2. **Context**: Provide relevant context for better accuracy
3. **Batch Size**: Process 5-15 claims per batch for optimal performance
4. **Search Depth**: Balance speed vs. accuracy based on your needs
5. **Error Handling**: Always check the `success` field in responses

## Troubleshooting

### Common Issues

1. **No OpenAI API Key**: Fallback to pattern-based claim extraction
2. **Slow Response Times**: Reduce search_depth or claim count
3. **Low Confidence Scores**: Claims may be too vague or subjective
4. **Source Unavailability**: System automatically uses fallback sources

### Logs
Check application logs for detailed error information:
```bash
tail -f logs/fact_verification.log
```

## Contributing

To contribute to the fact verification system:

1. Add new tools in `fact_verification_service.py`
2. Enhance claim extraction patterns in `claim_extraction_service.py`
3. Improve verification logic in the LangGraph workflow
4. Add new source types in the models

## API Rate Limits

- **Verification requests**: 60 per minute per IP
- **Batch processing**: 10 per minute per IP
- **Health checks**: Unlimited

## Privacy & Security

- No claim data is permanently stored
- Source queries are anonymized
- API keys are securely handled
- HTTPS encryption for all endpoints 