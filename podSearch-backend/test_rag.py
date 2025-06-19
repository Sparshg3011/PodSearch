#!/usr/bin/env python3
"""
Test script for RAG functionality
This script demonstrates how to use the RAG pipeline with transcript data
"""

import asyncio
import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_VIDEO_ID = "dQw4w9WgXcQ"  # Replace with actual video ID

class RAGTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        
    def make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url)
            elif method.upper() == "POST":
                response = requests.post(url, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return {"error": str(e)}
    
    def test_health_check(self):
        """Test API health check"""
        print("🔍 Testing API health...")
        result = self.make_request("GET", "/health")
        print(f"✅ Health check: {result}")
        return result
    
    def test_rag_health_check(self):
        """Test RAG service health check"""
        print("\n🔍 Testing RAG service health...")
        result = self.make_request("GET", "/api/rag/health")
        print(f"✅ RAG health check: {result}")
        return result
    
    def test_get_transcript(self, video_id: str):
        """Test getting transcript from database"""
        print(f"\n🔍 Getting transcript for video {video_id}...")
        result = self.make_request("GET", f"/api/transcripts/search/{video_id}")
        
        if "error" not in result:
            print(f"✅ Found transcript with {result.get('segments_count', 0)} segments")
            # Show first few segments
            segments = result.get('segments', [])
            for i, segment in enumerate(segments[:3]):
                print(f"   Segment {i+1}: {segment.get('text', '')[:100]}...")
        else:
            print(f"❌ Failed to get transcript: {result['error']}")
        
        return result
    
    def test_process_transcript(self, video_id: str):
        """Test processing transcript for RAG"""
        print(f"\n🔍 Processing transcript for RAG (video {video_id})...")
        
        data = {
            "video_id": video_id,
            "overwrite": True
        }
        
        result = self.make_request("POST", f"/api/rag/process/{video_id}", data)
        
        if result.get("success"):
            print(f"✅ Processed transcript: {result.get('chunks_stored', 0)} chunks stored")
            print(f"   Collection: {result.get('collection_name', 'N/A')}")
        else:
            print(f"❌ Failed to process transcript: {result.get('error', 'Unknown error')}")
        
        return result
    
    def test_search_transcript(self, video_id: str, query: str):
        """Test searching transcript"""
        print(f"\n🔍 Searching transcript for: '{query}'...")
        
        data = {
            "query": query,
            "top_k": 3
        }
        
        result = self.make_request("POST", f"/api/rag/search/{video_id}", data)
        
        if result.get("success"):
            results = result.get("results", [])
            print(f"✅ Found {len(results)} relevant segments:")
            
            for i, r in enumerate(results):
                timestamp = r.get("timestamp", 0)
                score = r.get("relevance_score", 0)
                text = r.get("text", "")
                print(f"   {i+1}. [{int(timestamp//60):02d}:{int(timestamp%60):02d}] "
                      f"(Score: {score:.3f}) {text[:100]}...")
        else:
            print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def test_generate_response(self, video_id: str, query: str):
        """Test generating RAG response"""
        print(f"\n🔍 Generating response for: '{query}'...")
        
        data = {
            "query": query,
            "top_k": 3
        }
        
        result = self.make_request("POST", f"/api/rag/generate/{video_id}", data)
        
        if result.get("success"):
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            retrieval_only = result.get("retrieval_only", False)
            
            print(f"✅ Generated response:")
            print(f"   Answer: {answer}")
            print(f"   Sources used: {len(sources)}")
            print(f"   Retrieval only: {retrieval_only}")
            
            if sources:
                print("   Source segments:")
                for i, source in enumerate(sources[:2]):
                    timestamp = source.get("timestamp", 0)
                    text = source.get("text", "")
                    print(f"     {i+1}. [{int(timestamp//60):02d}:{int(timestamp%60):02d}] {text[:80]}...")
        else:
            print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def test_list_processed_videos(self):
        """Test listing processed videos"""
        print("\n🔍 Listing processed videos...")
        result = self.make_request("GET", "/api/rag/list")
        
        if "error" not in result:
            video_ids = result.get("video_ids", [])
            count = result.get("count", 0)
            print(f"✅ Found {count} processed videos: {video_ids}")
        else:
            print(f"❌ Failed to list videos: {result['error']}")
        
        return result
    
    def run_full_test(self, video_id: str):
        """Run complete RAG test suite"""
        print("🚀 Starting RAG Pipeline Test Suite")
        print("=" * 50)
        
        # 1. Health checks
        self.test_health_check()
        self.test_rag_health_check()
        
        # 2. Check if transcript exists
        transcript_result = self.test_get_transcript(video_id)
        if "error" in transcript_result:
            print(f"\n❌ Cannot proceed without transcript data for {video_id}")
            print("   Please run the transcript extraction first:")
            print(f"   POST /api/transcripts/transcript-supadata/{video_id}")
            return
        
        # 3. Process transcript for RAG
        process_result = self.test_process_transcript(video_id)
        if not process_result.get("success"):
            print(f"\n❌ Cannot proceed without processing transcript")
            return
        
        # 4. Test search functionality
        search_queries = [
            "What is the main topic?",
            "Tell me about the key points",
            "What does the speaker say about technology?"
        ]
        
        for query in search_queries:
            self.test_search_transcript(video_id, query)
        
        # 5. Test response generation
        generate_queries = [
            "What is this video about?",
            "Summarize the main points",
            "What are the key takeaways?"
        ]
        
        for query in generate_queries:
            self.test_generate_response(video_id, query)
        
        # 6. List processed videos
        self.test_list_processed_videos()
        
        print("\n🎉 RAG Pipeline Test Suite Complete!")
        print("=" * 50)

def main():
    """Main test function"""
    tester = RAGTester()
    
    # Get video ID from user or use default
    video_id = input(f"Enter video ID to test (or press Enter for default '{TEST_VIDEO_ID}'): ").strip()
    if not video_id:
        video_id = TEST_VIDEO_ID
    
    print(f"\nTesting RAG pipeline with video ID: {video_id}")
    
    # Run the test suite
    tester.run_full_test(video_id)

if __name__ == "__main__":
    main() 