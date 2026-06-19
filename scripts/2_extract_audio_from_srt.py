import os
import csv
import subprocess
import pysrt
import sys
import gc
import time
from pydub import AudioSegment

# Force UTF-8 for stdout/stderr on Windows to avoid encoding errors with Nepali/Unicode
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

CSV_MAPPING = r"D:\Projects\Projects\Code switching\nepali_subtitles_mapping.csv"
SRT_DIR = r"D:\Projects\Projects\Code switching\nepali_subtitles (1)"
OUTPUT_DIR = r"D:\Projects\Projects\Code switching\whisper_dataset"
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio_segments")
METADATA_PATH = os.path.join(OUTPUT_DIR, "metadata.csv")

os.makedirs(AUDIO_DIR, exist_ok=True)

# Define segmentation duration threshold in milliseconds
MAX_DURATION_MS = 10000 

def download_audio(yt_link, tmp_filename):
    print(f"Downloading audio from {yt_link}...")
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--output", tmp_filename,
        "--force-overwrites",
        "--quiet",
        "--no-warnings",
        yt_link
    ]
    res = subprocess.run(cmd)
    if res.returncode == 0 and os.path.exists(tmp_filename):
        return True
    return False

def clean_text(text):
    # Remove '>>' speaker markers
    text = text.replace('>>', '')
    # Normalize whitespace
    return " ".join(text.replace('\n', ' ').split())

def main():
    # Load mapping
    mapping = []
    with open(CSV_MAPPING, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping.append(row)
            
    print(f"Loaded {len(mapping)} videos from mapping.")
    
    # Prepare metadata CSV
    metadata_exists = os.path.exists(METADATA_PATH)
    with open(METADATA_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not metadata_exists:
            writer.writerow(["path", "transcription"])
            
        for i, row in enumerate(mapping):
            srt_filename = row['srtfile']
            yt_link = row['ytlink']
            srt_path = os.path.join(SRT_DIR, srt_filename)
            
            if not os.path.exists(srt_path):
                print(f"Skip (SRT not found): {srt_filename}")
                continue
                
            base_name = srt_filename.replace(".srt", "")
            
            # Skip if already processed (check if first chunk exists)
            first_chunk_path = os.path.join(AUDIO_DIR, f"{base_name}.ne1.wav")
            if os.path.exists(first_chunk_path):
                print(f"Already processed: {base_name}. Skipping...")
                continue
                
            # Temporary full audio file
            tmp_audio_path = os.path.join(OUTPUT_DIR, f"tmp_download_{i}.wav")
            if os.path.exists(tmp_audio_path):
                try:
                    os.remove(tmp_audio_path)
                except:
                    pass
            
            print(f"Processing ({i+1}/{len(mapping)}): {base_name}")
            if not download_audio(yt_link, tmp_audio_path):
                print(f" Failed to download audio for {yt_link}")
                continue
                
            try:
                # Load full audio
                audio = AudioSegment.from_wav(tmp_audio_path)
                
                # Load subtitles
                subs = pysrt.open(srt_path, encoding='utf-8')
                if not subs:
                    os.remove(tmp_audio_path)
                    continue
                
                # SEQUENTIALIZE: Resolve overlapping timestamps (rolling subs)
                # Set previous sub end to current sub start if it overlaps
                for s_idx in range(len(subs) - 1):
                    if subs[s_idx].end.ordinal > subs[s_idx+1].start.ordinal:
                        subs[s_idx].end = subs[s_idx+1].start

                current_group = []
                group_start_ms = 0
                chunk_index = 1
                
                for j, sub in enumerate(subs):
                    sub_start = sub.start.ordinal
                    sub_end = sub.end.ordinal
                    
                    if not current_group:
                        current_group = [sub]
                        group_start_ms = sub_start
                    else:
                        current_group.append(sub)
                        
                    group_duration = sub_end - group_start_ms
                    
                    # If duration exceeds 10s or it's the last subtitle, chunk it
                    if group_duration >= MAX_DURATION_MS or j == len(subs) - 1:
                        if current_group:
                            # Trim audio strictly using the current group's bounds
                            start_trim = current_group[0].start.ordinal
                            end_trim = current_group[-1].end.ordinal
                            
                            if end_trim > start_trim:
                                chunk_audio = audio[start_trim:end_trim]
                                text = " ".join([clean_text(s.text) for s in current_group])
                                
                                if text.strip() != "":
                                    chunk_filename = f"{base_name}.ne{chunk_index}.wav"
                                    chunk_path = os.path.join(AUDIO_DIR, chunk_filename)
                                    
                                    chunk_audio.export(chunk_path, format="wav")
                                    writer.writerow([chunk_filename, text])
                                    f.flush()
                                    print(f"  Exported chunk {chunk_index}")
                                    chunk_index += 1
                                
                        current_group = []
                    
                
                
            except Exception as e:
                print(f"Error processing {base_name}: {e}")
            finally:
                # Explicitly close and delete objects to release file handles
                if 'audio' in locals(): del audio
                if 'subs' in locals(): del subs
                gc.collect()
                time.sleep(1) # Small delay to ensure file system catch up
                
            if os.path.exists(tmp_audio_path):
                try:
                    os.remove(tmp_audio_path)
                except:
                    pass

if __name__ == "__main__":
    main()
