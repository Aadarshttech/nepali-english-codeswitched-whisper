import csv
import os

METADATA_PATH = r"D:\Projects\Projects\Code switching\whisper_dataset\metadata.csv"
TEMP_METADATA_PATH = r"D:\Projects\Projects\Code switching\whisper_dataset\metadata_clean.csv"

def clean_text(text):
    # Remove '>>' speaker markers
    text = text.replace('>>', '')
    # Normalize whitespace
    return " ".join(text.replace('\n', ' ').split())

def main():
    if not os.path.exists(METADATA_PATH):
        print("Metadata file not found.")
        return

    print(f"Cleaning {METADATA_PATH}...")
    
    with open(METADATA_PATH, 'r', encoding='utf-8') as fin:
        reader = csv.reader(fin)
        header = next(reader, None)
        
        with open(TEMP_METADATA_PATH, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.writer(fout)
            if header:
                writer.writerow(header)
            
            count = 0
            for row in reader:
                if len(row) == 2:
                    path, transcription = row
                    row[1] = clean_text(transcription)
                    writer.writerow(row)
                    count += 1
                    if count % 5000 == 0:
                        print(f"Processed {count} entries...")

    # Replace original with cleaned version
    os.remove(METADATA_PATH)
    os.rename(TEMP_METADATA_PATH, METADATA_PATH)
    print(f"Successfully cleaned {count} entries in {METADATA_PATH}.")

if __name__ == "__main__":
    main()
