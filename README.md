# Codebase Search & Refactor Assistant

A small tool that indexes a source repository with a custom **inverted
index** and **trie**, ranks search results with **BM25**, and can call an LLM API to summarize files or suggest refactors.

## Quickstart

```bash
pip install -r requirements.txt

# Build an index for a repo
python cli.py index /path/to/repo --out index.json

# Search it
python cli.py search "parse json file" --index index.json --top 5
```

Autocomplete currently needs the in-memory trie from the same indexing
run (the trie isn't persisted to disk yet — see "Next steps"):

```python
from indexer.parallel_indexer import build_index
from search.query import autocomplete

index, trie = build_index("/path/to/repo")
print(autocomplete(trie, "pars"))
```

### AI commands

Requires `ANTHROPIC_API_KEY` set in your environment and `pip install anthropic`:

```bash
export ANTHROPIC_API_KEY=sk-ant-...

python cli.py explain indexer/trie.py        # 3-5 sentence summary
python cli.py refactor indexer/trie.py       # up to 3 concrete refactor suggestions
python cli.py docstring indexer/trie.py --symbol Trie   # generate a docstring
```

Responses are cached in `.ai_cache/` keyed by the file's content hash and
the action requested, so re-running on an unchanged file costs nothing.
Pass `--no-cache` to force a fresh call, or `--api-key` to override the
environment variable.

## Design

- **`indexer/walker.py`** — walks the filesystem, skips `.git`/`node_modules`/etc.
- **`indexer/tokenizer.py`** — splits code into terms; splits `camelCase`/`snake_case`
  identifiers into sub-words so `getUserName` also matches a search for `user`.
- **`indexer/inverted_index.py`** — the core data structure: `term -> [(file, line)]`,
  plus per-file document lengths for length-normalized ranking. JSON-serializable.
- **`indexer/trie.py`** — prefix tree over extracted function/class names, for
  autocomplete-style symbol lookup.
- **`indexer/parallel_indexer.py`** — indexes files concurrently with
  `ProcessPoolExecutor`, then merges results into one index.
- **`search/ranker.py`** — BM25 scoring (a length-normalized upgrade over
  plain TF-IDF) so short files with a lucky term match don't outrank longer,
  genuinely relevant files.
- **`search/query.py`** — glues tokenizing + ranking + trie lookups into a
  simple `search()` / `autocomplete()` API.
- **`cli.py`** — command-line entrypoint (`index`, `search`, `autocomplete`,
  `explain`, `refactor`, `docstring`).
- **`ai/client.py`** — thin wrapper around the Anthropic API: retries with
  backoff, isolates SDK details from the rest of the app.
- **`ai/prompts.py`** — one function per action (summarize/refactor/docstring),
  each truncating source to a bounded size so prompts stay cheap and fast.
- **`ai/cache.py`** — on-disk cache keyed by a hash of file content + action,
  so re-running on an unchanged file never re-bills the API.
- **`ai/refactor_assistant.py`** — orchestrates read file → check cache →
  build prompt → call client → cache result. Accepts the client and cache
  via dependency injection, which is what makes `tests/test_ai_client.py`
  possible without hitting the real API or needing a key.

## Tests

`tests/` covers the inverted index (add/query/save/load/merge), the trie
(insert/prefix search), and the ranker (relevance ordering). Run with
`pytest tests/ -v` (or adapt to `unittest` if you don't want the dependency).

## Next steps (stretch goals)

1. **Web UI**: a minimal Flask/FastAPI layer over `search/query.py` and
   `ai/refactor_assistant.py`, built with accessible, keyboard-navigable,
   semantic HTML.
