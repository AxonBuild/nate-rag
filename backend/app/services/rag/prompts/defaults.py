from backend.app.services.rag.prompts.chat_answer import CHAT_SYSTEM_PROMPT


def get_default_system_prompt() -> str:
    return CHAT_SYSTEM_PROMPT
