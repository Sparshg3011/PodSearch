from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import yt_dlp
import tempfile
import os
from pydantic import BaseModel

router = APIRouter()

class YouTubeVideo(BaseModel):
    id: str
    title: str
    channel: str
    duration: Optional[int] = None 
    url: str
    description: Optional[str] = None
    has_captions: bool = False
    available_languages: List[str] = []

class YouTubeSearchResponse(BaseModel):
    results: List[YouTubeVideo]
    query: str

class TranscriptResponse(BaseModel):
    video_id: str
    title: str
    transcript: Optional[str] = None
    available_languages: List[str] = []
    has_manual_captions: bool = False
    has_auto_captions: bool = False

def get_available_captions(entry: dict) -> tuple[List[str], bool, bool]:
    """Get available caption languages and types"""
    languages = []
    has_manual = bool(entry.get('subtitles'))
    has_auto = bool(entry.get('automatic_captions'))
    
    if entry.get('subtitles'):
        languages.extend(list(entry['subtitles'].keys()))
    if entry.get('automatic_captions'):
        languages.extend(list(entry['automatic_captions'].keys()))
    
    return list(set(languages)), has_manual, has_auto

def extract_caption_text(video_id: str, language: str = 'en') -> Optional[str]:
    """Download and extract actual caption text"""
    try:
        import urllib.request
        import json
        import re
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [language, 'en'],
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Try to get subtitle entries directly from the info
            subtitles = info.get('subtitles', {})
            auto_captions = info.get('automatic_captions', {})
            
            # Try manual subtitles first, then auto captions
            all_subs = {**subtitles, **auto_captions}
            
            # Try the requested language first, then fallback to English variants
            lang_candidates = [language, 'en', 'en-US', 'en-GB']
            
            for lang in lang_candidates:
                if lang in all_subs and all_subs[lang]:
                    # Try each subtitle format available
                    for sub_info in all_subs[lang]:
                        if 'url' not in sub_info:
                            continue
                            
                        try:
                            with urllib.request.urlopen(sub_info['url']) as response:
                                subtitle_content = response.read().decode('utf-8')
                            
                            # Handle different subtitle formats
                            if sub_info.get('ext') == 'json3':
                                # Parse YouTube's JSON3 format
                                data = json.loads(subtitle_content)
                                transcript_lines = []
                                
                                if 'events' in data:
                                    for event in data['events']:
                                        if 'segs' in event:
                                            for seg in event['segs']:
                                                if 'utf8' in seg:
                                                    text = seg['utf8'].strip()
                                                    if text and text != '\n':
                                                        # Clean up text
                                                        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
                                                        text = text.replace('\n', ' ').strip()
                                                        if text:
                                                            transcript_lines.append(text)
                                
                                if transcript_lines:
                                    full_text = ' '.join(transcript_lines)
                                    # Truncate if too long and add ellipsis
                                    if len(full_text) > 3000:
                                        return full_text[:3000] + '...'
                                    return full_text
                            
                            elif sub_info.get('ext') in ['vtt', 'srv3', 'srv2']:
                                # Parse VTT/SRV format
                                lines = subtitle_content.split('\n')
                                transcript_lines = []
                                
                                for line in lines:
                                    line = line.strip()
                                    # Skip VTT headers, timestamps, and empty lines
                                    if (line and 
                                        not line.startswith('WEBVTT') and 
                                        not line.startswith('NOTE') and
                                        not '-->' in line and
                                        not line.startswith('STYLE') and
                                        not line.isdigit() and
                                        not line.startswith('<')):
                                        # Remove any remaining HTML tags
                                        clean_line = re.sub(r'<[^>]+>', '', line)
                                        if clean_line.strip():
                                            transcript_lines.append(clean_line.strip())
                                
                                if transcript_lines:
                                    full_text = ' '.join(transcript_lines)
                                    if len(full_text) > 3000:
                                        return full_text[:3000] + '...'
                                    return full_text
                                    
                        except Exception as e:
                            print(f"Error downloading subtitle from URL: {e}")
                            continue
            
            return "Captions available but could not extract text content."
                
    except Exception as e:
        print(f"Error extracting captions: {e}")
        return f"Error extracting captions: {str(e)}"

def extract_basic_video_info(entry: dict) -> YouTubeVideo:
    """Extract basic video information"""
    languages, has_manual, has_auto = get_available_captions(entry)
    
    return YouTubeVideo(
        id=entry.get('id', ''),
        title=entry.get('title', 'Unknown Title'),
        channel=entry.get('uploader', 'Unknown Channel'),
        duration=entry.get('duration'),
        url=f"https://www.youtube.com/watch?v={entry.get('id', '')}",
        description=entry.get('description', '')[:200] + '...' if entry.get('description') and len(entry.get('description', '')) > 200 else entry.get('description', ''),
        has_captions=bool(languages),
        available_languages=languages
    )

@router.get("/search", response_model=YouTubeSearchResponse)
async def search_youtube(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(5, ge=1, le=20, description="Maximum number of results")
):
    """Search YouTube videos and return basic info with caption availability"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False, 
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
        }
        
        search_query = f"ytsearch{max_results}:{q}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(search_query, download=False)
            
            if not search_results or 'entries' not in search_results:
                return YouTubeSearchResponse(results=[], query=q)
            
            videos = []
            for entry in search_results['entries']:
                if entry:
                    try:
                        video = extract_basic_video_info(entry)
                        videos.append(video)
                    except Exception as e:
                        print(f"Error processing video: {e}")
                        continue
            
            return YouTubeSearchResponse(results=videos, query=q)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/transcript/{video_id}", response_model=TranscriptResponse)
async def get_transcript(
    video_id: str,
    language: str = Query("en", description="Preferred language (e.g., 'en', 'es')")
):
    """Get transcript/captions for a YouTube video"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            languages, has_manual, has_auto = get_available_captions(info)
            
            # Try to get actual transcript text
            transcript_text = extract_caption_text(video_id, language)
            
            if not transcript_text:
                transcript_text = "Captions detected but could not extract text. Try a different language or video."
            
            return TranscriptResponse(
                video_id=video_id,
                title=info.get('title', 'Unknown'),
                transcript=transcript_text,
                available_languages=languages,
                has_manual_captions=has_manual,
                has_auto_captions=has_auto
            )
            
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch transcript: {str(e)}")

@router.get("/video/{video_id}")
async def get_video_info(video_id: str):
    """Get detailed info about a specific video"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video = extract_basic_video_info(info)
            return video
            
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")

@router.get("/debug/{video_id}")
async def debug_captions(video_id: str):
    """Debug endpoint to see raw caption data"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            subtitles = info.get('subtitles', {})
            auto_captions = info.get('automatic_captions', {})
            
            return {
                "video_id": video_id,
                "title": info.get('title'),
                "manual_subtitles": {lang: len(subs) for lang, subs in subtitles.items()},
                "auto_captions": {lang: len(subs) for lang, subs in auto_captions.items()},
                "sample_subtitle_info": {
                    "en_manual": subtitles.get('en', [{}])[0] if subtitles.get('en') else None,
                    "en_auto": auto_captions.get('en', [{}])[0] if auto_captions.get('en') else None
                }
            }
            
    except Exception as e:
        return {"error": str(e)}