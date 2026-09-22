"""
parallel_indexer.py
Indexes a whole repository by processing files concurrently, then
merging the per-file results into a single InvertedIndex and Trie.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed

from indexer.walker import find_source_files, read_file_safely
from indexer.tokenizer import tokenize_file, extract_symbols, language_hint_from_path
from indexer.inverted_index import InvertedIndex
from indexer.trie import Trie


def _index_single_file(path: str):
    """
    Worker function run in a separate process. Must be a top-level
    function (not a method/closure) so it can be pickled for
    ProcessPoolExecutor.

    Returns:
        tuple: (path, tokens_with_lines, symbols_with_lines) or None on failure.
    """
    text = read_file_safely(path)
    if text is None:
        return None

    tokens = tokenize_file(text)
    symbols = extract_symbols(text, language_hint_from_path(path))
    return path, tokens, symbols


def build_index(root: str, max_workers: int = 4):
    """
    Walk `root`, tokenize every source file in parallel, and build a
    combined InvertedIndex + Trie.

    Returns:
        (InvertedIndex, Trie)
    """
    index = InvertedIndex()
    trie = Trie()

    file_paths = list(find_source_files(root))
    if not file_paths:
        return index, trie

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_index_single_file, p): p for p in file_paths}

        for future in as_completed(futures):
            result = future.result()
            if result is None:
                continue

            path, tokens, symbols = result
            index.add_document(path, tokens)
            for line_no, symbol in symbols:
                trie.insert(symbol, path, line_no)

    return index, trie
