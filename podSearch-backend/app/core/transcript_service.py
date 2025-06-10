from typing import Optional, List
import os
from datetime import datetime
from ..models.youtube import TranscriptSegment

try:
    from supadata import Supadata, SupadataError
    SUPADATA_AVAILABLE = True
except ImportError:
    SUPADATA_AVAILABLE = False

class TranscriptService:
    """Service for extracting YouTube transcripts using Supadata API"""
    
    def __init__(self):
        if SUPADATA_AVAILABLE:
            self.client = Supadata(api_key="sd_83b3af6342ea05dbca4b5baaa821efa7")
        else:
            self.client = None
    
    def extract_transcript(self, video_id: str, language: str = "en") -> dict:
        """
        Extract transcript for a given video ID
        
        Args:
            video_id: YouTube video ID
            language: Language code (default: "en")
            
        Returns:
            dict with transcript data and metadata
        """
        if not SUPADATA_AVAILABLE or not self.client:
            return {
                "success": False,
                "error": "Supadata library not available",
                "transcript": None,
                "segments": [],
                "metadata": {}
            }
        
        try:
            transcript_result = self.client.youtube.transcript(video_id=video_id, lang=language)
            
            segments_data = self._process_transcript_content_with_timestamps(transcript_result.content)
            
            if not segments_data["segments"]:
                try:
                    plain_text_result = self.client.youtube.transcript(video_id=video_id, text=True)
                    segments_data = self._process_transcript_content_with_timestamps(plain_text_result.content)
                except SupadataError:
                    pass
            
            if segments_data["segments"] and len(segments_data["text"].strip()) >= 10:
                return {
                    "success": True,
                    "error": None,
                    "transcript": segments_data["text"],
                    "segments": segments_data["segments"],
                    "metadata": {
                        "video_id": video_id,
                        "language": language,
                        "length": len(segments_data["text"]),
                        "segment_count": len(segments_data["segments"]),
                        "timestamp": datetime.now().isoformat(),
                        "source": "supadata"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Transcript is empty or too short",
                    "transcript": None,
                    "segments": [],
                    "metadata": {"video_id": video_id, "language": language}
                }
                
        except SupadataError as e:
            return {
                "success": False,
                "error": f"Supadata API error: {str(e)}",
                "transcript": None,
                "segments": [],
                "metadata": {"video_id": video_id, "language": language}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "transcript": None,
                "segments": [],
                "metadata": {"video_id": video_id, "language": language}
            }
    
    def _process_transcript_content_with_timestamps(self, content) -> dict:
        """
        Process transcript content and extract segments with timestamps
        
        Args:
            content: The transcript content from supadata
            
        Returns:
            Dict with text and segments list
        """
        segments = []
        text_content = ""
        
        if isinstance(content, list):
            for item in content:
                segment = self._extract_segment_data(item)
                if segment:
                    segments.append(segment)
                    text_content += segment.text + " "
        elif isinstance(content, str):
            segments.append(TranscriptSegment(text=content.strip()))
            text_content = content.strip()
        else:
            segment = self._extract_segment_data(content)
            if segment:
                segments.append(segment)
                text_content = segment.text
        
        return {
            "text": text_content.strip(),
            "segments": segments
        }
    
    def _extract_segment_data(self, item) -> Optional[TranscriptSegment]:
        """
        Extract segment data from various item formats
        
        Returns:
            TranscriptSegment object or None
        """
        if isinstance(item, dict):
            timestamp_ms = item.get('offset') or item.get('start') or item.get('time') or item.get('timestamp') or item.get('begin')
            timestamp = None
            if timestamp_ms is not None:
                timestamp = timestamp_ms / 1000.0  
            
            return TranscriptSegment(
                text=item.get('text', ''),
                timestamp=timestamp
            )
        elif isinstance(item, str):
            return TranscriptSegment(text=item)
        elif hasattr(item, 'text'):
            timestamp = None
            for attr_name in ['offset', 'start', 'time', 'timestamp', 'begin', 'start_time']:
                if hasattr(item, attr_name):
                    timestamp_ms = getattr(item, attr_name, None)
                    if timestamp_ms is not None:
                        timestamp = timestamp_ms / 1000.0  
                        break
            
            return TranscriptSegment(
                text=getattr(item, 'text', ''),
                timestamp=timestamp
            )
        else:
            item_str = str(item)
            text = ""
            timestamp = None
            
            if "text='" in item_str:
                text_start = item_str.find("text='") + 6
                text_end = item_str.find("',", text_start)
                if text_end != -1:
                    text = item_str[text_start:text_end]
                else:
                    text = item_str
            elif "text=\"" in item_str:
                text_start = item_str.find('text="') + 6
                text_end = item_str.find('",', text_start)
                if text_end != -1:
                    text = item_str[text_start:text_end]
                else:
                    text = item_str
            else:
                text = item_str
            
            timestamp_patterns = ["offset=", "start=", "time=", "timestamp=", "begin="]
            for pattern in timestamp_patterns:
                if pattern in item_str:
                    start_pos = item_str.find(pattern) + len(pattern)
                    start_end = item_str.find(",", start_pos)
                    if start_end == -1:
                        start_end = item_str.find(")", start_pos)
                    if start_end == -1:
                        start_end = item_str.find(" ", start_pos)
                    if start_end != -1:
                        try:
                            timestamp_ms = float(item_str[start_pos:start_end])
                            timestamp = timestamp_ms / 1000.0  
                            break
                        except ValueError:
                            continue
            
            return TranscriptSegment(
                text=text,
                timestamp=timestamp
            )
    
    def _process_transcript_content(self, content) -> str:
        """
        Process transcript content (handle both string and list formats)
        
        Args:
            content: The transcript content from supadata
            
        Returns:
            Processed transcript as string
        """
        result = self._process_transcript_content_with_timestamps(content)
        return result["text"]
    
    def save_transcript_to_file(self, transcript_text: str, video_id: str, directory: str = "transcripts") -> Optional[str]:
        """
        Save transcript to a file
        
        Args:
            transcript_text: The transcript content
            video_id: YouTube video ID
            directory: Directory to save the file
            
        Returns:
            Filepath if successful, None if failed
        """
        try:
            os.makedirs(directory, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{directory}/{video_id}_transcript_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            return filename
        except Exception as e:
            print(f"Failed to save transcript: {e}")
            return None 