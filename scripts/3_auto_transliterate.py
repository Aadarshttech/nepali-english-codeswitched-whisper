# =============================================================================
# Auto Code-Switch Transliterator (Phase 3 - Improved Approach)
# =============================================================================
# Instead of a manual dictionary, this script:
# 1. Keeps the existing manual dictionary for known high-confidence mappings
# 2. ALSO reverse-transliterates every Devanagari word to Latin script
# 3. Checks if the reverse-transliterated form matches a known English word
# 4. If yes, replaces the Devanagari with the English word automatically
#
# This catches ALL English words written in Devanagari, not just ones we
# manually added.
# =============================================================================

import csv
import re
import time
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# =============================================================================
# Devanagari → Latin reverse transliteration map
# =============================================================================
DEVANAGARI_TO_LATIN = {
    # Vowels
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'ऋ': 'ri',
    # Vowel signs (matras)
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ृ': 'ri',
    # Consonants
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh',
    'ष': 'sh', 'स': 's', 'ह': 'h',
    # Special
    'क्ष': 'ksh', 'त्र': 'tr', 'ज्ञ': 'gya',
    # Halant (virama) - suppresses inherent vowel
    '्': '',
    # Anusvara, Visarga, Chandrabindu
    'ं': 'n', 'ँ': 'n', 'ः': 'h',
    # Nukta variants (for English sounds)
    'ॅ': 'e', 'ॉ': 'o',
}

# Multiple possible reverse transliterations for ambiguous consonants
# This handles the fact that Devanagari can represent the same English
# sound in multiple ways
ALTERNATIVES = {
    'ph': ['f', 'ph'],
    'bh': ['v', 'bh', 'b'],  
    'v': ['v', 'w'],
    'sh': ['sh', 's'],
    'chh': ['ch', 'chh'],
    'ch': ['ch', 'c'],
    'j': ['j', 'z'],
    'k': ['k', 'c', 'q'],
    'kh': ['kh', 'k'],
    'th': ['th', 't'],
    'dh': ['dh', 'd'],
    'gh': ['gh', 'g'],
    'ng': ['ng', 'n'],
    'd': ['d', 't'],
    't': ['t', 'd'],
    'n': ['n', 'nd'],
    'r': ['r', 'l'],
    'l': ['l', 'r'],
    'ee': ['ee', 'i', 'y'],
    'oo': ['oo', 'u'],
    'ai': ['ai', 'a', 'e', 'i'],
    'au': ['au', 'o', 'ow'],
    'a': ['a', 'e', 'u', 'o', ''],
    'e': ['e', 'a', 'i', ''],
    'i': ['i', 'e', 'y', ''],
    'o': ['o', 'a', 'ow'],
    'u': ['u', 'oo', 'o'],
}


def reverse_transliterate(devanagari_word):
    """Convert a Devanagari word to its most likely Latin representation(s)."""
    result = []
    i = 0
    chars = list(devanagari_word)
    
    while i < len(chars):
        # Try two-character combinations first
        if i + 1 < len(chars):
            pair = chars[i] + chars[i+1]
            if pair in DEVANAGARI_TO_LATIN:
                result.append(DEVANAGARI_TO_LATIN[pair])
                i += 2
                continue
        
        # Single character
        ch = chars[i]
        if ch in DEVANAGARI_TO_LATIN:
            latin = DEVANAGARI_TO_LATIN[ch]
            result.append(latin)
        i += 1
    
    # Join and clean up
    base = ''.join(result)
    # Add inherent 'a' after consonants that don't have a vowel sign following
    # This is a simplification - real transliteration is more complex
    return base


def generate_variants(latin_base, max_variants=50):
    """Generate possible English spellings from a Latin base form."""
    # Start with the base
    variants = {latin_base}
    
    # Apply alternative mappings
    for old, news in ALTERNATIVES.items():
        new_variants = set()
        for v in variants:
            if old in v:
                for new in news:
                    new_variants.add(v.replace(old, new, 1))
        variants.update(new_variants)
        if len(variants) > max_variants:
            break
    
    # Also try common English spelling patterns
    extra = set()
    for v in list(variants):
        # Double letters
        for ch in 'sltpnmrg':
            extra.add(v.replace(ch, ch*2, 1))
        # -tion pattern
        if v.endswith('san') or v.endswith('sn'):
            extra.add(v[:-3] + 'tion')
            extra.add(v[:-2] + 'tion')
        if v.endswith('shun') or v.endswith('shn'):
            extra.add(v[:-4] + 'tion')
            extra.add(v[:-3] + 'tion')
        # -ment pattern
        if v.endswith('ment'):
            extra.add(v)
        # -ing pattern  
        if v.endswith('ing'):
            extra.add(v)
    
    variants.update(extra)
    return variants


# =============================================================================
# Load a comprehensive English word list
# =============================================================================
def load_english_words():
    """Load English words. Uses nltk if available, otherwise a built-in set."""
    words = set()
    
    # Try nltk first
    try:
        import nltk
        try:
            from nltk.corpus import words as nltk_words
            words.update(w.lower() for w in nltk_words.words())
            print(f"  Loaded {len(words)} words from NLTK")
        except LookupError:
            nltk.download('words', quiet=True)
            from nltk.corpus import words as nltk_words
            words.update(w.lower() for w in nltk_words.words())
            print(f"  Loaded {len(words)} words from NLTK (downloaded)")
    except ImportError:
        pass
    
    # Add a comprehensive set of common English words used in Nepali conversations
    # This covers words that may not be in nltk but are commonly code-switched
    COMMON_ENGLISH = {
        # Economic / Government / Professional
        'economy', 'economic', 'economics', 'economist', 'economies',
        'agriculture', 'agricultural', 'agriculturalist',
        'gdp', 'gnp', 'inflation', 'deflation',
        'development', 'developer', 'developing', 'developed',
        'contribution', 'contributor', 'contributing', 'contribute',
        'sector', 'sectors', 'public', 'private',
        'based', 'base', 'basis',
        'remittance', 'remittances',
        'industrialization', 'industrial', 'industry', 'industries',
        'production', 'product', 'products', 'productive', 'productivity',
        'infrastructure', 'investment', 'investor', 'invest', 'investing',
        'governance', 'government', 'governing', 'governor',
        'democracy', 'democratic', 'democrat',
        'republic', 'republican', 'constitution', 'constitutional',
        'parliament', 'parliamentary', 'minister', 'ministry',
        'policy', 'policies', 'political', 'politician', 'politics',
        'election', 'elections', 'elected', 'electorate',
        'corruption', 'corrupt', 'corrupted',
        'bureaucracy', 'bureaucratic', 'bureaucrat',
        'institution', 'institutional', 'institutions',
        'regulation', 'regulations', 'regulate', 'regulatory',
        'budget', 'budgets', 'fiscal', 'monetary',
        'export', 'exports', 'exporter', 'import', 'imports', 'importer',
        'trade', 'trading', 'trader', 'customs',
        'tax', 'taxes', 'taxation', 'taxpayer',
        'revenue', 'revenues',
        'poverty', 'inequality', 'unemployment', 'employment',
        'population', 'populated', 'demographic', 'demographics',
        'migration', 'migrant', 'migrants', 'migrate',
        'urbanization', 'urban', 'rural',
        'sustainable', 'sustainability', 'environment', 'environmental',
        'resource', 'resources', 'natural',
        'foreign', 'domestic', 'bilateral', 'multilateral',
        'diplomacy', 'diplomatic', 'diplomat', 'ambassador',
        'sovereignty', 'sovereign', 'independent', 'independence',
        
        # Technology & Science
        'technology', 'technological', 'technical', 'technician',
        'digital', 'software', 'hardware', 'computer', 'internet',
        'artificial', 'intelligence', 'machine', 'learning',
        'data', 'database', 'algorithm', 'programming',
        'innovation', 'innovative', 'innovator',
        'research', 'researcher', 'researching',
        'science', 'scientific', 'scientist',
        'engineering', 'engineer', 'engineers',
        'medical', 'medicine', 'doctor', 'hospital', 'health',
        'healthcare', 'therapy', 'therapist', 'diagnosis',
        'psychology', 'psychological', 'psychologist',
        'climate', 'weather', 'temperature', 'pollution',
        'energy', 'solar', 'renewable', 'electricity',
        'nuclear', 'atomic', 'radiation',
        'satellite', 'telescope', 'observatory',
        'laboratory', 'experiment', 'hypothesis',
        
        # Media & Entertainment
        'media', 'social', 'platform', 'platforms',
        'content', 'creator', 'creators', 'audience',
        'subscriber', 'subscribers', 'subscription',
        'broadcast', 'broadcasting', 'broadcaster',
        'journalism', 'journalist', 'journalists',
        'documentary', 'documentaries',
        'entertainment', 'entertaining', 'entertainer',
        'celebrity', 'celebrities', 'fame', 'famous',
        'interview', 'interviewing', 'interviewer',
        'podcast', 'podcasts', 'podcaster',
        'episode', 'episodes', 'season', 'seasons',
        'trending', 'trend', 'trends', 'viral',
        'influence', 'influencer', 'influencers',
        'brand', 'branding', 'advertisement', 'marketing',
        
        # Education & Academic
        'education', 'educational', 'academic', 'academics',
        'university', 'universities', 'college', 'colleges',
        'scholarship', 'scholarships', 'fellowship',
        'degree', 'degrees', 'diploma', 'certificate',
        'curriculum', 'syllabus', 'examination', 'exam',
        'graduate', 'graduated', 'graduation', 'undergraduate',
        'professor', 'lecturer', 'teacher', 'student', 'students',
        'literature', 'literary', 'philosophy', 'philosophical',
        'history', 'historical', 'historian',
        'geography', 'geographical', 'biology', 'biological',
        'chemistry', 'chemical', 'physics', 'physical',
        'mathematics', 'mathematical', 'statistics', 'statistical',
        
        # Sports (common ones)
        'cricket', 'football', 'basketball', 'volleyball',
        'tournament', 'championship', 'league', 'match',
        'player', 'players', 'coach', 'coaching',
        'team', 'teams', 'captain', 'performance',
        'training', 'trainer', 'practice', 'practicing',
        'score', 'scoring', 'record', 'records',
        'stadium', 'arena', 'ground', 'pitch',
        'referee', 'umpire', 'fitness', 'athlete',
        
        # Common conversational English
        'actually', 'basically', 'definitely', 'honestly',
        'probably', 'especially', 'generally', 'exactly',
        'absolutely', 'obviously', 'certainly', 'literally',
        'personally', 'technically', 'practically', 'seriously',
        'experience', 'experienced', 'experiences',
        'opportunity', 'opportunities',
        'responsibility', 'responsible',
        'relationship', 'relationships',
        'management', 'manager', 'managing',
        'situation', 'situations',
        'generation', 'generations',
        'communication', 'communicate',
        'competition', 'competitive', 'competitor',
        'organization', 'organizational', 'organize',
        'professional', 'profession', 'professionals',
        'international', 'national', 'regional', 'local',
        'traditional', 'tradition', 'traditions',
        'modern', 'modernization', 'modernity',
        'culture', 'cultural', 'cultures',
        'society', 'social', 'societal',
        'community', 'communities',
        'identity', 'identify', 'identification',
        'perspective', 'perspectives',
        'challenge', 'challenges', 'challenging',
        'solution', 'solutions',
        'progress', 'progressive', 'progression',
        'success', 'successful', 'successfully',
        'failure', 'failed', 'fail',
        'process', 'processes', 'processing',
        'result', 'results', 'resulting',
        'impact', 'impacts', 'impactful',
        'benefit', 'benefits', 'beneficial',
        'advantage', 'advantages', 'disadvantage',
        'quality', 'qualities',
        'standard', 'standards',
        'strategy', 'strategies', 'strategic',
        'analysis', 'analyze', 'analytical',
        'concept', 'concepts', 'conceptual',
        'theory', 'theories', 'theoretical',
        'evidence', 'evident',
        'factor', 'factors',
        'issue', 'issues',
        'topic', 'topics',
        'aspect', 'aspects',
        'context', 'contexts',
        'approach', 'approaches',
        'method', 'methods', 'methodology',
        'structure', 'structural', 'structures',
        'framework', 'frameworks',
        'system', 'systems', 'systematic',
        'network', 'networks', 'networking',
        'channel', 'channels',
        'platform', 'platforms',
        'feature', 'features',
        'function', 'functions', 'functional',
        'category', 'categories',
        'version', 'versions',
        'option', 'options',
        'design', 'designs', 'designer',
        'pattern', 'patterns',
        'focus', 'focused', 'focusing',
        'target', 'targets', 'targeting', 'targeted',
        'goal', 'goals',
        'mission', 'missions',
        'vision', 'visions',
        'purpose', 'purposes',
        'objective', 'objectives',
        'interest', 'interests', 'interesting', 'interested',
        'figure', 'figures',
        'realization', 'realize', 'realized',
        'awareness', 'aware',
        'knowledge', 'knowledgeable',
        'information', 'informed', 'inform',
        
        # Common short words often code-switched
        'yes', 'no', 'ok', 'okay', 'sure', 'thanks', 'sorry',
        'hi', 'hello', 'bye', 'please', 'like', 'just',
        'right', 'wrong', 'good', 'bad', 'great', 'nice',
        'cool', 'hot', 'cold', 'big', 'small', 'old', 'new',
        'start', 'stop', 'go', 'come', 'get', 'give', 'take',
        'make', 'do', 'see', 'look', 'feel', 'think', 'know',
        'want', 'need', 'try', 'help', 'work', 'play', 'call',
        'talk', 'walk', 'run', 'sit', 'stand', 'open', 'close',
        'change', 'move', 'turn', 'put', 'set', 'keep', 'let',
        'say', 'tell', 'ask', 'answer', 'talk', 'speak',
        'live', 'love', 'hate', 'enjoy', 'miss', 'wish',
        'believe', 'hope', 'dream', 'plan', 'decide', 'choose',
        'follow', 'lead', 'join', 'leave', 'stay', 'wait',
        'fight', 'win', 'lose', 'pass', 'fail', 'break',
        'build', 'create', 'destroy', 'fix', 'check',
        'learn', 'teach', 'study', 'read', 'write',
        'buy', 'sell', 'pay', 'spend', 'save', 'invest',
        
        # Adjectives commonly code-switched
        'interesting', 'important', 'different', 'difficult',
        'beautiful', 'comfortable', 'available', 'possible',
        'impossible', 'successful', 'powerful', 'popular',
        'amazing', 'fantastic', 'wonderful', 'excellent',
        'serious', 'honest', 'genuine', 'real', 'fake',
        'smart', 'strong', 'weak', 'rich', 'poor',
        'safe', 'dangerous', 'lucky', 'happy', 'sad',
        'angry', 'scared', 'confident', 'surprised', 'shocked',
        
        # Time / Place
        'weekend', 'weekday', 'morning', 'evening', 'night',
        'today', 'tomorrow', 'yesterday', 'daily', 'weekly',
        'monthly', 'yearly', 'annual', 'regular', 'regularly',
        'recent', 'recently', 'current', 'currently',
        'future', 'present', 'past', 'modern', 'ancient',
        'city', 'town', 'village', 'country', 'nation',
        'world', 'global', 'worldwide', 'abroad',
        
        # Business
        'business', 'company', 'corporate', 'corporation',
        'startup', 'startups', 'entrepreneur', 'entrepreneurship',
        'market', 'marketing', 'marketplace',
        'customer', 'customers', 'client', 'clients',
        'service', 'services', 'delivery',
        'profit', 'profitable', 'loss', 'losses',
        'salary', 'income', 'wage', 'wages',
        'career', 'job', 'jobs', 'profession',
        'office', 'offices', 'workplace',
        'meeting', 'conference', 'seminar', 'workshop',
        'project', 'projects', 'program', 'programs',
        'plan', 'planning', 'planned',
        'deal', 'deals', 'contract', 'agreement',
        'partner', 'partnership', 'collaborate', 'collaboration',
    }
    
    words.update(COMMON_ENGLISH)
    return words


# =============================================================================
# Devanagari words that look English after reverse-transliteration but are
# actually genuine Nepali words.  These must NEVER be auto-replaced.
# =============================================================================
NEPALI_FALSE_POSITIVES = {
    'बस',       # Nepali "bas" = enough/stop/sit, NOT English "bus"
}

# =============================================================================
# Build the Devanagari-to-English mapping using reverse transliteration
# =============================================================================
def build_auto_dictionary(csv_path, english_words):
    """Scan the dataset and build an automatic dictionary of Devanagari→English."""
    DEVANAGARI_RE = re.compile(r'[\u0900-\u097F]+')
    auto_dict = {}
    
    # Collect all unique Devanagari words
    devanagari_words = set()
    print("  Scanning dataset for unique Devanagari words...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 2: continue
            words = row[1].split()
            for w in words:
                if DEVANAGARI_RE.search(w):
                    devanagari_words.add(w)
    
    print(f"  Found {len(devanagari_words)} unique Devanagari tokens")
    
    # For each Devanagari word, try reverse transliteration
    matched = 0
    for dv_word in devanagari_words:
        # Skip words that are known false positives
        if dv_word in NEPALI_FALSE_POSITIVES:
            continue
            
        # Strip common Nepali suffixes to get the base English word
        # Nepali postpositions often attached: को, मा, ले, लाई, हरु, बाट, etc.
        bases = [dv_word]
        suffixes_to_try = [
            ('को', ' को'), ('मा', ' मा'), ('ले', ' ले'), ('लाई', ' लाई'),
            ('हरु', ' हरु'), ('हरुले', ' हरुले'), ('हरुको', ' हरुको'),
            ('हरुमा', ' हरुमा'), ('हरुलाई', ' हरुलाई'),
            ('बाट', ' बाट'), ('बाटै', ' बाटै'),
            ('कै', ' कै'), ('नै', ' नै'), ('मै', ' मै'),
        ]
        
        for suffix, replacement in suffixes_to_try:
            if dv_word.endswith(suffix) and len(dv_word) > len(suffix) + 2:
                base = dv_word[:-len(suffix)]
                bases.append(base)
        
        for base in bases:
            latin = reverse_transliterate(base)
            if len(latin) < 2:
                continue
            
            # Check if it matches any English word
            variants = generate_variants(latin, max_variants=30)
            for v in variants:
                v_lower = v.lower()
                if v_lower in english_words and len(v_lower) >= 3:
                    # Found a match!
                    if base == dv_word:
                        auto_dict[dv_word] = v_lower
                    else:
                        # Reconstruct with suffix
                        suffix_str = dv_word[len(base):]
                        auto_dict[dv_word] = v_lower + ' ' + suffix_str
                    matched += 1
                    break
    
    print(f"  Auto-matched {matched} Devanagari words to English")
    return auto_dict


# =============================================================================
# Main
# =============================================================================
def main():
    INPUT_CSV = r'D:\Projects\Projects\Code switching\whisper_dataset\metadata.csv'
    OUTPUT_CSV = r'D:\Projects\Projects\Code switching\whisper_dataset\metadata_code_switched.csv'
    
    print("=" * 60)
    print("AUTO CODE-SWITCH TRANSLITERATOR (Phase 3)")
    print("=" * 60)
    
    # Step 1: Load the existing manual dictionary
    print("\n[1/4] Loading manual dictionary...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from code_switch_dictionary import MULTI_WORD_PHRASES, SINGLE_WORDS, build_replacer, code_switch
    
    manual_replacements = build_replacer(MULTI_WORD_PHRASES, SINGLE_WORDS)
    print(f"  {len(MULTI_WORD_PHRASES)} multi-word phrases")
    print(f"  {len(SINGLE_WORDS)} single words")
    
    # Step 2: Load English word list
    print("\n[2/4] Loading English word list...")
    english_words = load_english_words()
    print(f"  Total English words available: {len(english_words)}")
    
    # Step 3: Build auto-dictionary from the dataset
    print("\n[3/4] Building auto-dictionary from dataset scan...")
    auto_dict = build_auto_dictionary(INPUT_CSV, english_words)
    
    # Merge: manual dictionary takes priority over auto
    # auto_dict entries that conflict with SINGLE_WORDS are dropped
    existing_keys = set(SINGLE_WORDS.keys()) | set(MULTI_WORD_PHRASES.keys())
    new_additions = {k: v for k, v in auto_dict.items() if k not in existing_keys}
    print(f"  New auto-discovered words (not in manual dict): {len(new_additions)}")
    
    # Show some examples
    print("\n  Sample auto-discovered mappings:")
    for i, (k, v) in enumerate(sorted(new_additions.items(), key=lambda x: len(x[0]), reverse=True)):
        if i < 30:
            print(f"    {k} → {v}")
        else:
            break
    
    # Save the new additions to a file for review
    additions_file = r'D:\Projects\Projects\Code switching\auto_discovered_words.csv'
    with open(additions_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["devanagari", "english"])
        for k, v in sorted(new_additions.items()):
            writer.writerow([k, v])
    print(f"\n  Saved {len(new_additions)} auto-discovered words to {additions_file}")
    
    # Step 4: Process the dataset
    print(f"\n[4/4] Processing {INPUT_CSV}...")
    
    # Build regex patterns for auto-discovered words
    auto_replacements = []
    for dv, eng in sorted(new_additions.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(r'(?<!\S)' + re.escape(dv) + r'(?!\S)')
        auto_replacements.append((pattern, eng))
    
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)
    
    total = len(rows)
    start_time = time.time()
    changed_count = 0
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["path", "transcription"])
        
        for i, row in enumerate(rows):
            if len(row) < 2:
                continue
            
            path, transcription = row[0], row[1]
            
            # Apply manual dictionary first (highest priority)
            result = code_switch(transcription, manual_replacements)
            
            # Then apply auto-discovered words
            for pattern, replacement in auto_replacements:
                result = pattern.sub(replacement, result)
            
            if result != transcription:
                changed_count += 1
            
            writer.writerow([path, result])
            
            if (i + 1) % 5000 == 0:
                elapsed = time.time() - start_time
                print(f"  [{i+1}/{total}] {elapsed:.1f}s elapsed, {changed_count} entries changed")
    
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"DONE in {elapsed:.1f} seconds!")
    print(f"Total entries: {total}")
    print(f"Entries with changes: {changed_count} ({changed_count/total*100:.1f}%)")
    print(f"Output: {OUTPUT_CSV}")
    print(f"{'='*60}")
    
    # Print some samples
    print("\n--- SAMPLE RESULTS (around line 3760) ---")
    with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for i, row in enumerate(reader):
            if 3758 <= i <= 3770:
                print(f"  [{i}] {row[1][:150]}")


if __name__ == "__main__":
    main()
