# Run this cell first to install required dependencies:
# !pip install -q transformers datasets accelerate evaluate jiwer tensorboard soundfile librosa

import os
import gc
import re
import csv
import torch
import pandas as pd
import evaluate
import librosa
from transformers import (
    WhisperFeatureExtractor,
    WhisperTokenizer,
    WhisperForConditionalGeneration,
    logging as hf_logging
)
from jiwer import process_words

# Suppress annoying generation warnings
hf_logging.set_verbosity_error()

print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")

# =============================================================================
# 1. CONFIGURATION (Kaggle Paths)
# =============================================================================
class Config:
    AUDIO_DIR = "/kaggle/input/datasets/panditaadarsh/nepali-english-codeswitched/kaggle_upload/audios_segment"
    METADATA_CSV = "/kaggle/input/datasets/panditaadarsh/codeswitchv3/metadata_cycle1.csv"
    
    BASELINE_MODEL = "openai/whisper-small"
    TRAINED_MODEL = "/kaggle/input/datasets/panditaadarsh/latest-codeswitch-model/latest csmodel"

    SAMPLING_RATE = 16000
    TEST_SIZE = 500
    SEED = 42

config = Config()

# =============================================================================
# 2. DATA LOADING
# =============================================================================
def load_test_data():
    print("\nLoading metadata...")
    df = pd.read_csv(config.METADATA_CSV, engine="python", on_bad_lines="warn", quoting=csv.QUOTE_MINIMAL)
    
    def resolve_audio_path(rel):
        return os.path.join(config.AUDIO_DIR, os.path.basename(str(rel)))
    
    df["audio_path"] = df["path"].apply(resolve_audio_path)
    missing = ~df["audio_path"].apply(os.path.exists)
    if missing.sum() > 0:
        df = df[~missing].reset_index(drop=True)
        
    df["transcription"] = df["transcription"].astype(str)
    df = df.dropna(subset=["transcription"])
    df = df[df["transcription"].str.strip() != ""].reset_index(drop=True)
    df["transcription"] = df["transcription"].str.replace(r"\s+", " ", regex=True).str.strip()
    
    test_df = df.sample(n=config.TEST_SIZE, random_state=config.SEED).reset_index(drop=True)
    print(f"Test set size: {len(test_df)} samples")
    return test_df

# =============================================================================
# 3. METRICS (CS-WER)
# =============================================================================
wer_metric = evaluate.load("wer")

def is_english_word(word):
    cleaned = re.sub(r'[^\w]', '', str(word))
    if not cleaned: return False
    return cleaned[0].isascii() and cleaned[0].isalpha()

def compute_cs_wer(references, hypotheses):
    total_eng, correct_eng, sub_eng, del_eng, ins_eng = 0, 0, 0, 0, 0
    total_nep, correct_nep, sub_nep, del_nep = 0, 0, 0, 0

    overall_wer = wer_metric.compute(predictions=hypotheses, references=references)

    for ref, hyp in zip(references, hypotheses):
        output = process_words(ref, hyp)
        for chunk in output.alignments[0]:
            ref_slice = output.references[0][chunk.ref_start_idx:chunk.ref_end_idx]
            hyp_slice = output.hypotheses[0][chunk.hyp_start_idx:chunk.hyp_end_idx]

            if chunk.type == "equal":
                for w in ref_slice:
                    if is_english_word(w): total_eng += 1; correct_eng += 1
                    else: total_nep += 1; correct_nep += 1
            elif chunk.type == "substitute":
                for w in ref_slice:
                    if is_english_word(w): total_eng += 1; sub_eng += 1
                    else: total_nep += 1; sub_nep += 1
            elif chunk.type == "delete":
                for w in ref_slice:
                    if is_english_word(w): total_eng += 1; del_eng += 1
                    else: total_nep += 1; del_nep += 1
            elif chunk.type == "insert":
                for w in hyp_slice:
                    if is_english_word(w): ins_eng += 1

    cs_wer = (sub_eng + del_eng + ins_eng) / total_eng * 100 if total_eng > 0 else 0.0
    nep_wer = (sub_nep + del_nep) / total_nep * 100 if total_nep > 0 else 0.0

    return {
        "overall_wer": round(overall_wer * 100, 2),
        "cs_wer": round(cs_wer, 2),
        "nep_wer": round(nep_wer, 2),
        "eng_total": total_eng,
    }

# =============================================================================
# 4. INFERENCE ENGINE
# =============================================================================
def run_inference(model_path, audio_paths, constrain_language=True):
    print(f"\nLoading model: {model_path} | Constrained: {constrain_language}")
    feature_extractor = WhisperFeatureExtractor.from_pretrained(model_path)
    tokenizer = WhisperTokenizer.from_pretrained(model_path, language="ne", task="transcribe")
    model = WhisperForConditionalGeneration.from_pretrained(model_path)
    model.to("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()

    model.generation_config.task = "transcribe"
    model.generation_config.max_length = 225
    model.generation_config.max_new_tokens = None
    model.generation_config.no_repeat_ngram_size = 5
    
    if constrain_language:
        model.generation_config.language = "ne"
        model.generation_config.forced_decoder_ids = [
            (1, tokenizer.convert_tokens_to_ids("<|ne|>")),
            (2, tokenizer.convert_tokens_to_ids("<|transcribe|>")),
        ]
    else:
        model.generation_config.language = None
        model.generation_config.forced_decoder_ids = None
        model.generation_config.suppress_tokens = []

    predictions = []
    print("Running inference...")
    for i, path in enumerate(audio_paths):
        audio, sr = librosa.load(path, sr=config.SAMPLING_RATE)
        inputs = feature_extractor(audio, sampling_rate=sr, return_tensors="pt", return_attention_mask=True).to(model.device)
        with torch.no_grad():
            ids = model.generate(inputs.input_features, attention_mask=inputs.attention_mask)
        
        pred_text = tokenizer.decode(ids[0], skip_special_tokens=True)
        predictions.append(pred_text)
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(audio_paths)}")

    del model
    torch.cuda.empty_cache()
    gc.collect()
    return predictions

# =============================================================================
# 5. BASIC ERROR ANALYSIS
# =============================================================================
def perform_error_analysis(references, hypotheses, n_examples=5):
    categories = {"intra_sentential": [], "inter_sentential": [], "mixed_morphology": [], "proper_noun": []}
    for ref, hyp in zip(references, hypotheses):
        output = process_words(ref, hyp)
        for chunk in output.alignments[0]:
            if chunk.type in ("substitute", "delete"):
                ref_words = output.references[0][chunk.ref_start_idx:chunk.ref_end_idx]
                hyp_words = output.hypotheses[0][chunk.hyp_start_idx:chunk.hyp_end_idx]
                eng_words = [w for w in ref_words if is_english_word(w)]
                if not eng_words: continue

                example = {"ref": " ".join(ref_words), "hyp": " ".join(hyp_words) if hyp_words else "[DELETED]"}
                has_suffix = any(re.search(r'[a-zA-Z]+[\u0900-\u097F]', w) for w in eng_words)
                if has_suffix: categories["mixed_morphology"].append(example)
                elif len(eng_words) >= 2: categories["inter_sentential"].append(example)
                elif any(w[0].isupper() for w in eng_words if w): categories["proper_noun"].append(example)
                else: categories["intra_sentential"].append(example)

    print("\n" + "="*50 + "\nERROR ANALYSIS\n" + "="*50)
    for cat, examples in categories.items():
        print(f"\n--- {cat.upper()} ({len(examples)} errors) ---")
        for ex in examples[:n_examples]:
            print(f"  REF: {ex['ref']}")
            print(f"  HYP: {ex['hyp']}")

# =============================================================================
# 6. ADVANCED MRL ANALYTICS (CMI & Switches)
# =============================================================================
def calculate_cmi_and_switches(reference):
    words = str(reference).split()
    if not words: return 0, 0
    
    eng_count, nep_count, switches = 0, 0, 0
    prev_lang = None
    for w in words:
        lang = "ENG" if is_english_word(w) else "NEP"
        if lang == "ENG": eng_count += 1
        else: nep_count += 1
            
        if prev_lang is not None and lang != prev_lang: switches += 1
        prev_lang = lang
        
    total = eng_count + nep_count
    if total == 0: return 0, 0
        
    max_lang = max(eng_count, nep_count)
    cmi = 100 * (1 - (max_lang / total))
    return cmi, switches

def run_advanced_mrl_analytics(refs, hyps):
    cmi_bins = {"Low (CMI < 15)": [], "Medium (15-30)": [], "High (CMI > 30)": []}
    switch_bins = {"1 Switch": [], "2 Switches": [], "3+ Switches": []}
    
    for ref, hyp in zip(refs, hyps):
        cmi, switches = calculate_cmi_and_switches(ref)
        if switches == 0: continue
            
        if cmi < 15: cmi_bins["Low (CMI < 15)"].append((ref, hyp))
        elif cmi <= 30: cmi_bins["Medium (15-30)"].append((ref, hyp))
        else: cmi_bins["High (CMI > 30)"].append((ref, hyp))
            
        if switches == 1: switch_bins["1 Switch"].append((ref, hyp))
        elif switches == 2: switch_bins["2 Switches"].append((ref, hyp))
        else: switch_bins["3+ Switches"].append((ref, hyp))
            
    def print_bin_results(title, bins_dict):
        print("\n" + "="*80)
        print(f"{title}")
        print("="*80)
        print(f"{'Category':<20} | {'Sentences':<10} | {'Overall WER':<12} | {'CS-WER':<10}")
        print("-" * 65)
        for name, data in bins_dict.items():
            count = len(data)
            if count == 0:
                print(f"{name:<20} | {count:<10} | {'N/A':<12} | {'N/A':<10}")
                continue
                
            b_refs = [item[0] for item in data]
            b_hyps = [item[1] for item in data]
            
            metrics = compute_cs_wer(b_refs, b_hyps)
            ower = metrics["overall_wer"]
            cwer = metrics["cs_wer"]
            print(f"{name:<20} | {count:<10} | {ower:<12.1f} | {cwer:<10.1f}")

    print_bin_results("TABLE 2: Performance by Code-Mixing Index (CMI)", cmi_bins)
    print_bin_results("TABLE 3: Performance by Language Switch Frequency", switch_bins)


# =============================================================================
# 7. EXECUTE EVERYTHING IN GLOBAL SCOPE
# =============================================================================
# 1. Load Data
test_df = load_test_data()
audio_paths = test_df["audio_path"].tolist()
references = test_df["transcription"].tolist()

results = {}

# 2. BASELINE (Zero-shot Whisper Constrained)
preds_baseline = run_inference(config.BASELINE_MODEL, audio_paths, constrain_language=True)
results["A: Zero-Shot Baseline"] = compute_cs_wer(references, preds_baseline)

# 3. YOUR TRAINED MODEL (Unconstrained)
preds_unconstrained = run_inference(config.TRAINED_MODEL, audio_paths, constrain_language=False)
results["B: Trained (Unconstrained)"] = compute_cs_wer(references, preds_unconstrained)

# 4. Print initial WER results
print("\n" + "="*80)
print(f"{'Model Setup':<35} | {'Overall WER':<12} | {'CS-WER':<10} | {'Nep-WER':<10}")
print("-" * 80)
for name, metrics in results.items():
    print(f"{name:<35} | {metrics['overall_wer']:<12.1f} | {metrics['cs_wer']:<10.1f} | {metrics['nep_wer']:<10.1f}")
print("="*80)

# 5. Run Error Analysis
perform_error_analysis(references, preds_unconstrained)

# 6. Run Advanced MRL Analytics
run_advanced_mrl_analytics(references, preds_unconstrained)
