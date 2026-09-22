#!/usr/bin/env python3
"""
cli.py
Command-line entrypoint.

Usage:
    python cli.py index /path/to/repo [--out index.json] [--workers 4]
    python cli.py search "parse json" [--index index.json] [--top 10]
    python cli.py autocomplete "pars" [--index index.json]
    python cli.py explain path/to/file.py
    python cli.py refactor path/to/file.py
    python cli.py docstring path/to/file.py [--symbol my_function]

The `explain`/`refactor`/`docstring` commands require ANTHROPIC_API_KEY
to be set in your environment (or passed via --api-key), and the
`anthropic` package installed (`pip install anthropic`). Responses are
cached in `.ai_cache/` keyed by file content, so re-running on an
unchanged file won't re-call the API.

Note: `search` and `autocomplete` currently rebuild the trie/index from
the saved JSON for search, but the trie itself isn't persisted yet
(see README "Next steps") — for now, run `index` and `search` in the
same process via the Python API, or persist the trie the same way
InvertedIndex.save/load works.
"""

import argparse
import sys

from indexer.parallel_indexer import build_index
from indexer.inverted_index import InvertedIndex
from search.query import search, autocomplete
from ai.refactor_assistant import RefactorAssistant
from ai.client import AIClient, AIClientError


def cmd_index(args):
    print(f"Indexing {args.path} with {args.workers} worker(s)...")
    index, trie = build_index(args.path, max_workers=args.workers)
    index.save(args.out)
    print(f"Indexed {index.num_docs} file(s), {len(index.postings)} unique term(s).")
    print(f"Saved index to {args.out}")
    # Trie is in-memory only for now; see docstring above.
    return index, trie


def cmd_search(args):
    index = InvertedIndex.load(args.index)
    results = search(index, args.query, top_k=args.top)

    if not results:
        print("No matches found.")
        return

    for r in results:
        lines = ", ".join(str(l) for l in r["lines"])
        print(f"{r['score']:.3f}  {r['file']}  (lines: {lines})")


def cmd_autocomplete(args):
    print("Autocomplete requires an in-memory trie from the current indexing run.")
    print("Run index + autocomplete together via the Python API for now, e.g.:")
    print('  from indexer.parallel_indexer import build_index')
    print('  from search.query import autocomplete')
    print('  index, trie = build_index("/path/to/repo")')
    print(f'  print(autocomplete(trie, "{args.prefix}"))')


def cmd_ai_action(args, action):
    client = None
    if args.api_key:
        client = AIClient(api_key=args.api_key)

    assistant = RefactorAssistant(client=client)
    symbol = getattr(args, "symbol", None)

    try:
        result = assistant.run(
            args.file, action, symbol=symbol, use_cache=not args.no_cache
        )
    except (FileNotFoundError, ValueError, AIClientError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    tag = " (cached)" if result["from_cache"] else ""
    print(f"--- {action}{tag}: {result['file']} ---\n")
    print(result["response"])


def main():
    parser = argparse.ArgumentParser(description="Codebase search & AI refactor assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_index = subparsers.add_parser("index", help="Build an index for a repository")
    p_index.add_argument("path", help="Path to the repository root")
    p_index.add_argument("--out", default="index.json", help="Output path for the saved index")
    p_index.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    p_index.set_defaults(func=cmd_index)

    p_search = subparsers.add_parser("search", help="Search a previously built index")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--index", default="index.json", help="Path to saved index")
    p_search.add_argument("--top", type=int, default=10, help="Number of results to show")
    p_search.set_defaults(func=cmd_search)

    p_auto = subparsers.add_parser("autocomplete", help="Symbol autocomplete (see notes)")
    p_auto.add_argument("prefix", help="Symbol name prefix")
    p_auto.add_argument("--index", default="index.json", help="Path to saved index")
    p_auto.set_defaults(func=cmd_autocomplete)

    def add_ai_flags(subparser):
        subparser.add_argument("file", help="Path to the source file")
        subparser.add_argument("--api-key", default=None, help="Override ANTHROPIC_API_KEY")
        subparser.add_argument(
            "--no-cache", action="store_true", help="Skip the response cache"
        )

    p_explain = subparsers.add_parser("explain", help="Summarize a file using AI")
    add_ai_flags(p_explain)
    p_explain.set_defaults(func=lambda a: cmd_ai_action(a, "summarize"))

    p_refactor = subparsers.add_parser("refactor", help="Get AI refactor suggestions for a file")
    add_ai_flags(p_refactor)
    p_refactor.set_defaults(func=lambda a: cmd_ai_action(a, "refactor"))

    p_doc = subparsers.add_parser("docstring", help="Generate a docstring for a file/symbol")
    add_ai_flags(p_doc)
    p_doc.add_argument("--symbol", default=None, help="Specific function/class name")
    p_doc.set_defaults(func=lambda a: cmd_ai_action(a, "docstring"))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
