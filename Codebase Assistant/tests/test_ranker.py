from indexer.inverted_index import InvertedIndex
from search.ranker import rank


def build_sample_index():
    index = InvertedIndex()
    # "a.py" is heavily about parsing json
    index.add_document("a.py", [(1, "parse"), (2, "json"), (3, "parse"), (4, "json")])
    # "b.py" mentions parse once, unrelated otherwise
    index.add_document("b.py", [(1, "parse"), (2, "render"), (3, "html")])
    return index


def test_rank_prefers_more_relevant_file():
    index = build_sample_index()
    results = rank(index, ["parse", "json"], top_k=5)

    assert results[0][0] == "a.py"  # a.py should outrank b.py
    assert results[0][1] > results[1][1]


def test_rank_ignores_files_without_any_term():
    index = build_sample_index()
    results = rank(index, ["nonexistent_term"], top_k=5)
    assert results == []
