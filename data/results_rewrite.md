# Corrected Results — Verified Numbers + LaTeX Patches for `acl2023.tex`

*Every Whisper and HuBERT number below was recomputed on the **same 150-utterance test set** through the **same single-alignment partition** (corrected notebook §5 `full_report`). Whisper numbers were additionally re-derived with an independent Levenshtein implementation; all agree. HuBERT was scored in the same run and passed the partition self-check.*

---

## 1. Status: bug fixed, and the architectural thesis now holds under a significance test

The M1 impossibility is gone for **both** models — per-language WERs bracket the aggregate:

> Whisper: 27.21 (Eng) ≤ 29.23 (Overall) ≤ 30.06 (Nep) ✓
> HuBERT:  30.84 (Nep) ≤ 32.38 (Overall) ≤ 35.58 (Eng) ✓

And the paired bootstrap gives you a real, defensible Contribution 3 (see §3b).

## 2. Verified numbers (both models, 150-utt test set)

| Metric | **Whisper-CS** | **HuBERT-CTC** | Paper had (Whisper / HuBERT) |
|---|---|---|---|
| Overall WER | **29.23** [26.60, 32.24] | **32.38** [30.47, 34.26] | 29.39 / 37.58 |
| CER | **13.96** | **11.66** | 13.96 / 16.45 |
| Nepali WER | **30.06** [27.09, 33.60] | **30.84** | 38.75 / 38.98 |
| CM-WER (English) | **27.21** [23.49, 31.24] | **35.58** | 33.59 / 54.14 |
| Switch-point WER | **25.28** | **31.94** | 29.99 / — |
| SDI (S/D/I; total; N) | 909/166/244; 1319; 4512 | 1160/160/141; 1461; 4512 | 934/241/151 / — |
| RTF (T4, bs=1) | ~0.026 | **~0.004** | 0.029 / — |
| Ablation (con==unc) | **150/150 (100%)** | n/a | claimed identical |
| CMI–WER | r=0.074, p=0.37, CI [−0.09, 0.23] | — | r=0.062, p=0.451 |

## 3. What the numbers mean — three things

**(a) The ablation is now a real result.** Force `<|ne|>` vs auto-LID → byte-identical output on 150/150 utterances, one WER, one CI [26.60, 32.24]. The old "identical outputs, different CIs" contradiction is gone. Contribution 1 is fully supported — lean into it.

**(b) Contribution 3 SURVIVES, now with significance — but "collapse" is too strong.** Paired bootstrap (HuBERT − Whisper, same utterances):

| Contrast | Whisper | HuBERT | Δ (Hub−Whis) | 95% CI | Verdict |
|---|---|---|---|---|---|
| **Overall** | 29.23 | 32.38 | +3.15 | [+0.44, +5.49] | **significant** |
| **English (CM-WER)** | 27.21 | 35.58 | +8.36 | [+4.33, +12.10] | **significant** |
| **Nepali** | 30.06 | 30.84 | +0.77 | [−2.57, +3.58] | not significant |

So the paper's core story holds: **on the matrix language the two models are statistically indistinguishable, but Whisper is significantly better on the embedded language.** That is exactly the "multilingual pretraining helps English" claim — now backed by a test.

BUT the magnitude collapsed with the bug fix: the English gap is **8.4 pts, not 20.55**, and HuBERT's English WER is **35.58%, not 54.14%**. 35.58% is "significantly worse," not a "collapse." You must retire the word *collapse* and the phrases *"structural prerequisite" / "structurally essential."*

**(c) The CER paradox — a reviewer landmine you must pre-empt.** HuBERT's **CER (11.66) is *lower* than Whisper's (13.96)** and it runs ~7× faster, yet its word-level English WER is 8 pts worse. Explanation (and it's a *better* mechanistic story than "collapse"): the char-level CTC model produces near-miss *spellings* of embedded English words — each misspelling is one word error but only a few character errors. Your own HuBERT sample shows it exactly: **"health" → "healt t", "Gen Z" → "GeN zज"** (it even leaks a Devanagari character into an English word). Whisper, with multilingual subword pretraining, spells embedded English correctly. Frame the finding as *lexical/orthographic fidelity on the embedded language*, and report CER honestly so a reviewer can't ambush you with it.

## 4. Two consistency issues to fix in the HuBERT training table (Table 7)

Table 7's numbers are on a **different, un-corrected footing** and no longer match the corrected Table 3:

- Its epoch-10 **Overall WER (37.58)** ≠ the corrected comparable number (**32.38**). The ~5-pt gap is likely different normalization/decoding/test-set filtering in the old eval. Re-measure epoch-10 overall on the corrected pipeline.
- Its per-epoch **Nep/Eng columns** were computed with the broken independent-filter method → untrustworthy.

Fix: if you kept per-epoch checkpoints, rescore each through `full_report`. If not, reduce Table 7 to **train/val loss + a consistently-measured overall WER** and drop the per-language columns, or caption it clearly as illustrative training dynamics not directly comparable to Table 3.

---

# 5. Block-by-block LaTeX patches (all numbers final)

Line numbers reference your current `acl2023.tex`.

## 5.1 Abstract (line 58)

Replace from "Through an ablation study…" to "…HuBERT's 54.14\%)." with:

```latex
Through an ablation study, we show that standard fine-tuning of Whisper-Small
completely overcomes this constraint, reducing \wer{} to \textbf{29.23\%} (\cer{} 13.96\%):
forcing the Devanagari language token yields output \emph{identical} to unconstrained
decoding on all 150 test utterances. A controlled comparison against a HuBERT-CTC baseline
shows that both models recognize the matrix language (Nepali) equally well, but Whisper's
multilingual pre-training yields significantly better embedded-language recognition
(English \wer{} 27.21\% vs.\ 35.58\%; +8.4 points, 95\% CI [4.3, 12.1] by paired bootstrap).
```

## 5.2 Contribution 1 (line 83)

```latex
\item \textbf{Overcoming token constraints via fine-tuning.} Through an ablation study,
we demonstrate that standard fine-tuning fundamentally alters how Whisper interprets
language tokens. The fine-tuned model produces \emph{byte-identical} output across all
150 test utterances whether the Nepali token is forced or decoding is unconstrained,
achieving \wer{} 29.23\% in both settings. This reduces \wer{} from the zero-shot
baseline of 170.86\% to \textbf{29.23\%} (an 82.9\% relative reduction).
```

## 5.3 Contribution 3 (line 87)

```latex
\item \textbf{Architectural comparison: Whisper vs.\ HuBERT.} In a controlled comparison
on the same test set and metric, Whisper and a HuBERT-CTC baseline achieve statistically
indistinguishable Nepali \wer{} (30.06\% vs.\ 30.84\%), but Whisper is significantly
better on embedded English (\cmwer{} 27.21\% vs.\ 35.58\%; +8.4 points, paired-bootstrap
95\% CI [4.3, 12.1]), indicating that multilingual pre-training improves embedded-language
recognition even when the matrix language dominates fine-tuning.
```

## 5.4 Contribution 4 (line 89)

```latex
\item \textbf{Stable performance across complexity.} We find no significant association
between code-mixing intensity (\cmi{}) and \wer{} on our test set, though we note this
analysis is underpowered for small effects.
```

## 5.5 Dataset paragraph (line 126) + Table 1 (lines 136–145)

```latex
\noindent The training corpus, \textbf{NepEn-CS-10K}, comprises 10{,}000 utterances of
Nepali-English code-mixed speech, shuffled and split 9{,}000/1{,}000 into training and
validation (seed=42). For evaluation we use a \emph{separate} collection of 200 deeply
code-mixed utterances from disjoint sources; 150 of these form the held-out test set,
with no speaker or topic overlap with training. The full resource totals 10{,}200
utterances. Table~\ref{tab:dataset} summarizes the statistics.
```
Table 1:
```latex
Training utterances (pool) & 10{,}000 \\
\quad -- training split      & 9{,}000 \\
\quad -- validation split    & 1{,}000 \\
Held-out test set (disjoint) & 150 \\
Mean utterance length        & $\sim$30 tokens \\
Test-set token mix           & 68.6\% Nepali / 31.3\% English \\
```

## 5.6 §5.1 Overall — Table 3 (lines 328–331) + prose (line 341)

```latex
Whisper Zero-Shot (Constrained)      & 170.86 [162.33, 179.69] & --$^\dagger$ & -- & -- \\
\textbf{Whisper-CS (Constrained)}    & 29.23 [26.60, 32.24] & 13.96 & 30.06 & 27.21 \\
\textbf{Whisper-CS (Unconstrained)}  & \textbf{29.23} [26.60, 32.24] & \textbf{13.96} & \textbf{30.06} & \textbf{27.21} \\
HuBERT-CTC                           & 32.38 [30.47, 34.26] & 11.66 & 30.84 & 35.58 \\
```
Both Whisper CIs are now identical (byte-identical outputs). Prose (line 341):
```latex
Our fine-tuned Whisper model reduces overall \wer{} to 29.23\% (an 82.9\% relative
reduction). An ablation shows that removing the language constraint at decoding is
\emph{not} the driver: forcing \texttt{<|ne|>} yields output byte-identical to
unconstrained decoding on all 150 utterances, hence the same \wer{} and the same 95\% CI.
The \cer{} of 13.96\% indicates strong character-level accuracy, and the model runs at
RTF 0.026 (single T4, batch size 1). Only \textbf{1} utterance (0.67\%) showed runaway
insertion (hypothesis $>2\times$ reference length).
```

## 5.7 §5.2 Language-Specific Analysis (rewrite lines 346–387)

```latex
Table~\ref{tab:main_results} decomposes performance by language. On the matrix language
(Nepali), Whisper and HuBERT are statistically indistinguishable (30.06\% vs.\ 30.84\%;
paired-bootstrap difference +0.77, 95\% CI [$-2.57$, $+3.58$]). On the embedded language
(English), Whisper is significantly better: \cmwer{} 27.21\% vs.\ 35.58\%, a gap of
\textbf{8.4 points} (95\% CI [4.3, 12.1], paired bootstrap over utterances). The overall
gap (+3.15, 95\% CI [0.44, 5.49]) is thus driven almost entirely by the embedded language.

Notably, HuBERT attains a \emph{lower} corpus \cer{} (11.66\% vs.\ 13.96\%) despite its
higher English \wer{}. The discrepancy is informative: the character-level CTC model
produces near-miss \emph{spellings} of embedded English words (e.g.\ ``health'' $\to$
``healt t'', ``Gen Z'' $\to$ ``Gen zज''), each of which is a single word error but only a
few character errors. Whisper's multilingual subword pre-training instead reproduces
embedded English words correctly. We interpret this as multilingual pre-training providing
stronger \emph{lexical/orthographic fidelity} on the embedded language, rather than a
wholesale loss of English phonetics.
```
Figure 2 coordinates:
```latex
\addplot[...] coordinates {(Overall,29.23) (Nepali,30.06) (\cmwer{},27.21)}; % Whisper
\addplot[...] coordinates {(Overall,32.38) (Nepali,30.84) (\cmwer{},35.58)}; % HuBERT
```
Fig. 2 caption: "…HuBERT shows a significant 8.4-point gap on \cmwer{}, while matrix-language performance is comparable." (Delete "phonetic collapse" / "20.55 percentage-point" wording.)

## 5.8 §5.4 Error Analysis — Table 6 SDI (lines 426–430)

```latex
Substitutions & 909 & 68.9\% \\
Insertions    & 244 & 18.5\% \\
Deletions     & 166 & 12.6\% \\
\midrule
Total errors  & 1{,}319 & 100\% \\
```
N = 4{,}512 reference words; 1319/4512 = 29.23\% reconciles with Table 3. (Optional: contrast HuBERT's profile — S=1160, D=160, I=141 — more substitutions, fewer insertions, consistent with the misspelling story.)

## 5.9 §5.5 CMI + switch-point (lines 454–459)

```latex
To assess whether increased code-mixing degrades recognition, we computed the Pearson
correlation between sentence-level \cmi{} and \wer{} ($r = 0.074$, $p = 0.37$,
95\% CI $[-0.09, 0.23]$).

We did not detect a significant association between mixing intensity and error rate.
With $n=150$ this test is underpowered for small effects (the CI admits $r$ up to
$\approx0.23$), so this is evidence of \emph{no large effect}, not proof of independence.

\noindent The switch-point \wer{}, measured on reference words adjacent to a language
boundary, is 25.28\% for Whisper---\emph{below} its corpus aggregate (29.23\%)---and
31.94\% for HuBERT (near its 32.38\% aggregate). Neither model incurs extra error at
switch points, indicating fluid script-switching rather than boundary hesitation.
```

## 5.10 Discussion (line 471) + Conclusion (line 484)

- Line 471 ("Implications of phonetic collapse"): retitle to **"Embedded-language degradation in HuBERT"**; change "($\sim$75\% of tokens)" → **"(81.6\% of training-pool tokens are Nepali)"**; replace "overwrites the English phonetic representations" with a calibrated version: HuBERT's English word error is significantly higher (35.58\% vs 27.21\%) though its character accuracy remains high, consistent with degraded lexical fidelity rather than acoustic collapse.
- Line 468: "weight updates to the language model head" is still unsupported (all params fine-tuned) → **"weight updates during fine-tuning."**
- Conclusion (line 484): "170.86\% to 29.39\%" → **"170.86\% to 29.23\%"**; replace "English \wer{} reached 54.14\% … structurally essential" with **"Whisper's multilingual pre-training yields significantly better embedded-language recognition than an English-pretrained HuBERT-CTC baseline (English \wer{} 27.21\% vs.\ 35.58\%)."**

---

# 6. Still open (post-HuBERT)

1. **Table 7 fix** — re-measure epoch-10 overall (should be ~32.38, not 37.58) and either rescore per-epoch per-language columns or drop them (see §4).
2. **Multiple seeds (≥3)** for the headline Whisper model; demote the "simple schedule wins" hyperparameter finding to an observation.
3. **Multilingual-CTC control** (MMS / XLS-R) — now more valuable than ever: it would separate "multilingual pretraining" from "seq2seq vs CTC." With the gap down to 8 pts, a reviewer will ask whether the advantage is multilinguality or the seq2seq objective. One multilingual-CTC point settles it.
4. **Fairer zero-shot baselines** (auto-LID, forced `<|en|>`) so 170.86% isn't a strawman.
5. **Human-verify all 150 test references** (not 5%); report κ and restoration error rate.
6. **Verify claims:** "Gemini 3.1 Pro" exact model/version, and Whisper language count ("97" → tokenizer lists ~99).
