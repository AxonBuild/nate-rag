"""Safe error messages for API/SSE responses (full detail stays in logs)."""

import re

_TECHNICAL = re.compile(
    r"getaddrinfo|errno\s*\d+|\[errno|econnrefused|enotfound|eai_again|"
    r"traceback|exception:|socket|ssl|certificate|failed to fetch",
    re.I,
)


def user_facing_message(exc: BaseException, *, context: str = "chat") -> str:
    raw = str(exc).strip()
    lower = raw.lower()

    if "conversation not found" in lower:
        return "Conversation not found"

    if any(
        x in lower
        for x in (
            "getaddrinfo",
            "enotfound",
            "econnrefused",
            "connection refused",
            "timed out",
            "timeout",
        )
    ):
        return (
            "Couldn't reach a required service. Please try again."
            if context == "chat"
            else "Couldn't complete the request. Please try again."
        )

    if any(x in lower for x in ("openai", "openrouter", "rate limit", "insufficient_quota")):
        return "The AI service is temporarily unavailable. Please try again shortly."

    if raw and not _TECHNICAL.search(raw) and len(raw) < 200:
        return raw

    if context == "chat":
        return "We couldn't complete your question. Please try again."
    return "Something went wrong. Please try again."
