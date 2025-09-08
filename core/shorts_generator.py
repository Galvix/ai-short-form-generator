#!/usr/bin/env python3
"""
AI Short-Form Content Generator
Creates multiple 9:16 vertical shorts from a single long-form video.

Features:
- Intelligent content segmentation with GPT analysis
- Automatic 9:16 format conversion with smart cropping
- Multi-language subtitle generation (translate to English)
- AI-generated titles based on content
- Bulk export with organized file structure
"""

import os
import sys
import json
import time
import math
from typing import List, Dict, Tuple
from pathlib import Path

import whisper
import openai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.resize import resize
from moviepy.video.fx.crop import crop
from moviepy.video.tools.subtitles import SubtitlesClip
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

# Configure ImageMagick path for Windows
if os.name == 'nt':  # Windows
    imagemagick_paths = [
        r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe", 
        r"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe",
        r"C:\Program Files (x86)\ImageMagick-7.1.2-Q16-HDRI\magick.exe",
        r"C:\Program Files (x86)\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
    ]
    
    for path in imagemagick_paths:
        if os.path.exists(path):
            os.environ['IMAGEMAGICK_BINARY'] = path
            # Also try to configure MoviePy directly
            try:
                import moviepy.config as conf
                conf.change_settings({"IMAGEMAGICK_BINARY": path})
            except:
                pass
            print(f"🔧 ImageMagick configured: {path}")
            break

class AIShortFormGenerator:
    """AI-powered short-form content generator."""
    
    def __init__(self, api_key: str = None):
        """Initialize the generator."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.whisper_model = None
        self.openai_client = None
        
        if self.api_key:
            self.openai_client = openai.OpenAI(api_key=self.api_key)
            print("✓ OpenAI client initialized")
        else:
            print("⚠️ No OpenAI API key - GPT features disabled")
    
    def load_whisper_model(self, model_size: str = "base"):
        """Load Whisper model for transcription."""
        print(f"Loading Whisper model: {model_size}")
        self.whisper_model = whisper.load_model(model_size)
        print("✓ Whisper model loaded")
    
    def transcribe_video(self, video_path: str) -> Dict:
        """Transcribe video with word-level timestamps."""
        if not self.whisper_model:
            self.load_whisper_model()
        
        print("🎙️ Transcribing video...")
        start_time = time.time()
        
        result = self.whisper_model.transcribe(
            video_path,
            word_timestamps=True,
            verbose=False,
            fp16=False
        )
        
        elapsed = time.time() - start_time
        print(f"✓ Transcription completed in {elapsed:.1f}s")
        print(f"  - Language: {result.get('language', 'unknown')}")
        print(f"  - Segments: {len(result['segments'])}")
        
        return result
    
    def translate_to_english(self, text: str, source_language: str) -> str:
        """Translate text to English using GPT."""
        if not self.openai_client or source_language.lower() in ['en', 'english']:
            return text
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate the following {source_language} text to natural, fluent English. Maintain the meaning and tone. Only return the translation, no explanations."
                    },
                    {
                        "role": "user", 
                        "content": text
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def analyze_content_for_shorts(self, transcript: str, video_duration: float) -> List[Dict]:
        """Analyze content and identify the best segments with natural boundaries."""
        if not self.openai_client:
            # Fallback: create segments every 30-60 seconds
            return self._create_fallback_segments(video_duration)
        
        print("🤖 Analyzing content for intelligent segments with natural boundaries...")
        
        prompt = f"""
        Analyze this video transcript and identify the BEST segments for creating engaging short-form vertical videos.
        
        IMPORTANT: Extract segments with NATURAL START and END points based on content, not fixed durations.
        
        Video Duration: {video_duration/60:.1f} minutes
        Transcript: {transcript[:4000]}...

        For each segment, identify:
        1. NATURAL start point (when scene/topic/action begins)
        2. NATURAL end point (when scene/topic/action concludes)
        3. Duration should vary based on content (15-120 seconds)
        4. Complete scenes, fights, explanations, or story arcs
        5. Don't cut mid-action or mid-sentence

        Examples of natural boundaries:
        - Fight scene: Start when fighting begins → End when fight concludes
        - Explanation: Start with question/topic → End when point is made
        - Story: Start with setup → End with resolution/punchline
        - Action sequence: Start with buildup → End with conclusion

        Focus on:
        - Complete, self-contained content
        - Strong hooks that grab attention immediately
        - Natural conclusion points
        - Content that makes sense as standalone clips
        - Varying durations based on what the content needs

        Return JSON format:
        {{
            "segments": [
                {{
                    "start_time": 45.2,
                    "end_time": 98.7,
                    "duration": 53.5,
                    "topic": "Complete fight sequence",
                    "hook": "Epic battle from start to finish",
                    "title": "Ultimate Showdown",
                    "description": "Complete fight with natural beginning and ending",
                    "engagement_score": 9.2,
                    "content_type": "action",
                    "natural_boundary": "fight_complete"
                }}
            ]
        }}

        Aim for 3-7 high-quality segments with natural boundaries. Duration should vary (15-120s) based on content needs.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert video editor who creates engaging short-form content. Focus on natural content boundaries and complete scenes, not fixed durations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            analysis = json.loads(json_str)
            segments = analysis.get("segments", [])
            
            # Validate segments and ensure natural boundaries
            valid_segments = []
            for seg in segments:
                duration = seg.get('duration', seg['end_time'] - seg['start_time'])
                if 15 <= duration <= 120:  # Allow variable duration based on content
                    seg['duration'] = duration
                    valid_segments.append(seg)
            
            print(f"✓ Found {len(valid_segments)} intelligent segments with natural boundaries")
            for i, seg in enumerate(valid_segments, 1):
                print(f"  {i}. {seg['title']} ({seg['duration']:.1f}s) - {seg.get('content_type', 'general')}")
            
            return valid_segments
            
        except Exception as e:
            print(f"Error analyzing content: {e}")
            return self._create_fallback_segments(video_duration)
    
    def _create_fallback_segments(self, video_duration: float) -> List[Dict]:
        """Create fallback segments when GPT analysis fails."""
        segments = []
        segment_length = 45  # 45 second segments
        
        current_time = 0
        segment_num = 1
        
        while current_time + segment_length <= video_duration:
            segments.append({
                "start_time": current_time,
                "end_time": current_time + segment_length,
                "duration": segment_length,
                "topic": f"Segment {segment_num}",
                "hook": "Auto-generated segment",
                "title": f"Short Clip {segment_num}",
                "description": f"Automatically extracted segment {segment_num}",
                "engagement_score": 5.0
            })
            
            current_time += segment_length
            segment_num += 1
        
        return segments
    
    def convert_to_vertical_advanced(self, clip: VideoFileClip) -> VideoFileClip:
        """Convert video clip to 9:16 vertical format with dynamic cropping and keyframes."""
        original_width, original_height = clip.size
        target_width = 1080
        target_height = 1920
        target_ratio = target_height / target_width  # 16:9 = 1.777...
        
        print(f"   Original: {original_width}x{original_height}")
        print(f"   Target: {target_width}x{target_height}")
        
        # Calculate crop dimensions to maintain aspect ratio
        if original_height / original_width > target_ratio:
            # Video is too tall, crop height
            crop_width = original_width
            crop_height = int(original_width * target_ratio)
        else:
            # Video is too wide, crop width  
            crop_height = original_height
            crop_width = int(original_height / target_ratio)
        
        print(f"   Crop size: {crop_width}x{crop_height}")
        
        # Define keyframe positions for dynamic cropping
        # This creates a subtle movement effect to keep content engaging
        def dynamic_crop_position(t):
            """Calculate crop position based on time for dynamic effect."""
            duration = clip.duration
            
            # Create subtle movement patterns
            if duration <= 30:
                # Short clips: gentle side-to-side
                x_offset = 20 * math.sin(t * 0.5)
                y_offset = 10 * math.sin(t * 0.3)
            elif duration <= 60:
                # Medium clips: slow zoom with movement
                zoom_factor = 1 + 0.02 * math.sin(t * 0.2)
                x_offset = 15 * math.sin(t * 0.4) * zoom_factor
                y_offset = 8 * math.sin(t * 0.25) * zoom_factor
            else:
                # Long clips: complex movement pattern
                x_offset = 25 * (math.sin(t * 0.3) + 0.5 * math.sin(t * 0.7))
                y_offset = 15 * (math.cos(t * 0.2) + 0.3 * math.cos(t * 0.6))
            
            # Calculate center position with dynamic offset
            center_x = original_width / 2 + x_offset
            center_y = original_height / 2 + y_offset
            
            # Ensure crop stays within bounds
            x1 = max(0, min(center_x - crop_width / 2, original_width - crop_width))
            y1 = max(0, min(center_y - crop_height / 2, original_height - crop_height))
            
            return (x1, y1, x1 + crop_width, y1 + crop_height)
        
        # Apply dynamic cropping with keyframes
        print("   🎬 Applying dynamic cropping with keyframes...")
        
        def crop_function(get_frame, t):
            """Apply crop at specific time t."""
            x1, y1, x2, y2 = dynamic_crop_position(t)
            frame = get_frame(t)
            return frame[int(y1):int(y2), int(x1):int(x2)]
        
        # Create dynamically cropped clip
        cropped_clip = clip.fl(crop_function, apply_to=['mask'])
        
        # Resize to exact target dimensions
        print("   📱 Resizing to 9:16 format...")
        final_clip = cropped_clip.fx(resize, newsize=(target_width, target_height))
        
        return final_clip
    
    def convert_to_vertical(self, clip: VideoFileClip) -> VideoFileClip:
        """Convert video clip to 9:16 vertical format with smart cropping (fallback method)."""
        original_width, original_height = clip.size
        target_ratio = 9/16  # Height/Width for vertical
        
        # Calculate target dimensions
        if original_height / original_width > target_ratio:
            # Video is too tall, crop height
            new_width = original_width
            new_height = int(original_width * target_ratio)
        else:
            # Video is too wide, crop width  
            new_height = original_height
            new_width = int(original_height / target_ratio)
        
        # Center crop
        x_center = original_width / 2
        y_center = original_height / 2
        
        x1 = x_center - new_width / 2
        y1 = y_center - new_height / 2
        
        # Apply crop effect
        cropped = clip.fx(crop, x1=x1, y1=y1, x2=x1+new_width, y2=y1+new_height)
        
        # Resize to standard 9:16 resolution (1080x1920)
        resized = cropped.fx(resize, newsize=(1080, 1920))
        
        return resized
    
    def create_subtitles(self, transcript_segments: List[Dict], 
                        video_duration: float, source_language: str) -> List[Tuple[float, float, str]]:
        """Create subtitle data with translations."""
        subtitles = []
        
        for segment in transcript_segments:
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            
            if text and start_time < video_duration:
                # Translate if needed
                if source_language.lower() not in ['en', 'english']:
                    english_text = self.translate_to_english(text, source_language)
                else:
                    english_text = text
                
                subtitles.append((start_time, end_time, english_text))
        
        return subtitles
    
    def create_subtitle_overlay(self, frame, text, video_width, video_height):
        """Create subtitle overlay using OpenCV (no ImageMagick needed)."""
        try:
            # Convert frame to work with OpenCV
            if isinstance(frame, np.ndarray):
                img = frame.copy()
            else:
                img = np.array(frame)
            
            # Text styling
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = min(video_width, video_height) / 800  # Scale font to video size
            font_thickness = max(2, int(font_scale * 2))
            text_color = (255, 255, 255)  # White
            outline_color = (0, 0, 0)  # Black outline
            
            # Handle long text by wrapping
            words = text.split()
            lines = []
            current_line = ""
            max_chars_per_line = max(20, video_width // 30)
            
            for word in words:
                if len(current_line + " " + word) <= max_chars_per_line:
                    current_line += (" " + word) if current_line else word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Calculate position (bottom center)
            line_height = int(40 * font_scale)
            total_text_height = len(lines) * line_height
            start_y = video_height - total_text_height - 50  # 50px from bottom
            
            # Draw each line
            for i, line in enumerate(lines):
                # Get text size
                (text_width, text_height), _ = cv2.getTextSize(line, font, font_scale, font_thickness)
                
                # Center the text
                x = (video_width - text_width) // 2
                y = start_y + (i * line_height) + text_height
                
                # Draw outline (black)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx != 0 or dy != 0:
                            cv2.putText(img, line, (x + dx, y + dy), font, font_scale, 
                                      outline_color, font_thickness + 1, cv2.LINE_AA)
                
                # Draw main text (white)
                cv2.putText(img, line, (x, y), font, font_scale, text_color, 
                          font_thickness, cv2.LINE_AA)
            
            return img
            
        except Exception as e:
            print(f"   Warning: Subtitle overlay failed: {e}")
            return frame
    
    def add_subtitles_to_video_opencv(self, video_clip: VideoFileClip, 
                                     subtitles: List[Tuple[float, float, str]]) -> VideoFileClip:
        """Add subtitles using OpenCV (ImageMagick-free method)."""
        if not subtitles:
            return video_clip
        
        print(f"   📝 Adding {len(subtitles)} subtitles using OpenCV...")
        
        try:
            def make_frame_with_subtitles(get_frame, t):
                """Create frame with subtitles at time t."""
                # Get original frame
                frame = get_frame(t)
                
                # Find active subtitle at time t
                current_text = ""
                for start_time, end_time, text in subtitles:
                    if start_time <= t <= end_time:
                        current_text = text.strip()
                        break
                
                # Add subtitle if there's text
                if current_text:
                    frame = self.create_subtitle_overlay(
                        frame, current_text, 
                        video_clip.w, video_clip.h
                    )
                
                return frame
            
            # Create new video clip with subtitles
            subtitled_clip = video_clip.fl(make_frame_with_subtitles)
            print(f"   ✅ OpenCV subtitles added successfully!")
            return subtitled_clip
            
        except Exception as e:
            print(f"   ❌ OpenCV subtitle creation failed: {e}")
            return video_clip

    def add_subtitles_to_video(self, video_clip: VideoFileClip, 
                              subtitles: List[Tuple[float, float, str]]) -> VideoFileClip:
        """Add subtitles to video clip with multiple methods."""
        if not subtitles:
            return video_clip
            
        print(f"   📝 Adding {len(subtitles)} subtitles...")
        
        # Method 1: Try OpenCV method first (more reliable)
        try:
            return self.add_subtitles_to_video_opencv(video_clip, subtitles)
        except Exception as e:
            print(f"   ⚠️ OpenCV method failed: {e}")
        
        # Method 2: Try ImageMagick method as fallback
        try:
            print("   🔄 Trying ImageMagick method...")
            test_clip = TextClip("Test", fontsize=24, color='white')
            test_clip.close()
            
            subtitle_clips = []
            for start_time, end_time, text in subtitles:
                if start_time >= video_clip.duration:
                    continue
                end_time = min(end_time, video_clip.duration)
                
                txt_clip = TextClip(
                    text, fontsize=50, color='white', font='Arial-Bold',
                    stroke_color='black', stroke_width=2
                ).set_start(start_time).set_end(end_time).set_position(('center', 'bottom'))
                
                subtitle_clips.append(txt_clip)
            
            if subtitle_clips:
                return CompositeVideoClip([video_clip] + subtitle_clips)
            
        except Exception as e:
            print(f"   ⚠️ ImageMagick method also failed: {e}")
        
        # Method 3: Return video without subtitles
        print(f"   ⚠️ Creating video without subtitles")
        return video_clip
    
    def generate_shorts(self, input_video: str, output_dir: str = "shorts_output", max_shorts: int = None) -> Dict:
        """Main function to generate short-form content."""
        print("=== AI Short-Form Content Generator ===")
        start_time = time.time()
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            "success": False,
            "shorts_created": 0,
            "output_files": [],
            "errors": []
        }
        
        try:
            # Load video
            print(f"📹 Loading video: {input_video}")
            with VideoFileClip(input_video) as original_clip:
                video_duration = original_clip.duration
                print(f"   Duration: {video_duration/60:.1f} minutes")
            
            # Transcribe video
            transcript_result = self.transcribe_video(input_video)
            source_language = transcript_result.get('language', 'en')
            
            # Save full transcript
            transcript_path = os.path.join(output_dir, "full_transcript.txt")
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript_result['text'])
            
            # Analyze content for shorts
            segments = self.analyze_content_for_shorts(transcript_result['text'], video_duration)
            
            if not segments:
                results["errors"].append("No suitable segments found for shorts")
                return results
            
            # Limit segments based on max_shorts parameter
            if max_shorts and max_shorts > 0:
                segments = segments[:max_shorts]
                print(f"   🎯 Limited to {len(segments)} shorts (max_shorts={max_shorts})")
            
            # Create subtitles data
            subtitles_data = self.create_subtitles(
                transcript_result['segments'], 
                video_duration, 
                source_language
            )
            
            # Generate each short
            print(f"\n🎬 Creating {len(segments)} shorts...")
            
            for i, segment in enumerate(segments, 1):
                try:
                    print(f"\n--- Short {i}/{len(segments)}: {segment['title']} ---")
                    
                    start_time = segment['start_time']
                    end_time = segment['end_time']
                    title = segment['title']
                    
                    print(f"   Time: {start_time:.1f}s - {end_time:.1f}s ({end_time-start_time:.1f}s)")
                    
                    # Extract video segment
                    print("🎞️ Extracting video segment...")
                    with VideoFileClip(input_video) as full_clip:
                        segment_clip = full_clip.subclip(start_time, end_time)
                        
                        # Convert to 9:16 vertical with advanced dynamic cropping
                        print("📱 Converting to 9:16 format with dynamic keyframes...")
                        try:
                            vertical_clip = self.convert_to_vertical_advanced(segment_clip)
                        except Exception as crop_error:
                            print(f"   ⚠️ Advanced cropping failed, using fallback: {crop_error}")
                            vertical_clip = self.convert_to_vertical(segment_clip)
                        
                        # Filter subtitles for this segment
                        segment_subtitles = [
                            (s_start - start_time, s_end - start_time, text)
                            for s_start, s_end, text in subtitles_data
                            if s_start >= start_time and s_end <= end_time
                        ]
                        
                        # Add subtitles
                        if segment_subtitles:
                            print(f"📝 Adding {len(segment_subtitles)} subtitles...")
                            final_clip = self.add_subtitles_to_video(vertical_clip, segment_subtitles)
                        else:
                            print("📝 No subtitles for this segment")
                            final_clip = vertical_clip
                        
                        # Generate safe filename
                        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_title = safe_title[:50]  # Limit length
                        filename = f"short_{i:02d}_{safe_title}.mp4"
                        output_path = os.path.join(output_dir, filename)
                        
                        print(f"💾 Exporting to: {filename}")
                        print(f"   Full path: {output_path}")
                        
                        # Check if we can write to the path
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        
                        # Export with better error handling
                        try:
                            final_clip.write_videofile(
                                output_path,
                                codec='libx264',
                                audio_codec='aac',
                                temp_audiofile='temp-audio.m4a',
                                remove_temp=True,
                                verbose=False,
                                logger=None
                            )
                            print(f"✓ Export successful!")
                        except Exception as export_error:
                            print(f"❌ Export failed: {export_error}")
                            print("🔄 Retrying with simpler settings...")
                            final_clip.write_videofile(
                                output_path,
                                verbose=False,
                                logger=None
                            )
                            print(f"✓ Export successful (retry)!")
                        
                        # Clean up
                        final_clip.close()
                        vertical_clip.close()
                        segment_clip.close()
                        
                        # Verify file was created
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                            results["output_files"].append({
                                "filename": filename,
                                "path": output_path,
                                "title": title,
                                "duration": segment['duration'],
                                "topic": segment['topic']
                            })
                            print(f"✅ Short {i} completed: {filename} ({file_size:.1f}MB)")
                        else:
                            raise Exception(f"Output file was not created or is empty: {output_path}")
                        
                except Exception as e:
                    error_msg = f"Error creating short {i}: {str(e)}"
                    print(f"❌ {error_msg}")
                    print(f"   Segment: {segment.get('title', 'Unknown')}")
                    import traceback
                    traceback.print_exc()
                    results["errors"].append(error_msg)
                    continue
            
            results["success"] = True
            results["shorts_created"] = len(results["output_files"])
            
            elapsed = time.time() - start_time
            print(f"\n🎉 Generation complete!")
            print(f"   Created: {results['shorts_created']} shorts")
            print(f"   Time: {elapsed/60:.1f} minutes")
            print(f"   Output: {output_dir}")
            
            return results
            
        except Exception as e:
            error_msg = f"Fatal error: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results

def main():
    """CLI interface for shorts generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Short-Form Content Generator")
    parser.add_argument("input", help="Input video file")
    parser.add_argument("-o", "--output", default="shorts_output", help="Output directory")
    parser.add_argument("--no-gpt", action="store_true", help="Disable GPT analysis")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return
    
    # Initialize generator
    api_key = None if args.no_gpt else os.getenv("OPENAI_API_KEY")
    generator = AIShortFormGenerator(api_key)
    
    # Generate shorts
    results = generator.generate_shorts(args.input, args.output)
    
    if results["success"]:
        print(f"\n✅ Successfully created {results['shorts_created']} shorts!")
        for output_file in results["output_files"]:
            print(f"   📱 {output_file['filename']} - {output_file['title']}")
    else:
        print(f"\n❌ Generation failed!")
        for error in results["errors"]:
            print(f"   Error: {error}")

if __name__ == "__main__":
    main()
