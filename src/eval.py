import torch
import evaluate
import numpy as np
from transformers import Seq2SeqTrainer
from src.config import config

wer_metric = evaluate.load("wer")

def get_compute_metrics_fn(tokenizer):
    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids

        label_ids[label_ids == -100] = tokenizer.pad_token_id

        pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        wer = 100 * wer_metric.compute(predictions=pred_str, references=label_str)
        return {"wer": wer}
    return compute_metrics

class WERLoggingTrainer(Seq2SeqTrainer):
    """Seq2SeqTrainer that also logs sampled WER alongside training loss."""
    def __init__(self, *args, wer_samples=None, wer_tokenizer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.wer_samples = wer_samples
        self.wer_tokenizer = wer_tokenizer

    def log(self, logs):
        if self.wer_samples and "loss" in logs and self.model is not None:
            self.model.eval()
            preds_text, refs_text = [], []
            for s in self.wer_samples:
                inp = torch.tensor(s["input_features"]).unsqueeze(0).to(self.model.device)
                with torch.no_grad():
                    ids = self.model.generate(inp, max_new_tokens=225)
                preds_text.append(self.wer_tokenizer.decode(ids[0], skip_special_tokens=True))
                lab = [t if t != -100 else self.wer_tokenizer.pad_token_id for t in s["labels"]]
                refs_text.append(self.wer_tokenizer.decode(lab, skip_special_tokens=True))
            logs["sampled_wer"] = round(
                100 * wer_metric.compute(predictions=preds_text, references=refs_text), 2
            )
            self.model.train()
        super().log(logs)

def get_wer_samples(dataset):
    rng = np.random.RandomState(config.SEED)
    _idx = rng.choice(len(dataset["test"]), config.WER_SAMPLE_SIZE, replace=False)
    return [dataset["test"][int(i)] for i in _idx]
