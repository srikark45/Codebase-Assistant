"""
tokenizer.py
Splits source code text into indexable tokens: identifiers, keywords,
and words inside comments/strings. Also extracts a lighter-weight list
of "symbol" tokens (function/class/variable-style names) for the trie.
"""

import re

# Matches identifiers (letters, digits, underscore) not starting with a digit
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Splits camelCase / PascalCase / snake_case identifiers into sub-words,
# e.g. "parseJsonFile" -> ["parse", "Json", "File"], "parse_json_file" -> [...]
_CAMEL_SPLIT_RE = re.compile(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])")


def tokenize_line(line: str):
    """
    Return a list of lowercase tokens found in a single line of code.
    Splits compound identifiers into sub-words so "getUserName" also
    matches a search for "user".
    """
    tokens = []
    for match in _IDENTIFIER_RE.finditer(line):
        raw = match.group()
        for part in raw.split("_"):
            if not part:
                continue
            sub_parts = _CAMEL_SPLIT_RE.findall(part) or [part]
            tokens.extend(p.lower() for p in sub_parts)
        tokens.append(raw.lower())  # keep the whole identifier too
    return tokens


def tokenize_file(text: str):
    """
    Tokenize an entire file's text.

    Returns:
        list[tuple[int, str]]: (line_number, token) pairs, 1-indexed lines.
    """
    result = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for token in tokenize_line(line):
            result.append((line_no, token))
    return result


def extract_symbols(text: str, language_hint: str = "py"):
    """
    Extract likely function/class/method names for autocomplete (trie).
    Intentionally simple regex-based extraction, not a full parser.

    Returns:
        list[tuple[int, str]]: (line_number, symbol_name) pairs.
    """
    patterns = {
        "py": re.compile(r"^\s*(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)"),
        "js": re.compile(
            r"^\s*(?:function\s+([A-Za-z_$][\w$]*)"
            r"|const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:\(.*?\)|[\w$]+)\s*=>"
            r"|class\s+([A-Za-z_$][\w$]*))"
        ),
        "java": re.compile(
            r"^\s*(?:public|private|protected|static|\s)*"
            r"(?:class|interface)\s+([A-Za-z_][A-Za-z0-9_]*)"
        ),
    }
    pattern = patterns.get(language_hint, patterns["py"])

    symbols = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        m = pattern.match(line)
        if m:
            name = next((g for g in m.groups() if g), None)
            if name:
                symbols.append((line_no, name))
    return symbols


def language_hint_from_path(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {"py": "py", "js": "js", "ts": "js", "java": "java"}.get(ext, "py")
