# RAG Pipeline for PodSearch

This document explains how to use the Retrieval-Augmented Generation (RAG) pipeline implemented in the PodSearch backend.

## Overview

The RAG pipeline allows you to:
1. **Process** transcript data into embeddings for semantic search
2. **Search** for relevant segments in transcripts using natural language queries
3. **Generate** AI-powered responses based on transcript content

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (optional, for LLM functionality):
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

3. Start the server:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### 1. Process Transcript for RAG
**POST** `/api/rag/process/{video_id}`

Process a video's transcript data and store embeddings for semantic search.

```bash
curl -X POST "http://localhost:8000/api/rag/process/VIDEO_ID" \
  -H "Content-Type: application/json" \
  -d '{"video_id": "VIDEO_ID", "overwrite": true}'
```

### 2. Search Transcript
**POST** `/api/rag/search/{video_id}`

Search for relevant segments in a video's transcript.

```bash
curl -X POST "http://localhost:8000/api/rag/search/VIDEO_ID" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic?", "top_k": 5}'
```

### 3. Generate AI Response
**POST** `/api/rag/generate/{video_id}`

Generate an AI-powered response based on transcript content.

```bash
curl -X POST "http://localhost:8000/api/rag/generate/VIDEO_ID" \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the key points", "top_k": 3}'
```

### 4. List Processed Videos
**GET** `/api/rag/list`

List all videos that have been processed for RAG.

```bash
curl "http://localhost:8000/api/rag/list"
```

### 5. Delete RAG Data
**DELETE** `/api/rag/delete/{video_id}`

Delete RAG data for a specific video.

```bash
curl -X DELETE "http://localhost:8000/api/rag/delete/VIDEO_ID"
```

### 6. Health Check
**GET** `/api/rag/health`

Check the health status of the RAG service.

```bash
curl "http://localhost:8000/api/rag/health"
```

## Usage Workflow

1. **First**, get transcript data using the existing endpoint:
   ```bash
   POST /api/transcripts/transcript-supadata/{video_id}
   ```

2. **Then**, process the transcript for RAG:
   ```bash
   POST /api/rag/process/{video_id}
   ```

3. **Now you can**:
   - Search for specific content: `POST /api/rag/search/{video_id}`
   - Generate AI responses: `POST /api/rag/generate/{video_id}`

## Testing

Run the comprehensive test suite:

```bash
cd podSearch-backend
python test_rag.py
```

The test script will:
1. Check API health
2. Verify transcript data exists
3. Process transcript for RAG
4. Test search functionality
5. Test response generation
6. List processed videos

## Technical Details

### Embedding Model
- Uses `all-MiniLM-L6-v2` for fast, efficient embeddings
- Sentence-transformers based model optimized for semantic similarity

### Vector Database
- ChromaDB for vector storage and similarity search
- Persistent storage in `./chroma_db/` directory
- Each video gets its own collection: `transcript_{video_id}`

### Text Processing
- Chunks transcript segments into smaller pieces (500 chars, 50 overlap)
- Preserves timestamp information for accurate referencing
- Filters out very small chunks (< 10 characters)

### LLM Integration (Optional)
- Uses OpenAI GPT-3.5-turbo for response generation
- Falls back to retrieval-only mode if no API key provided
- Includes context from top-k most relevant segments

## Response Format Examples

### Search Response
```json
{
  "success": true,
  "query": "main topic",
  "video_id": "VIDEO_ID",
  "results": [
    {
      "text": "The main topic of this video is...",
      "timestamp": 45.6,
      "segment_index": 2,
      "relevance_score": 0.89,
      "metadata": {...}
    }
  ]
}
```

### Generate Response
```json
{
  "success": true,
  "query": "What is this video about?",
  "video_id": "VIDEO_ID", 
  "answer": "This video discusses...",
  "sources": [...],
  "retrieval_only": false
}
```

## Troubleshooting

### Common Issues

1. **"Transcript not found"**: Ensure you've extracted the transcript first using `/api/transcripts/transcript-supadata/{video_id}`

2. **"Video not processed for RAG"**: Run `/api/rag/process/{video_id}` first

3. **Empty search results**: Try broader search terms or check if transcript was processed correctly

4. **LLM not working**: Set `OPENAI_API_KEY` environment variable, or use retrieval-only mode

### Logs
Check the application logs for detailed error messages and debugging information.

## Performance Notes

- First-time processing may take a few seconds depending on transcript length
- Search operations are typically very fast (< 100ms)
- LLM generation adds 1-3 seconds depending on context size
- Vector database persists between server restarts 