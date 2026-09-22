"""
query.py
User-facing search interface: turns a raw query string into ranked
results, and exposes autocomplete over the trie.
"""

from indexer.tokenizer import tokenize_line
from indexer.inverted_index import InvertedIndex
from indexer.trie import Trie
from search.ranker import rank, best_matching_lines


def search(index: InvertedIndex, raw_query: str, top_k: int = 10):
    """
    Search the index for `raw_query`.

    Returns:
        list[dict]: each with keys "file", "score", "lines" (preview
        line numbers where the match is strongest).
    """
    query_terms = tokenize_line(raw_query)
    if not query_terms:
        return []

    ranked_files = rank(index, query_terms, top_k=top_k)

    results = []
    for file, score in ranked_files:
        if score <= 0:
            continue
        results.append({
            "file": file,
            "score": round(score, 4),
            "lines": best_matching_lines(index, query_terms, file),
        })
    return results


def autocomplete(trie: Trie, prefix: str, limit: int = 10):
    """
    Return symbol suggestions for `prefix`.

    Returns:
        list[dict]: each with keys "symbol" and "locations" (file, line pairs).
    """
    matches = trie.starts_with(prefix, limit=limit)
    return [{"symbol": symbol, "locations": locations} for symbol, locations in matches]
