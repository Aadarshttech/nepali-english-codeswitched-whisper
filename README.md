# Fine-Tuning Whisper for Nepali-English Code-Switching 🗣️🇳🇵🇬🇧

This repository provides a modular, academic-grade pipeline for fine-tuning the Whisper model on **Nepali-English Code-Switched** speech data. 

This project is part of a paper submission to the **MRL EMNLP Workshop (August)**.

## 📊 Dataset: Nepali-English Code-Switched Audio
The dataset consists of approximately 12,000 audio segments containing mixed Nepali and English speech.
* **Dataset Hosting:** The raw data and pre-processed chunks are hosted on Kaggle.
* **Kaggle Link:** [Nepali_english_codeswitched on Kaggle](https://www.kaggle.com/datasets/panditaadarsh/nepali-english-codeswitched)

## 🗂️ Repository Structure

```
├── scripts/              # Data extraction and preprocessing pipeline
│   ├── 1_generate_mapping.py          # Maps YouTube URLs to SRT files
│   ├── 2_extract_audio_from_srt.py    # Downloads audio and slices it by SRT timestamps
│   ├── 3_auto_transliterate.py        # Normalizes transcripts
│   ├── clean_metadata_csv.py
│   └── extract_frames.py
├── src/                  # Core model training module
│   ├── config.py         # Hyperparameters and paths
│   ├── data_prep.py      # HuggingFace dataset processing
│   ├── eval.py           # WER metric computation
│   └── train.py          # Trainer initialization and training loop
├── data/                 # Metadata and mappings
│   └── metadata_cycle1.csv
├── requirements.txt      # Dependencies
├── README.md
└── LICENSE
```

## 🚀 Pipeline Usage

If you are a researcher aiming to reproduce or expand on this dataset, you can follow this end-to-end pipeline.

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```
*(Make sure `ffmpeg` and `yt-dlp` are installed on your system for audio extraction).*

### Step 2: Extract Data from YouTube & SRT
If you have a folder of `.srt` subtitle files, you can build the dataset directly from YouTube:
1. Map subtitles to YouTube video IDs:
   ```bash
   python scripts/1_generate_mapping.py
   ```
2. Download audio and slice it exactly according to the subtitle timestamps:
   ```bash
   python scripts/2_extract_audio_from_srt.py
   ```
*(Note: Ensure paths in the scripts match your local setup).*

### Step 3: Fine-Tune Whisper
Once you have the `audio_segments` and `metadata.csv` (or use the one from Kaggle), update `src/config.py` with your dataset paths.
Start the distributed training process:
```bash
python -m src.train
```

## 📝 License
This project is licensed under the [MIT License](LICENSE).
