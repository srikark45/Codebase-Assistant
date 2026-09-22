from indexer.trie import Trie


def test_insert_and_prefix_search():
    trie = Trie()
    trie.insert("parse_json", "a.py", 10)
    trie.insert("parse_args", "a.py", 20)
    trie.insert("format_output", "b.py", 5)

    results = trie.starts_with("parse")
    symbols = {s for s, _ in results}
    assert symbols == {"parse_json", "parse_args"}


def test_no_match_returns_empty():
    trie = Trie()
    trie.insert("foo", "a.py", 1)
    assert trie.starts_with("zzz") == []


def test_contains():
    trie = Trie()
    trie.insert("run_server", "app.py", 1)
    assert trie.contains("run_server") is True
    assert trie.contains("run_serv") is False
