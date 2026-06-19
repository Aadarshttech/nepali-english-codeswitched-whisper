import os
import pandas as pd
import csv
import torch
from dataclasses import dataclass
from typing import Any, Dict, List, Union
from datasets import Dataset, Audio
from src.config import config

def load_and_prepare_dataset(feature_extractor, tokenizer):
    print("📂 Loading metadata...")

    df = pd.read_csv(
        config.METADATA_CSV,
        engine="python",
        on_bad_lines="warn",
        quoting=csv.QUOTE_MINIMAL
    )

    def resolve_audio_path(relative_path):
        filename = os.path.basename(str(relative_path))
        return os.path.join(config.AUDIO_DIR, filename)

    df["audio_path"] = df["path"].apply(resolve_audio_path)

    missing_mask = ~df["audio_path"].apply(os.path.exists)
    missing_count = missing_mask.sum()
    if missing_count > 0:
        print(f"⚠️  {missing_count} audio files not found! Removing them.")
        df = df[~missing_mask].reset_index(drop=True)

    df["transcription"] = df["transcription"].astype(str)
    df = df.dropna(subset=["transcription"])
    df = df[df["transcription"].str.strip() != ""].reset_index(drop=True)
    df["transcription"] = df["transcription"].str.replace(r"\s+", " ", regex=True).str.strip()

    print("📦 Creating HuggingFace Dataset...")
    dataset = Dataset.from_dict({
        "audio": df["audio_path"].tolist(),
        "transcription": df["transcription"].tolist(),
    }).cast_column("audio", Audio(sampling_rate=config.SAMPLING_RATE))

    dataset = dataset.train_test_split(test_size=config.TEST_SIZE, seed=config.SEED)

    def prepare_dataset(batch):
        audio = batch["audio"]
        batch["input_features"] = feature_extractor(
            audio["array"],
            sampling_rate=audio["sampling_rate"]
        ).input_features[0]
        batch["labels"] = tokenizer(batch["transcription"]).input_ids
        return batch

    print("⚙️  Preprocessing datasets (this may take a while)...")
    dataset = dataset.map(
        prepare_dataset,
        remove_columns=dataset.column_names["train"],
        num_proc=1,
    )
    return dataset

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: Any
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        input_features = [{"input_features": f["input_features"]} for f in features]
        label_features = [{"input_ids": f["labels"]} for f in features]

        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels
        return batch
