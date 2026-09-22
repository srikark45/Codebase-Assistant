"""
trie.py
A prefix tree over symbol names (function/class names) for fast
autocomplete: "pars" -> ["parse_json", "parse_args", ...].
"""


class TrieNode:
    __slots__ = ("children", "locations", "is_end")

    def __init__(self):
        self.children = {}
        self.locations = []  # list of (file, line) where this exact symbol occurs
        self.is_end = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, symbol: str, file: str, line: int):
        """Insert a symbol name (case-insensitive) with its source location."""
        node = self.root
        for ch in symbol.lower():
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True
        node.locations.append((file, line))

    def _find_node(self, prefix: str):
        node = self.root
        for ch in prefix.lower():
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def starts_with(self, prefix: str, limit: int = 10):
        """
        Return up to `limit` (symbol, [(file, line), ...]) pairs whose
        symbol name starts with `prefix`.
        """
        node = self._find_node(prefix)
        if node is None:
            return []

        results = []
        self._collect(node, prefix.lower(), results, limit)
        return results

    def _collect(self, node: TrieNode, prefix: str, results: list, limit: int):
        if len(results) >= limit:
            return
        if node.is_end:
            results.append((prefix, node.locations))
        for ch, child in sorted(node.children.items()):
            if len(results) >= limit:
                break
            self._collect(child, prefix + ch, results, limit)

    def contains(self, symbol: str) -> bool:
        node = self._find_node(symbol)
        return node is not None and node.is_end
