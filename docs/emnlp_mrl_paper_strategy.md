# Strategy Guide: EMNLP MRL Workshop 2026 Submission

Based on your project description and the codebase/notebook we just structured, you have a very strong foundation for an MRL (Multilingual Representation Learning) workshop paper. The problem (transliteration vs. orthography in low-resource code-switching) is highly relevant to the community.

To ensure your paper is accepted and highly regarded, here is a strategic breakdown of what you need to focus on, both in your writing and in your codebase.

## 1. Implement CS-WER in the Codebase (CRITICAL)
Your project description correctly identifies **CS-WER (Code-Switched Word Error Rate)** as the key novel metric for your paper. However, looking at your `src/eval.py` and the original notebook, **you are currently only calculating overall WER**. 

If you submit the paper claiming CS-WER is your novel metric but only report overall WER, reviewers will reject it.
* **Action Item:** You need to write a custom evaluation script that calculates CS-WER. 
* **How to do it:** You can use an alignment tool (like `jiwer`'s detailed alignment outputs) to align the reference and hypothesis. Then, check the reference words against an English dictionary (or use a language identification tool). If the reference word is English, check if the hypothesis predicted it correctly. Calculate the error rate strictly over these English tokens.

## 2. Frame as a "Generalizable Transfer-Learning Pipeline"
EMNLP MRL reviewers are looking for insights that apply broadly, not just "we fixed Nepali Whisper."
* **Action Item:** In your abstract and introduction, emphasize that this is an **LLM-driven data-cleaning pipeline for low-resource code-switched languages**. 
* **The Pitch:** "Many low-resource datasets suffer from transliterated loanwords. We propose a scalable, LLM-based pipeline to restore original orthography in training data, significantly improving code-switched ASR without requiring manual re-transcription."
* **Bonus Points (Highly Recommended):** If you can run a tiny pilot (even just 5 hours of data) on a second language pair like Hindi-English or Bengali-English using the exact same LLM prompt, your paper's chance of acceptance skyrockets.

## 3. Emphasize the Unconstrained Decoding
In your notebook, I saw this crucial line:
```python
model.generation_config.suppress_tokens = []           # English allowed
```
* **Action Item:** Make this a focal point in your methodology section. Explain that standard Whisper relies heavily on forced language tokens (`<|ne|>`), which strictly biases the decoder against outputting English. By unconstraining the decoder and training on properly orthographic data, you allow the model to dynamically rely on acoustic cues rather than a static language ID. 

## 4. The Human-Verified Gold Test Set
Your plan to use 300–500 manually transcribed clips is excellent. Reviewers are highly skeptical of LLM-generated test sets because models often just learn the LLM's biases rather than ground truth.
* **Action Item:** Devote a subsection in your paper specifically to the creation of the "Gold Test Set." State explicitly: *"To ensure rigorous evaluation and prevent LLM-bias leakage, our test set was entirely transcribed by bilingual human annotators and completely isolated from the LLM data pipeline."*

## 5. Recommended Ablation Studies
To make the paper mathematically and scientifically robust, consider adding these experiments to your results table:
1. **Base Whisper Small** (Zero-shot)
2. **Finetuned on Original Data** (Devanagari-only) + Forced `<|ne|>` token
3. **Finetuned on Original Data** (Devanagari-only) + Unconstrained decoding
4. **Finetuned on LLM-Augmented Data** (Code-switched) + Unconstrained decoding *(Your proposed model)*

Comparing #2, #3, and #4 allows you to mathematically prove exactly *how much* improvement comes from the LLM data cleaning vs. simply unconstraining the decoder.

## 6. Error Analysis: Intra vs. Inter-sentential CS
Include a qualitative section looking at *where* the model fails. 
* Does it fail when a speaker switches languages for just one word (**intra-sentential**)? 
* Or does it fail when they switch for a whole sentence (**inter-sentential**)? 
Providing 2-3 real examples in a table will make the paper much more engaging to read.

---

### Next Steps for the Codebase
If you want, I can help you write the **CS-WER calculation script** and add it to `src/eval.py` right now. This is the biggest technical gap currently missing from your repository. Shall we build that next?
