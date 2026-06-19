import os

class Config:
    # Base dataset path
    DATASET_BASE = "./"

    # Correct audio folder
    AUDIO_DIR = os.path.join(
        DATASET_BASE,
        "audios_segment"
    )

    # Correct metadata CSV
    METADATA_CSV = "./metadata_cycle1.csv"

    # Output
    OUTPUT_DIR = "./whisper-small-nepali-english-cs"

    # Model
    MODEL_NAME = "openai/whisper-small" # Start from base model or path
    LANGUAGE = "ne"
    TASK = "transcribe"

    # Training
    BATCH_SIZE = 2
    GRADIENT_ACCUMULATION = 8
    LEARNING_RATE = 1e-5
    WARMUP_STEPS = 300
    NUM_EPOCHS = 5
    EVAL_STEPS = 500
    SAVE_STEPS = 500
    LOGGING_STEPS = 50
    FP16 = True

    # Audio
    SAMPLING_RATE = 16000
    MAX_AUDIO_LENGTH_SEC = 30

    # Split
    TEST_SIZE = 0.05
    SEED = 42
    WER_SAMPLE_SIZE = 5

config = Config()
