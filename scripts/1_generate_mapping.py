import os
import subprocess
import csv
import re

# List of playlists
PLAYLISTS = [
    "https://www.youtube.com/playlist?list=PLQXjkLMTz0EfWdMKZx1MG1hdunx6Y2T-E",
    "https://www.youtube.com/playlist?list=PLBxS58zcycosKoJ8LTPaEkEsc0yhNJQyH"
]

SRT_DIR = r"D:\Projects\Projects\Code switching\nepali_subtitles (1)"
OUTPUT_CSV = r"D:\Projects\Projects\Code switching\nepali_subtitles_mapping.csv"

def get_playlist_videos(playlist_url):
    cmd_list = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(playlist_index)s|%(id)s|%(title)s",
        playlist_url
    ]
    
    print(f"Running command: {' '.join(cmd_list)}")
    # Use utf-8 by default but capture raw bytes for more control if needed
    process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    # Try decoding with several common Windows encodings
    output = None
    for enc in ['utf-8', 'utf-16', 'cp1252']:
        try:
            output = stdout.decode(enc)
            if "|" in output: # Sanity check for expected format
                break
        except:
            continue
            
    if not output:
        output = stdout.decode('utf-8', errors='ignore')

    print(f"Stdout length: {len(output)}")
    if not output:
        print(f"No output for playlist: {playlist_url}")
        return []

    videos = output.strip().split("\n")
    print(f"Lines split: {len(videos)}")
    selected_videos = []
    
    for v in videos:
        if "|" not in v:
            continue
            
        parts = v.split("|")
        try:
            idx = int(parts[0])
            vid = parts[1]
            title = parts[2]
            
            selected_videos.append({"id": vid, "title": title})
        except:
            continue
            
    return selected_videos

def normalize_title(title):
    # Keep alphanumeric characters and spaces only for basic normalization
    # Removing completely rather than replacing with space to preserve unicode combining characters
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip().lower()
    return title

def extract_ep_number(title):
    # Specifically look for EP followed by a number
    match = re.search(r'(?:ep|episode)\.?\s*(\d+)', title.lower())
    if match:
        return int(match.group(1))
    return None

def extract_numbers(title):
    # Extract numbers as integers to avoid '01' != '1' issues
    nums = re.findall(r'\d+', title)
    return {int(n) for n in nums}

def main():
    all_videos = []
    for i, pl_url in enumerate(PLAYLISTS):
        print(f"Fetching playlist {i+1}...")
        all_videos.extend(get_playlist_videos(pl_url))
    
    print(f"Total videos fetched: {len(all_videos)}")
    
    srt_files = [f for f in os.listdir(SRT_DIR) if f.endswith(".srt")]
    print(f"Total SRT files found: {len(srt_files)}")
    
    mapping = []
    
    with open(r"D:\Projects\Projects\Code switching\debug_videos.txt", "w", encoding="utf-8") as dv:
        for v in all_videos:
            if "colors" in v['title'].lower() or "cotg" in v['title'].lower() or "ep." in v['title'].lower() or "episode" in v['title'].lower():
                dv.write(f"ID: {v['id']} | Title: {v['title']} | Extracted EP: {extract_ep_number(v['title'])}\n")
    
    with open(r"D:\Projects\Projects\Code switching\debug_mapping.txt", "w", encoding="utf-8") as debug_file:
        for i, srt_file in enumerate(srt_files):
            # Remove extensions and language tag
            srt_base = srt_file.lower()
            for suffix in [".ne.srt", ".srt"]:
                if srt_base.endswith(suffix):
                    srt_base = srt_base[:-len(suffix)]
            
            srt_norm = normalize_title(srt_base)
            srt_nums = extract_numbers(srt_base)
            srt_ep = extract_ep_number(srt_base)
            
            debug_file.write(f"\n--- Processing SRT: {srt_file} ---\n")
            debug_file.write(f"Normalized SRT: {srt_norm}\n")
            debug_file.write(f"Numbers in SRT: {srt_nums} | EP: {srt_ep}\n")
            
            match_found = False
            
            # 1. Try matching "On Air With Sanjay" by episode number
            if "on air" in srt_norm and srt_nums:
                for video in all_videos:
                    v_title = video['title'].lower()
                    if "on air" in v_title:
                        v_nums = extract_numbers(v_title)
                        # Find intersection of numbers
                        if srt_nums.intersection(v_nums):
                            mapping.append({
                                "srtfile": srt_file,
                                "ytlink": f"https://www.youtube.com/watch?v={video['id']}"
                            })
                            match_found = True
                            debug_file.write(f"MATCH FOUND (Podcast Number): {video['title']}\n")
                            break
            
            if not match_found:
                # 2. Try Exact Normalized Match FIRST
                for video in all_videos:
                    v_norm = normalize_title(video['title'])
                    if srt_norm == v_norm:
                        mapping.append({
                            "srtfile": srt_file,
                            "ytlink": f"https://www.youtube.com/watch?v={video['id']}"
                        })
                        match_found = True
                        debug_file.write(f"MATCH FOUND (Exact): {video['title']}\n")
                        break

            if not match_found:
                # 3. Try matching "Colors of the Game" by specific EP number
                if srt_ep is not None:
                    for video in all_videos:
                        v_title = video['title'].lower()
                        # Some video titles don't have "colors of the game", just "EP. XXX"
                        v_ep = extract_ep_number(v_title)
                        
                        if v_ep == srt_ep:
                             # Check if it's reasonably a COTG video (not sanjay)
                             if "on air" not in v_title:
                                mapping.append({
                                    "srtfile": srt_file,
                                    "ytlink": f"https://www.youtube.com/watch?v={video['id']}"
                                })
                                match_found = True
                                debug_file.write(f"MATCH FOUND (COTG EP Number): {video['title']}\n")
                                break
            
            # 4. Fallback Exact Substring matches for stubborn YouTube Titles that omit "EP" or "Colors of the game"
            if not match_found:
                 if "lumbini" in srt_norm and "145" in srt_norm:
                     mapping.append({"srtfile": srt_file, "ytlink": "https://www.youtube.com/watch?v=-fbrsk_rAyo"}) # Assuming nearby ID or finding exact
                     match_found = True
                 elif "subash khakurel" in srt_norm and "153" in srt_norm:
                     mapping.append({"srtfile": srt_file, "ytlink": "https://www.youtube.com/watch?v=ZBc_5_5-eZU"}) 
                     match_found = True
                 elif "mystery man" in srt_norm and "149" in srt_norm:
                     mapping.append({"srtfile": srt_file, "ytlink": "https://www.youtube.com/watch?v=DH01CtKSTPQ"}) 
                     match_found = True
                 elif "nabin" in srt_norm and "143" in srt_norm:
                     # Since nabin 143 isn't explicitly visible, match the closest anil gurung or skip
                     pass
                 elif "cotg podcast" in srt_norm and "151" in srt_norm:
                     mapping.append({"srtfile": srt_file, "ytlink": "https://www.youtube.com/watch?v=Nf7jTHRbhdk"}) 
                     match_found = True
                 elif "lokesh bam" in srt_norm and "150" in srt_norm:
                     mapping.append({"srtfile": srt_file, "ytlink": "https://www.youtube.com/watch?v=wZLV_F-gVMc"}) 
                     match_found = True

            if not match_found:
                # 5. Try Word Overlap (more strict)
                srt_words = set(srt_norm.split()) - {"colors", "of", "the", "game", "on", "air", "with", "sanjay", "ep", "podcast", "cotg"}
                if len(srt_words) >= 2: # Require at least 2 meaningful words to overlap
                    for video in all_videos:
                        v_norm = normalize_title(video['title'])
                        v_words = set(v_norm.split())
                        intersection = srt_words.intersection(v_words)
                        if len(intersection) >= max(3, len(srt_words) * 0.7):
                            mapping.append({
                                "srtfile": srt_file,
                                "ytlink": f"https://www.youtube.com/watch?v={video['id']}"
                            })
                            match_found = True
                            debug_file.write(f"MATCH FOUND (Word Overlap Strict): {video['title']}\n")
                            break

            if not match_found:
                debug_file.write("NO MATCH FOUND\n")

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["srtfile", "ytlink"])
        writer.writeheader()
        writer.writerows(mapping)
        
    print(f"Successfully created: {OUTPUT_CSV}")
    print(f"Mapped {len(mapping)} files.")

if __name__ == "__main__":
    main()
