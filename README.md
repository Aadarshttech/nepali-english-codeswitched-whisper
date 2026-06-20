# Fine-Tuning Whisper for Nepali-English Code-Switching 🗣️🇳🇵🇬🇧

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=flat&logo=PyTorch&logoColor=white)

This repository provides an academic-grade, end-to-end pipeline for fine-tuning OpenAI's Whisper model to accurately transcribe **Nepali-English Code-Switched** speech. 

This research and corresponding dataset are intended for submission to the **MRL Workshop @ EMNLP 2026**.

## 🌟 The Problem & Our Approach

Existing Nepali speech datasets historically transcribe English loanwords using Devanagari script (e.g., "cricket" written as "क्रिकेट"). ASR models trained on these datasets learn to hallucinate transliterations, which breaks downstream NLP tasks that expect correct English orthography for code-switched entities.

We propose a two-fold solution:
1. **Unconstrained Code-Switched Decoding:** We fine-tune Whisper on a newly curated code-switched dataset and remove constrained decoder forced-tokens during inference, allowing the model to naturally code-switch between Devanagari and Latin scripts.
2. **The CS-WER Metric:** We introduce **Code-Switched Word Error Rate (CS-WER)**, a novel evaluation metric that isolates word error rates strictly to English loanwords, providing a much higher-fidelity measurement of code-switching performance than traditional overall WER.

## 🏆 Key Results

Our unconstrained decoding methodology drastically reduces hallucination and spelling errors on English loanwords compared to the open-source baseline. 

| Model Setup | Overall WER | CS-WER (English Tokens) | Nep-WER (Nepali Tokens) |
| :--- | :---: | :---: | :---: |
| **Zero-Shot Baseline** (OpenAI Whisper-Small) | 117.8% | 101.0% | 98.0% |
| **Our Proposed Model** (Code-switched, Unconstrained, 5-ngram) | **29.2%** | **13.9%** | **28.1%** |

*Note: Our model correctly transcribes English loanwords in continuous Nepali speech with **>86% accuracy**, fundamentally solving the transliteration bottleneck.*

## 📊 Dataset

The core dataset consists of over **50,000 raw audio segments** (~68 hours of clean 16kHz audio) sourced from Nepali YouTube news, podcasts, drama, and documentaries. 
A highly-curated 10,000-sample slice (`metadata_cycle1.csv`) was augmented with LLMs to restore correct English orthography.

* **Kaggle Dataset:** [Nepali-English Code-Switched Audio](https://www.kaggle.com/datasets/panditaadarsh/nepali-english-codeswitched)

## 🗂️ Repository Structure

```
├── notebooks/            # Generated experiments & Jupyter notebooks
├── scripts/              # Data extraction and preprocessing pipeline
│   ├── 1_generate_mapping.py          # Maps YouTube URLs to SRT files
│   ├── 2_extract_audio_from_srt.py    # Downloads audio and slices it by SRT timestamps
│   ├── 3_auto_transliterate.py        # Normalizes transcripts
│   └── ...
├── src/                  # Core model training & evaluation module
│   ├── config.py         # Hyperparameters and paths
│   ├── data_prep.py      # HuggingFace dataset processing
│   ├── eval.py           # Legacy WER metric computation
│   ├── train.py          # Trainer initialization and training loop
│   └── kaggle_evaluation.py # The official EMNLP CS-WER evaluation script
├── docs/                 # Research strategies and documentation
│   └── emnlp_mrl_paper_strategy.md
├── requirements.txt      # Dependencies
├── README.md
└── LICENSE
```

## 🚀 Evaluation Pipeline

If you want to reproduce the results from the table above using your own Kaggle environment:

1. **Upload** the model weights and `metadata_cycle1.csv` to Kaggle.
2. **Run the evaluation script:** You can simply copy the contents of [`src/kaggle_evaluation.py`](src/kaggle_evaluation.py) into a Kaggle notebook cell.
3. Ensure you have installed the requirements:
   ```bash
   pip install transformers datasets accelerate evaluate jiwer tensorboard soundfile librosa
   ```

## 📝 License
This project is licensed under the [MIT License](LICENSE) - maintained by Aadarsh Pandit.
