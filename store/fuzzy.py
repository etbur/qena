"""
Fuzzy / typo-tolerant search helpers — no extra packages required.

Techniques used:
  1. Normalise query (lowercase, strip diacritics)
  2. Token matching  — each word in the query searched independently
  3. Trigram similarity — compare 3-char windows, score 0-1
  4. Levenshtein distance — classic edit distance, used for "did you mean?"
  5. Phonetic prefix heuristic — shared starting characters

These run entirely in Python; SQLite doesn't support trigrams natively.
"""

import re
import unicodedata


# ── Normalisation ──────────────────────────────────────────────────────────────

def normalise(text: str) -> str:
    """Lowercase, remove diacritics, collapse whitespace."""
    text = text.lower().strip()
    # Strip diacritics (e.g. café → cafe)
    nfkd = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in nfkd if not unicodedata.combining(c))
    text = re.sub(r'\s+', ' ', text)
    return text


def tokenise(text: str) -> list[str]:
    return [t for t in normalise(text).split() if len(t) > 1]


# ── Trigram similarity ─────────────────────────────────────────────────────────

def trigrams(text: str) -> set[str]:
    t = f'  {normalise(text)}  '
    return {t[i:i+3] for i in range(len(t) - 2)}


def trigram_similarity(a: str, b: str) -> float:
    ta, tb = trigrams(a), trigrams(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ── Levenshtein distance ───────────────────────────────────────────────────────

def levenshtein(a: str, b: str) -> int:
    a, b = normalise(a), normalise(b)
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            ))
        prev = curr
    return prev[-1]


def levenshtein_similarity(a: str, b: str) -> float:
    dist = levenshtein(a, b)
    max_len = max(len(a), len(b), 1)
    return 1.0 - dist / max_len


# ── Product scoring ────────────────────────────────────────────────────────────

def score_product(product, query: str) -> float:
    """
    Returns a relevance score 0–1 for a product against a query.
    Higher = more relevant.
    """
    q = normalise(query)
    tokens = tokenise(query)

    fields = [
        normalise(product.name),
        normalise(product.description or ''),
        normalise(product.category.name if product.category else ''),
        normalise(product.vendor.store_name if product.vendor else ''),
    ]

    best = 0.0

    for field in fields:
        # Exact substring match — highest priority
        if q in field:
            return 1.0

        # Every token present
        if tokens and all(t in field for t in tokens):
            best = max(best, 0.95)

        # Any token present
        for t in tokens:
            if t in field:
                best = max(best, 0.7)
            # Token trigram similarity
            for word in field.split():
                sim = trigram_similarity(t, word)
                best = max(best, sim * 0.85)
                # Levenshtein similarity for short words
                if len(t) >= 3:
                    lev = levenshtein_similarity(t, word)
                    best = max(best, lev * 0.75)

        # Full-field trigram similarity
        tg = trigram_similarity(q, field)
        best = max(best, tg * 0.8)

    return best


# ── Main fuzzy search function ────────────────────────────────────────────────

SCORE_THRESHOLD = 0.30   # minimum score to include in results


def fuzzy_search(products_qs, query: str):
    """
    Returns (scored_products, did_you_mean_str).
    scored_products = list of Product, sorted by relevance.
    did_you_mean_str = corrected query suggestion (or empty string).
    """
    if not query or not query.strip():
        return list(products_qs), ''

    q = normalise(query)
    all_products = list(products_qs)
    scored = []

    for p in all_products:
        s = score_product(p, q)
        if s >= SCORE_THRESHOLD:
            scored.append((s, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [p for _, p in scored]

    # ── "Did you mean?" suggestion ──
    did_you_mean = ''
    if len(results) < 3:
        did_you_mean = _suggest(q, all_products)

    return results, did_you_mean


def _suggest(query: str, products) -> str:
    """
    Build a vocabulary of known words from product names/categories,
    then find the closest word to each query token.
    Returns a corrected query string, or '' if nothing meaningful found.
    """
    vocab: dict[str, int] = {}   # word → frequency

    for p in products:
        for field in [p.name, p.category.name if p.category else '',
                      p.vendor.store_name if p.vendor else '']:
            for word in tokenise(field):
                vocab[word] = vocab.get(word, 0) + 1

    if not vocab:
        return ''

    q_tokens = tokenise(query)
    if not q_tokens:
        return ''

    corrected = []
    changed = False

    for token in q_tokens:
        # Already a known word?
        if token in vocab:
            corrected.append(token)
            continue

        # Find closest word in vocab by Levenshtein
        best_word, best_score = token, 0.0
        for word, freq in vocab.items():
            # Only suggest words of similar length (±40%)
            if abs(len(word) - len(token)) > max(2, len(token) * 0.5):
                continue
            sim = levenshtein_similarity(token, word) + (freq / 100)
            if sim > best_score:
                best_score = sim
                best_word = word

        if best_score > 0.6 and best_word != token:
            corrected.append(best_word)
            changed = True
        else:
            corrected.append(token)

    if changed:
        return ' '.join(corrected)
    return ''
