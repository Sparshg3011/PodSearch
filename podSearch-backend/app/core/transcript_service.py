from typing import Optional, List
import os
import json
import subprocess
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from ..models.youtube import TranscriptSegment
from ..models.transcript_db import TranscriptSegmentDB


load_dotenv()

try:
    from supadata import Supadata, SupadataError
    SUPADATA_AVAILABLE = True
except ImportError:
    SUPADATA_AVAILABLE = False

# Check if yt-dlp is available
try:
    subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    YT_DLP_AVAILABLE = True
except (subprocess.CalledProcessError, FileNotFoundError):
    YT_DLP_AVAILABLE = False

class TranscriptService:
    """Service for extracting YouTube transcripts using multiple fallback methods"""
    
    def __init__(self):
        if SUPADATA_AVAILABLE:
            api_key = os.getenv("SUPADATA_API_KEY")
            if api_key:
                self.client = Supadata(api_key=api_key)
            else:
                self.client = None
                print("Warning: SUPADATA_API_KEY not found, will use fallback methods")
        else:
            self.client = None
    
    def extract_transcript(self, video_id: str, language: str = "en") -> dict:
        """
        Extract transcript for a given video ID using multiple fallback methods
        
        Args:
            video_id: YouTube video ID
            language: Language code (default: "en")
            
        Returns:
            dict with transcript data and metadata
        """
        # Try Supadata first if available
        if SUPADATA_AVAILABLE and self.client:
            try:
                result = self._extract_with_supadata(video_id, language)
                if result["success"]:
                    return result
                else:
                    print(f"Supadata failed: {result['error']}. Trying fallback methods...")
            except Exception as e:
                print(f"Supadata error: {str(e)}. Trying fallback methods...")
        
        # Fallback to yt-dlp if Supadata fails or is unavailable
        if YT_DLP_AVAILABLE:
            try:
                result = self._extract_with_ytdlp(video_id, language)
                if result["success"]:
                    return result
                else:
                    print(f"yt-dlp failed: {result['error']}")
            except Exception as e:
                print(f"yt-dlp error: {str(e)}")
        
        # If all methods fail
        return {
            "success": False,
            "error": "All transcript extraction methods failed. Supadata limit exceeded and yt-dlp not available or failed.",
            "transcript": None,
            "segments": [],
            "metadata": {"video_id": video_id, "language": language}
        }

    def _extract_with_supadata(self, video_id: str, language: str = "en") -> dict:
        """Extract transcript using Supadata API"""
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

    def _extract_with_ytdlp(self, video_id: str, language: str = "en") -> dict:
        """Extract transcript using yt-dlp as fallback"""
        try:
            # Use yt-dlp to extract transcript
            cmd = [
                'yt-dlp',
                f'https://www.youtube.com/watch?v={video_id}',
                '--write-auto-sub',
                '--write-sub',
                '--sub-langs', f'{language},en',
                '--skip-download',
                '--sub-format', 'json3',
                '--output', f'%(id)s.%(ext)s'
            ]
            
            # Use temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Change to temp directory
                old_cwd = os.getcwd()
                os.chdir(temp_dir)
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    # Look for subtitle files
                    subtitle_files = []
                    for file in os.listdir('.'):
                        if file.startswith(video_id) and ('.json3' in file or '.vtt' in file):
                            subtitle_files.append(file)
                    
                    if not subtitle_files:
                        return {
                            "success": False,
                            "error": "No subtitle files found",
                            "transcript": None,
                            "segments": [],
                            "metadata": {"video_id": video_id, "language": language}
                        }
                    
                    # Try to parse JSON3 format first
                    for subtitle_file in subtitle_files:
                        if '.json3' in subtitle_file:
                            try:
                                with open(subtitle_file, 'r', encoding='utf-8') as f:
                                    subtitle_data = json.load(f)
                                
                                segments = self._parse_json3_subtitles(subtitle_data)
                                if segments:
                                    text_content = " ".join([seg.text for seg in segments])
                                    
                                    return {
                                        "success": True,
                                        "error": None,
                                        "transcript": text_content,
                                        "segments": segments,
                                        "metadata": {
                                            "video_id": video_id,
                                            "language": language,
                                            "length": len(text_content),
                                            "segment_count": len(segments),
                                            "timestamp": datetime.now().isoformat(),
                                            "source": "yt-dlp"
                                        }
                                    }
                            except Exception as e:
                                print(f"Error parsing JSON3 subtitle file: {e}")
                                continue
                    
                    # If JSON3 parsing failed, try VTT format
                    for subtitle_file in subtitle_files:
                        if '.vtt' in subtitle_file:
                            try:
                                with open(subtitle_file, 'r', encoding='utf-8') as f:
                                    vtt_content = f.read()
                                
                                segments = self._parse_vtt_subtitles(vtt_content)
                                if segments:
                                    text_content = " ".join([seg.text for seg in segments])
                                    
                                    return {
                                        "success": True,
                                        "error": None,
                                        "transcript": text_content,
                                        "segments": segments,
                                        "metadata": {
                                            "video_id": video_id,
                                            "language": language,
                                            "length": len(text_content),
                                            "segment_count": len(segments),
                                            "timestamp": datetime.now().isoformat(),
                                            "source": "yt-dlp"
                                        }
                                    }
                            except Exception as e:
                                print(f"Error parsing VTT subtitle file: {e}")
                                continue
                    
                    return {
                        "success": False,
                        "error": "Could not parse any subtitle files",
                        "transcript": None,
                        "segments": [],
                        "metadata": {"video_id": video_id, "language": language}
                    }
                    
                finally:
                    os.chdir(old_cwd)
                    
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "yt-dlp operation timed out",
                "transcript": None,
                "segments": [],
                "metadata": {"video_id": video_id, "language": language}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"yt-dlp error: {str(e)}",
                "transcript": None,
                "segments": [],
                "metadata": {"video_id": video_id, "language": language}
            }

    def _parse_json3_subtitles(self, subtitle_data) -> List[TranscriptSegment]:
        """Parse JSON3 subtitle format from yt-dlp"""
        segments = []
        
        try:
            if 'events' in subtitle_data:
                for event in subtitle_data['events']:
                    if 'segs' in event and event.get('tStartMs') is not None:
                        text_parts = []
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                text_parts.append(seg['utf8'])
                        
                        if text_parts:
                            text = ''.join(text_parts).strip()
                            if text and text not in ['\n', ' ', '']:
                                timestamp = event['tStartMs'] / 1000.0
                                segments.append(TranscriptSegment(
                                    text=text,
                                    timestamp=timestamp
                                ))
        except Exception as e:
            print(f"Error parsing JSON3 format: {e}")
        
        return segments

    def _parse_vtt_subtitles(self, vtt_content: str) -> List[TranscriptSegment]:
        """Parse VTT subtitle format"""
        segments = []
        
        try:
            lines = vtt_content.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Look for timestamp lines (format: 00:00:01.000 --> 00:00:04.000)
                if '-->' in line:
                    timestamp_parts = line.split(' --> ')
                    if len(timestamp_parts) == 2:
                        start_time = self._parse_vtt_timestamp(timestamp_parts[0])
                        
                        # Get the text (next non-empty lines until empty line or next timestamp)
                        i += 1
                        text_parts = []
                        while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                            text_line = lines[i].strip()
                            # Remove VTT formatting tags
                            text_line = self._clean_vtt_text(text_line)
                            if text_line:
                                text_parts.append(text_line)
                            i += 1
                        
                        if text_parts:
                            text = ' '.join(text_parts)
                            if text:
                                segments.append(TranscriptSegment(
                                    text=text,
                                    timestamp=start_time
                                ))
                        continue
                
                i += 1
                
        except Exception as e:
            print(f"Error parsing VTT format: {e}")
        
        return segments

    def _parse_vtt_timestamp(self, timestamp_str: str) -> float:
        """Parse VTT timestamp to seconds"""
        try:
            # Format: 00:00:01.000 or 01.000
            timestamp_str = timestamp_str.strip()
            
            if ':' in timestamp_str:
                parts = timestamp_str.split(':')
                if len(parts) == 3:  # HH:MM:SS.mmm
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:  # MM:SS.mmm
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            else:
                # Just seconds
                return float(timestamp_str)
        except:
            return 0.0

    def _clean_vtt_text(self, text: str) -> str:
        """Remove VTT formatting tags from text"""
        import re
        # Remove VTT tags like <c.colorE5E5E5>, </c>, etc.
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

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
    
    def save_transcript_to_file(self, transcript_data, video_id: str, directory: str = "transcripts") -> Optional[str]:
        """
        Save transcript with timestamps to a file
        
        Args:
            transcript_data: Either a TranscriptWithTimestampsResponse object or plain text string
            video_id: YouTube video ID
            directory: Directory to save the file
            
        Returns:
            Filepath if successful, None if failed
        """
        try:
            os.makedirs(directory, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{directory}/{video_id}_transcript_with_timestamps_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                if hasattr(transcript_data, 'segments') and hasattr(transcript_data, 'video_id'):
                    f.write(f"Transcript for Video ID: {transcript_data.video_id}\n")
                    f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for segment in transcript_data.segments:
                        if segment.timestamp is not None:
                            minutes = int(segment.timestamp // 60)
                            seconds = int(segment.timestamp % 60)
                            if minutes >= 60:
                                hours = minutes // 60
                                minutes = minutes % 60
                                timestamp_str = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                            else:
                                timestamp_str = f"[{minutes:02d}:{seconds:02d}]"
                            f.write(f"{timestamp_str} {segment.text}\n")
                        else:
                            f.write(f"[--:--] {segment.text}\n")
                else:
                    f.write(str(transcript_data))
            
            return filename
        except Exception as e:
            print(f"Failed to save transcript: {e}")
            return None
    
    async def save_transcript_to_db(self, video_id: str, segments: List[TranscriptSegment]) -> dict:
        """
        Save video ID and transcript segments to MongoDB
        
        Args:
            video_id: YouTube video ID
            segments: List of transcript segments with timestamps
            
        Returns:
            Dictionary with save results
        """
        try:
            await TranscriptSegmentDB.find(
                TranscriptSegmentDB.video_id == video_id
            ).delete()
            
            segment_docs = []
            for i, segment in enumerate(segments):
                segment_doc = TranscriptSegmentDB(
                    video_id=video_id,
                    sequence=i,
                    text=segment.text,
                    timestamp=segment.timestamp
                )
                segment_docs.append(segment_doc)
            
            if segment_docs:
                await TranscriptSegmentDB.insert_many(segment_docs)
            
            return {
                "success": True,
                "video_id": video_id,
                "segments_saved": len(segment_docs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save transcript to database: {str(e)}"
            }
    
    async def get_transcript_from_db(self, video_id: str) -> Optional[List[dict]]:
        """
        Get transcript segments from MongoDB by video ID
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of transcript segments or None
        """
        try:
            segments = await TranscriptSegmentDB.find(
                TranscriptSegmentDB.video_id == video_id
            ).sort(TranscriptSegmentDB.sequence).to_list()
            
            if not segments:
                return None
            
            return [
                {
                    "sequence": segment.sequence,
                    "text": segment.text,
                    "timestamp": segment.timestamp,
                    "created_at": segment.created_at
                }
                for segment in segments
            ]
            
        except Exception as e:
            return None
    
    # async def search_transcripts_in_db(self, query: str, limit: int = 10) -> List[dict]:
    #     """
    #     Search transcript segments by text content
        
    #     Args:
    #         query: Search query
    #         limit: Maximum results to return
            
    #     Returns:
    #         List of matching transcript segments
    #     """
    #     try:
    #         segments = await TranscriptSegmentDB.find({
    #             "text": {"$regex": query, "$options": "i"}
    #         }).limit(limit).to_list()
            
    #         return [
    #             {
    #                 "video_id": segment.video_id,
    #                 "sequence": segment.sequence,
    #                 "text": segment.text,
    #                 "timestamp": segment.timestamp,
    #                 "created_at": segment.created_at
    #             }
    #             for segment in segments
    #         ]
            
    #     except Exception as e:
    #         return [] 