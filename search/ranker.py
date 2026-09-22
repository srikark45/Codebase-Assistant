"""
ranker.py
Scores files against a query using BM25 (a stronger, length-normalized
successor to plain TF-IDF), so common terms in short files aren't
unfairly favored over relevant terms in longer files.
"""

import math

from indexer.inverted_index import InvertedIndex

# Standard BM25 tuning constants
K1 = 1.5
B = 0.75


def _idf(index: InvertedIndex, term: str) -> float:
    """Inverse document frequency: rarer terms score higher."""
    df = index.document_frequency(term)
    if df == 0:
        return 0.0
    # +1 smoothing to avoid negative scores / div-by-zero
    return math.log((index.num_docs - df + 0.5) / (df + 0.5) + 1)


def _bm25_score(index: InvertedIndex, term: str, file: str, avg_doc_len: float) -> float:
    tf = index.term_frequency_in_file(term, file)
    if tf == 0:
        return 0.0

    doc_len = index.doc_lengths.get(file, 0)
    idf = _idf(index, term)

    numerator = tf * (K1 + 1)
    denominator = tf + K1 * (1 - B + B * (doc_len / avg_doc_len if avg_doc_len else 1))
    return idf * (numerator / denominator)


def rank(index: InvertedIndex, query_terms: list, top_k: int = 10):
    """
    Score every candidate file against `query_terms` and return the
    top_k (file, score) pairs, highest score first.
    """
    avg_doc_len = index.average_doc_length()

    # Only consider files that contain at least one query term
    candidate_files = set()
    for term in query_terms:
        candidate_files |= index.files_containing(term)

    scores = {}
    for file in candidate_files:
        total = 0.0
        for term in query_terms:
            total += _bm25_score(index, term, file, avg_doc_len)
        scores[file] = total

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:top_k]


def best_matching_lines(index: InvertedIndex, query_terms: list, file: str, limit: int = 3):
    """
    For a given file, return up to `limit` line numbers that contain
    the most query terms — used to show a preview snippet.
    """
    line_hits = {}
    for term in query_terms:
        for posting in index.postings.get(term, []):
            if posting.file == file:
                line_hits[posting.line] = line_hits.get(posting.line, 0) + 1

    best_lines = sorted(line_hits.items(), key=lambda kv: kv[1], reverse=True)
    return [line for line, _ in best_lines[:limit]]
