"""
client.py
Thin wrapper around the Anthropic API. Isolating the raw API call here
means the rest of the app (prompts, caching, orchestration) never has
to know about SDK details, retry logic, or which provider we're using.
"""

import os
import time

try:
    import anthropic
except ImportError:
    anthropic = None  # allows the rest of the app to import cleanly before `pip install anthropic`

DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2


class AIClientError(Exception):
    """Raised when the AI API call fails after all retries."""


class AIClient:
    def __init__(self, api_key: str = None, model: str = DEFAULT_MODEL):
        if anthropic is None:
            raise ImportError(
                "The 'anthropic' package is required. Install it with: "
                "pip install anthropic"
            )
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set ANTHROPIC_API_KEY or pass api_key=..."
            )
        self.model = model
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def complete(self, prompt: str, max_tokens: int = 1024, system: str = None) -> str:
        """
        Send `prompt` to the model and return the text response.
        Retries on transient failures with exponential backoff.
        """
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                kwargs = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system:
                    kwargs["system"] = system

                response = self._client.messages.create(**kwargs)
                return self._extract_text(response)

            except Exception as e:  # noqa: BLE001 - broad on purpose; SDK raises several types
                last_error = e
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        raise AIClientError(
            f"AI request failed after {MAX_RETRIES} attempts: {last_error}"
        )

    @staticmethod
    def _extract_text(response) -> str:
        """Concatenate all text blocks from the response into one string."""
        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()
