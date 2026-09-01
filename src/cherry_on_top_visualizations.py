import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Run this inside a Kaggle cell to install seaborn if needed:
# !pip install -q matplotlib seaborn

# Set seaborn style for beautiful, publication-ready plots
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12, 'font.family': 'sans-serif'})

def generate_paper_visualizations(refs, baseline_hyps, proposed_hyps):
    """
    Generates publication-ready visualizations for a research paper.
    Assumes refs, baseline_hyps, and proposed_hyps are in global scope.
    """
    print("\n" + "="*80)
    print("Generating Publication-Ready Visualizations...")
    print("="*80)
    
    # -------------------------------------------------------------------------
    # PLOT 1: Overall Performance Comparison (Bar Chart)
    # -------------------------------------------------------------------------
    baseline_metrics = compute_cs_wer(refs, baseline_hyps)
    proposed_metrics = compute_cs_wer(refs, proposed_hyps)
    
    labels = ['Overall WER', 'CS-WER', 'Nepali-WER']
    baseline_scores = [baseline_metrics['overall_wer'], baseline_metrics['cs_wer'], baseline_metrics['nep_wer']]
    proposed_scores = [proposed_metrics['overall_wer'], proposed_metrics['cs_wer'], proposed_metrics['nep_wer']]
    
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    rects1 = ax.bar(x - width/2, baseline_scores, width, label='Baseline (Constrained)', color='#e74c3c', edgecolor='black')
    rects2 = ax.bar(x + width/2, proposed_scores, width, label='Proposed (Unconstrained)', color='#2ecc71', edgecolor='black')

    ax.set_ylabel('Word Error Rate (%)', fontweight='bold')
    ax.set_title('Performance Comparison: Baseline vs. Proposed Model', fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight='bold')
    ax.legend()
    ax.set_ylim(0, max(max(baseline_scores), max(proposed_scores)) + 15)

    # Add text labels on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)
    fig.tight_layout()
    plt.show()

    # -------------------------------------------------------------------------
    # PLOT 2: Performance by Code-Mixing Index (Bar Chart)
    # -------------------------------------------------------------------------
    cmi_bins = {"Low (< 15)": [], "Medium (15-30)": [], "High (> 30)": []}
    for ref, hyp in zip(refs, proposed_hyps):
        cmi, switches = calculate_cmi_and_switches(ref)
        if switches == 0: continue
        if cmi < 15: cmi_bins["Low (< 15)"].append((ref, hyp))
        elif cmi <= 30: cmi_bins["Medium (15-30)"].append((ref, hyp))
        else: cmi_bins["High (> 30)"].append((ref, hyp))
            
    cmi_labels = list(cmi_bins.keys())
    cmi_cs_wers = []
    
    for name in cmi_labels:
        data = cmi_bins[name]
        if len(data) > 0:
            b_refs = [item[0] for item in data]
            b_hyps = [item[1] for item in data]
            cmi_cs_wers.append(compute_cs_wer(b_refs, b_hyps)['cs_wer'])
        else:
            cmi_cs_wers.append(0)

    fig2, ax2 = plt.subplots(figsize=(7, 4))
    sns.barplot(x=cmi_labels, y=cmi_cs_wers, ax=ax2, palette="Blues_d", edgecolor=".2")
    ax2.set_ylabel('CS-WER (%)', fontweight='bold')
    ax2.set_xlabel('Code-Mixing Index (CMI)', fontweight='bold')
    ax2.set_title('Code-Switched WER across CMI Groups', fontweight='bold', fontsize=14)
    
    for i, v in enumerate(cmi_cs_wers):
        if v > 0:
            ax2.text(i, v + 1, f"{v:.1f}", color='black', ha='center', fontweight='bold')
            
    fig2.tight_layout()
    plt.show()
    
    # -------------------------------------------------------------------------
    # PLOT 3: Error Type Distribution (Pie Chart)
    # -------------------------------------------------------------------------
    categories = {"Intra-Sentential": 0, "Inter-Sentential": 0, "Mixed-Morphology": 0, "Proper Noun": 0}
    for ref, hyp in zip(refs, proposed_hyps):
        output = process_words(ref, hyp)
        for chunk in output.alignments[0]:
            if chunk.type in ("substitute", "delete"):
                ref_words = output.references[0][chunk.ref_start_idx:chunk.ref_end_idx]
                eng_words = [w for w in ref_words if is_english_word(w)]
                if not eng_words: continue
                has_suffix = any(re.search(r'[a-zA-Z]+[\u0900-\u097F]', w) for w in eng_words)
                if has_suffix: categories["Mixed-Morphology"] += 1
                elif len(eng_words) >= 2: categories["Inter-Sentential"] += 1
                elif any(w[0].isupper() for w in eng_words if w): categories["Proper Noun"] += 1
                else: categories["Intra-Sentential"] += 1

    labels_pie = [k for k, v in categories.items() if v > 0]
    sizes_pie = [v for k, v in categories.items() if v > 0]
    
    if sum(sizes_pie) > 0:
        fig3, ax3 = plt.subplots(figsize=(6, 6))
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
        
        # Slight pop-out effect for the largest category
        explode = tuple([0.05 if v == max(sizes_pie) else 0 for v in sizes_pie])
            
        ax3.pie(sizes_pie, explode=explode, labels=labels_pie, colors=colors[:len(sizes_pie)], autopct='%1.1f%%',
                shadow=True, startangle=140, textprops={'fontweight': 'bold'})
        ax3.set_title('Distribution of English Error Types', fontweight='bold', fontsize=14)
        plt.show()

# ====================================================================
# EXECUTE THE VISUALIZATIONS
# ====================================================================
generate_paper_visualizations(references, preds_baseline, preds_unconstrained)
