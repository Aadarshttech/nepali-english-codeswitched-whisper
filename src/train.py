import gc
import torch
from transformers import (
    WhisperFeatureExtractor,
    WhisperTokenizer,
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments
)
from src.config import config
from src.data_prep import load_and_prepare_dataset, DataCollatorSpeechSeq2SeqWithPadding
from src.eval import get_compute_metrics_fn, WERLoggingTrainer, get_wer_samples

def main():
    print(f"🤖 Loading {config.MODEL_NAME}...")

    feature_extractor = WhisperFeatureExtractor.from_pretrained(config.MODEL_NAME)
    tokenizer = WhisperTokenizer.from_pretrained(config.MODEL_NAME, language="ne", task="transcribe")
    processor = WhisperProcessor.from_pretrained(config.MODEL_NAME, language="ne", task="transcribe")

    model = WhisperForConditionalGeneration.from_pretrained(config.MODEL_NAME)
    model.generation_config.language = "ne"
    model.generation_config.task = "transcribe"
    model.generation_config.forced_decoder_ids = processor.get_decoder_prompt_ids(language="ne", task="transcribe")
    model.generation_config.suppress_tokens = []
    model.generation_config.max_new_tokens = 225
    model.generation_config.no_repeat_ngram_size = 3

    dataset = load_and_prepare_dataset(feature_extractor, tokenizer)
    data_collator = DataCollatorSpeechSeq2SeqWithPadding(
        processor=processor,
        decoder_start_token_id=model.config.decoder_start_token_id,
    )

    wer_samples = get_wer_samples(dataset)

    training_args = Seq2SeqTrainingArguments(
        output_dir=config.OUTPUT_DIR,
        per_device_train_batch_size=config.BATCH_SIZE,
        per_device_eval_batch_size=config.BATCH_SIZE,
        gradient_accumulation_steps=config.GRADIENT_ACCUMULATION,
        learning_rate=config.LEARNING_RATE,
        warmup_steps=config.WARMUP_STEPS,
        lr_scheduler_type="linear",
        num_train_epochs=config.NUM_EPOCHS,
        eval_steps=config.EVAL_STEPS,
        save_steps=config.SAVE_STEPS,
        logging_steps=config.LOGGING_STEPS,
        eval_strategy="steps",
        predict_with_generate=True,
        generation_max_length=225,
        fp16=config.FP16,
        dataloader_num_workers=2,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        report_to=["tensorboard"],
        push_to_hub=False,
        remove_unused_columns=False,
        label_names=["labels"],
        seed=config.SEED,
    )

    trainer = WERLoggingTrainer(
        args=training_args,
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        data_collator=data_collator,
        compute_metrics=get_compute_metrics_fn(tokenizer),
        processing_class=processor.feature_extractor,
        wer_samples=wer_samples,
        wer_tokenizer=tokenizer,
    )

    print("=" * 60)
    print("🚀 STARTING FINE-TUNING")
    print("=" * 60)

    torch.cuda.empty_cache()
    gc.collect()
    trainer.train()

if __name__ == "__main__":
    main()
