import cv2
import os
from pathlib import Path

def extract_frames(video_path, output_dir, fps=25, quality=95):
    """
    Extract frames from video at specified FPS
    
    Args:
        video_path: Path to input video file
        output_dir: Directory to save extracted frames
        fps: Frames per second to extract (default: 25)
        quality: JPG quality 0-100 (default: 95)
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Open the video
    video = cv2.VideoCapture(video_path)
    
    if not video.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return
    
    # Get video properties
    original_fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / original_fps
    
    print(f"Video Properties:")
    print(f"  Original FPS: {original_fps:.2f}")
    print(f"  Total Frames: {total_frames}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Extracting at: {fps} FPS")
    print(f"  Output format: JPG (Quality: {quality}%)")
    
    # Calculate frame interval
    # If target fps >= original fps, extract all frames
    if fps >= original_fps:
        frame_interval = 1
        print(f"  Note: Target FPS ({fps}) >= Original FPS ({original_fps:.2f}), extracting all frames")
    else:
        frame_interval = int(original_fps / fps)
    
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = video.read()
        
        if not ret:
            break
        
        # Save frame at specified intervals
        if frame_count % frame_interval == 0:
            output_filename = output_path / f"frame_{saved_count:05d}.jpg"
            cv2.imwrite(str(output_filename), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            saved_count += 1
            
            if saved_count % 100 == 0:
                print(f"Extracted {saved_count} frames...")
        
        frame_count += 1
    
    video.release()
    
    print(f"\nExtraction complete!")
    print(f"Extracted {saved_count} frames to {output_path}")
    print(f"Expected frames at {fps} FPS: ~{int(duration * fps)}")

if __name__ == "__main__":
    video_file = r"D:\Projects\Projects\Code switching\kling_20260227_VIDEO_Take_Image_5653_0.mp4"
    output_directory = r"D:\Projects\Projects\Code switching\extracted_frames"
    
    extract_frames(video_file, output_directory, fps=25, quality=95)
