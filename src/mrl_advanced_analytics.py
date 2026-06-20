import re

def is_english_word(word):
    # Matches any word that contains at least one English letter
    return bool(re.search(r'[a-zA-Z]', word))

def calculate_cmi_and_switches(reference):
    words = reference.split()
    if not words:
        return 0, 0
    
    eng_count = 0
    nep_count = 0
    switches = 0
    
    prev_lang = None
    for w in words:
        lang = "ENG" if is_english_word(w) else "NEP"
        if lang == "ENG":
            eng_count += 1
        else:
            nep_count += 1
            
        if prev_lang is not None and lang != prev_lang:
            switches += 1
        prev_lang = lang
        
    total = eng_count + nep_count
    if total == 0:
        return 0, 0
        
    # CMI formula: 100 * [1 - (max(w_i) / sum(w_i))]
    max_lang = max(eng_count, nep_count)
    cmi = 100 * (1 - (max_lang / total))
    return cmi, switches

def run_advanced_mrl_analytics(references, hypotheses):
    """
    Groups sentences by Code-Mixing Index (CMI) and Switching Frequency,
    then computes overall WER and CS-WER for each group using the 
    already-defined compute_cs_wer() function in your Kaggle notebook.
    """
    cmi_bins = {"Low (CMI < 15)": [], "Medium (15-30)": [], "High (CMI > 30)": []}
    switch_bins = {"1 Switch": [], "2 Switches": [], "3+ Switches": []}
    
    for ref, hyp in zip(references, hypotheses):
        cmi, switches = calculate_cmi_and_switches(ref)
        
        # We only care about sentences that actually have code-switching for this analysis
        if switches == 0:
            continue
            
        # Bin by CMI
        if cmi < 15:
            cmi_bins["Low (CMI < 15)"].append((ref, hyp))
        elif cmi <= 30:
            cmi_bins["Medium (15-30)"].append((ref, hyp))
        else:
            cmi_bins["High (CMI > 30)"].append((ref, hyp))
            
        # Bin by Switch Frequency
        if switches == 1:
            switch_bins["1 Switch"].append((ref, hyp))
        elif switches == 2:
            switch_bins["2 Switches"].append((ref, hyp))
        else:
            switch_bins["3+ Switches"].append((ref, hyp))
            
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
                
            refs = [item[0] for item in data]
            hyps = [item[1] for item in data]
            
            # Use the existing compute_cs_wer function
            metrics = compute_cs_wer(refs, hyps)
            ower = metrics["overall_wer"]
            cwer = metrics["cs_wer"]
            
            print(f"{name:<20} | {count:<10} | {ower:<12.1f} | {cwer:<10.1f}")

    print_bin_results("TABLE 2: Performance by Code-Mixing Index (CMI)", cmi_bins)
    print_bin_results("TABLE 3: Performance by Language Switch Frequency", switch_bins)

# ====================================================================
# TO RUN IN KAGGLE: Just paste this entire block in a new cell, then run:
# run_advanced_mrl_analytics(references, preds_unconstrained)
# ====================================================================
