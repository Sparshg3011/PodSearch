import yt_dlp
from typing import List
from ..models.youtube import YouTubeVideo

class YouTubeService:
    @staticmethod
    def search_videos(query: str, max_results: int = 5) -> List[YouTubeVideo]:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'default_search': 'ytsearch',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                
                videos = []
                if 'entries' in search_results:
                    for entry in search_results['entries']:
                        if entry:
                            videos.append(YouTubeService.extract_basic_video_info(entry))
                
                return videos
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    @staticmethod
    def get_video_info(video_id: str) -> YouTubeVideo:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                url = f"https://www.youtube.com/watch?v={video_id}"
                entry = ydl.extract_info(url, download=False)
                return YouTubeService.extract_basic_video_info(entry)
        except Exception as e:
            print(f"Video info error: {e}")
            raise Exception(f"Video not found: {video_id}")
    
    @staticmethod
    def extract_basic_video_info(entry: dict) -> YouTubeVideo:
        available_languages = []
        if entry.get('subtitles'):
            available_languages.extend(list(entry['subtitles'].keys()))
        if entry.get('automatic_captions'):
            available_languages.extend(list(entry['automatic_captions'].keys()))
        
        return YouTubeVideo(
            id=entry.get('id', ''),
            title=entry.get('title', 'Unknown Title'),
            duration=entry.get('duration', 0),
            view_count=entry.get('view_count', 0),
            upload_date=entry.get('upload_date', ''),
            uploader=entry.get('uploader', 'Unknown'),
            description=entry.get('description', '')[:500] if entry.get('description') else '',
            thumbnail_url=entry.get('thumbnail', ''),
            available_languages=list(set(available_languages)),
            has_captions=bool(available_languages),
            url=f"https://www.youtube.com/watch?v={entry.get('id', '')}"
        ) 