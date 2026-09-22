"""
refactor_assistant.py
Orchestration layer: given a file path and an action (summarize,
refactor, docstring), reads the file, checks the cache, calls the AI
client if needed, and caches the result.

This is the module the CLI and web layer actually call - they don't
need to know about prompts, caching, or the API client directly.
"""

from indexer.walker import read_file_safely
from ai.client import AIClient, AIClientError
from ai.prompts import SYSTEM_PROMPT, PROMPT_BUILDERS, docstring_prompt
from ai.cache import ResponseCache


class RefactorAssistant:
    def __init__(self, client: AIClient = None, cache: ResponseCache = None):
        # Allow injecting a fake client/cache for testing without hitting the real API.
        self.client = client
        self.cache = cache or ResponseCache()

    def _get_client(self) -> AIClient:
        if self.client is None:
            self.client = AIClient()  # reads ANTHROPIC_API_KEY from env
        return self.client

    def run(self, file_path: str, action: str, symbol: str = None, use_cache: bool = True):
        """
        Run an AI action against a file.

        Args:
            file_path: path to the source file.
            action: one of "summarize", "refactor", "docstring".
            symbol: optional function/class name, only used for "docstring".
            use_cache: if True, return a cached response when available
                       and cache new responses.

        Returns:
            dict with keys: "file", "action", "response", "from_cache".
        """
        if action not in PROMPT_BUILDERS:
            raise ValueError(
                f"Unknown action '{action}'. Choose from: {list(PROMPT_BUILDERS)}"
            )

        source = read_file_safely(file_path)
        if source is None:
            raise FileNotFoundError(f"Could not read file: {file_path}")

        cache_key_extra = symbol or ""

        if use_cache:
            cached = self.cache.get(source, action, extra=cache_key_extra)
            if cached is not None:
                return {
                    "file": file_path,
                    "action": action,
                    "response": cached,
                    "from_cache": True,
                }

        if action == "docstring":
            prompt = docstring_prompt(file_path, source, symbol=symbol)
        else:
            prompt = PROMPT_BUILDERS[action](file_path, source)

        client = self._get_client()
        try:
            response_text = client.complete(prompt, system=SYSTEM_PROMPT)
        except AIClientError as e:
            raise AIClientError(f"Failed to {action} {file_path}: {e}") from e

        if use_cache:
            self.cache.set(source, action, response_text, extra=cache_key_extra)

        return {
            "file": file_path,
            "action": action,
            "response": response_text,
            "from_cache": False,
        }
