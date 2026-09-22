"""
inverted_index.py
Core data structure: term -> list of postings (file, line_no).
Also tracks per-file term frequencies and document lengths, which the
ranker needs for TF-IDF / BM25 scoring.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Posting:
    file: str
    line: int


@dataclass
class InvertedIndex:
    # term -> list of Postings
    postings: dict = field(default_factory=lambda: defaultdict(list))
    # file -> total number of tokens in that file (for BM25 length normalization)
    doc_lengths: dict = field(default_factory=dict)
    # total number of indexed documents (files)
    num_docs: int = 0

    def add_document(self, file_path: str, tokens_with_lines):
        """
        Add a file's tokens to the index.

        Args:
            file_path: path of the file being indexed.
            tokens_with_lines: iterable of (line_no, token) pairs.
        """
        count = 0
        for line_no, token in tokens_with_lines:
            self.postings[token].append(Posting(file=file_path, line=line_no))
            count += 1
        self.doc_lengths[file_path] = count
        self.num_docs += 1

    def document_frequency(self, term: str) -> int:
        """Number of distinct files containing `term`."""
        return len({p.file for p in self.postings.get(term, [])})

    def term_frequency_in_file(self, term: str, file_path: str) -> int:
        """How many times `term` appears in `file_path`."""
        return sum(1 for p in self.postings.get(term, []) if p.file == file_path)

    def average_doc_length(self) -> float:
        if not self.doc_lengths:
            return 0.0
        return sum(self.doc_lengths.values()) / len(self.doc_lengths)

    def files_containing(self, term: str):
        """Set of files that contain `term` at least once."""
        return {p.file for p in self.postings.get(term, [])}

    def save(self, path: str):
        """Serialize the index to a JSON file."""
        serializable = {
            "postings": {
                term: [(p.file, p.line) for p in plist]
                for term, plist in self.postings.items()
            },
            "doc_lengths": self.doc_lengths,
            "num_docs": self.num_docs,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f)

    @classmethod
    def load(cls, path: str) -> "InvertedIndex":
        """Load a previously saved index from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        index = cls()
        index.postings = defaultdict(list)
        for term, plist in data["postings"].items():
            index.postings[term] = [Posting(file=f_, line=l_) for f_, l_ in plist]
        index.doc_lengths = data["doc_lengths"]
        index.num_docs = data["num_docs"]
        return index

    def merge(self, other: "InvertedIndex"):
        """Merge another index's postings into this one (used by parallel indexing)."""
        for term, plist in other.postings.items():
            self.postings[term].extend(plist)
        self.doc_lengths.update(other.doc_lengths)
        self.num_docs += other.num_docs
