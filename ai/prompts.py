"""
prompts.py
Prompt templates for each AI-assisted action. Keeping these as plain
functions (not scattered f-strings in the orchestration code) makes
them easy to test, tweak, and version independently of the API logic.
"""

SYSTEM_PROMPT = (
    "You are a precise, concise senior software engineer assistant. "
    "You review real source code and give direct, actionable feedback. "
    "Never invent behavior the code doesn't have."
)

# Keep source snippets bounded so prompts stay cheap and fast. A full
# file summary rarely needs more than ~6000 characters of context.
MAX_SOURCE_CHARS = 6000


def _truncate(source: str) -> str:
    if len(source) <= MAX_SOURCE_CHARS:
        return source
    return source[:MAX_SOURCE_CHARS] + "\n... (truncated)"


def summarize_prompt(file_path: str, source: str) -> str:
    return (
        f"Summarize what the following file does in 3-5 sentences. "
        f"Mention its main responsibility and any notable dependencies.\n\n"
        f"File: {file_path}\n\n"
        f"```\n{_truncate(source)}\n```"
    )


def refactor_prompt(file_path: str, source: str) -> str:
    return (
        f"Review the following file and suggest up to 3 concrete refactors. "
        f"For each, give: (1) the issue, (2) a one-line fix suggestion, "
        f"(3) why it matters. Skip style nitpicks; focus on correctness, "
        f"readability, or performance.\n\n"
        f"File: {file_path}\n\n"
        f"```\n{_truncate(source)}\n```"
    )


def docstring_prompt(file_path: str, source: str, symbol: str = None) -> str:
    target = f"the function/class `{symbol}`" if symbol else "each undocumented function/class"
    return (
        f"Write a concise docstring (Google style) for {target} in the "
        f"file below. Return only the docstring(s), with a comment noting "
        f"which function each belongs to.\n\n"
        f"File: {file_path}\n\n"
        f"```\n{_truncate(source)}\n```"
    )


def explain_search_result_prompt(query: str, file_path: str, source: str, lines: list) -> str:
    line_str = ", ".join(str(l) for l in lines) if lines else "unknown"
    return (
        f"A code search for \"{query}\" matched this file most strongly "
        f"around line(s) {line_str}. In 2-3 sentences, explain why this "
        f"file is likely relevant to that query and what it does at those "
        f"lines.\n\n"
        f"File: {file_path}\n\n"
        f"```\n{_truncate(source)}\n```"
    )


PROMPT_BUILDERS = {
    "summarize": summarize_prompt,
    "refactor": refactor_prompt,
    "docstring": docstring_prompt,
}
