import re

ATTACHMENT_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".xlsx", ".xls",
    ".docx", ".csv", ".txt", ".zip", ".mp4", ".mov",
)

BOILERPLATE_PHRASES = [
    "this chat area will be the primary form of communication",
    "please do not create a new chat thread",
    "respond within 48 business hours",
    "good news, we have received your completed organizer",
    "good news, i have received your completed organizer",
    "we will begin preparing your taxes now",
    "i will begin preparing your taxes now",
    "just a quick update—we've officially e-filed your tax returns",
    "just a quick update—we've officially e-filed your tax returns",
    "if your return is rejected for any reason, i'll notify you directly",
    "if your return is rejected for any reason, we'll notify you directly",
    "processing times vary by agency and typically take between",
    "move onto the final review, approval, invoice, and e-signature",
]

_URL_ONLY = re.compile(r'^https?://\S+$')


def _is_attachment_only(text: str) -> bool:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return bool(lines) and all(
        any(l.lower().endswith(ext) for ext in ATTACHMENT_EXTENSIONS)
        for l in lines
    )


def _is_boilerplate(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in BOILERPLATE_PHRASES)


def _is_url_only(text: str) -> bool:
    return bool(_URL_ONLY.match(text.strip()))


def _is_duplicate(message: dict, previous: list[dict], window: int = 10) -> bool:
    text = message.get("text", "").strip()
    sender = message.get("sender", "")
    if not text:
        return False
    for prev in reversed(previous[-window:]):
        if prev.get("sender") == sender and prev.get("text", "").strip() == text:
            return True
    return False


class FilterStats:
    def __init__(self, total: int):
        self.total_before = total
        self.boilerplate = 0
        self.attachment_only = 0
        self.url_only = 0
        self.duplicate = 0
        self.skipped_messages: list[dict] = []

    @property
    def total_removed(self) -> int:
        return self.boilerplate + self.attachment_only + self.url_only + self.duplicate

    @property
    def total_after(self) -> int:
        return self.total_before - self.total_removed

    def to_dict(self) -> dict:
        return {
            "total_before": self.total_before,
            "total_after": self.total_after,
            "total_removed": self.total_removed,
            "removed_by_reason": {
                "boilerplate": self.boilerplate,
                "attachment_only": self.attachment_only,
                "url_only": self.url_only,
                "duplicate": self.duplicate,
            },
            "skipped_messages": self.skipped_messages,
        }

    def log(self) -> None:
        print(
            f"  [filter] {self.total_before} -> {self.total_after} messages "
            f"(removed {self.total_removed} -- "
            f"{self.boilerplate} boilerplate, "
            f"{self.attachment_only} attachment-only, "
            f"{self.url_only} url-only, "
            f"{self.duplicate} duplicate)"
        )


def filter_messages(messages: list[dict]) -> tuple[list[dict], FilterStats]:
    """
    Remove messages that add no knowledge value before sending to the LLM.
    Filtered categories:
      1. Boilerplate (welcome, onboarding, e-file confirmation templates)
      2. Attachment filename-only messages
      4. Exact duplicates within a 10-message window from the same sender
      7. URL-only messages

    Returns the filtered message list and a FilterStats breakdown.
    """
    stats = FilterStats(total=len(messages))
    kept: list[dict] = []
    seen_buffer: list[dict] = []

    for msg in messages:
        text = msg.get("text", "").strip()
        reason = None

        if _is_boilerplate(text):
            stats.boilerplate += 1
            reason = "boilerplate"
        elif _is_attachment_only(text):
            stats.attachment_only += 1
            reason = "attachment_only"
        elif _is_url_only(text):
            stats.url_only += 1
            reason = "url_only"
        elif _is_duplicate(msg, seen_buffer):
            stats.duplicate += 1
            reason = "duplicate"

        if reason:
            stats.skipped_messages.append({
                "reason": reason,
                "sender": msg.get("sender", ""),
                "role": msg.get("role", ""),
                "date": msg.get("date", ""),
                "text": text[:200],
            })
            continue

        kept.append(msg)
        seen_buffer.append(msg)

    return kept, stats
