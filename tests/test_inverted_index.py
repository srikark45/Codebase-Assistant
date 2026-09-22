from indexer.inverted_index import InvertedIndex


def test_add_document_and_query():
    index = InvertedIndex()
    index.add_document("a.py", [(1, "parse"), (2, "json"), (3, "parse")])

    assert index.num_docs == 1
    assert index.doc_lengths["a.py"] == 3
    assert index.term_frequency_in_file("parse", "a.py") == 2
    assert index.document_frequency("parse") == 1
    assert index.files_containing("json") == {"a.py"}


def test_save_and_load_roundtrip(tmp_path):
    index = InvertedIndex()
    index.add_document("a.py", [(1, "parse"), (2, "json")])
    index.add_document("b.py", [(1, "parse"), (1, "args")])

    path = tmp_path / "index.json"
    index.save(str(path))

    loaded = InvertedIndex.load(str(path))
    assert loaded.num_docs == index.num_docs
    assert loaded.document_frequency("parse") == 2
    assert loaded.files_containing("args") == {"b.py"}


def test_merge():
    a = InvertedIndex()
    a.add_document("a.py", [(1, "foo")])

    b = InvertedIndex()
    b.add_document("b.py", [(1, "bar")])

    a.merge(b)
    assert a.num_docs == 2
    assert a.files_containing("bar") == {"b.py"}
