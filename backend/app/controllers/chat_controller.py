import json
import logging
from typing import Any, AsyncIterator

from backend.app.schemas.chat import ChatRequestSchema, ChatResponseSchema
from backend.app.services.chat_service import ChatService
from backend.app.utils.errors import user_facing_message

logger = logging.getLogger(__name__)


def _history_from_request(request: ChatRequestSchema) -> list[dict[str, str]] | None:
    if not request.chat_history:
        return None
    return [{"role": m.role, "content": m.content} for m in request.chat_history]


class ChatController:
    def __init__(self, chat_service: ChatService):
        self._chat = chat_service

    async def chat(self, request: ChatRequestSchema) -> ChatResponseSchema:
        history = _history_from_request(request)
        logger.info(
            "[chat] POST /chat/ history=%d retrieval_limit=%s",
            len(history or []),
            request.retrieval_limit,
        )
        result = await self._chat.chat(
            question=request.question,
            chat_history=history,
            topic=request.topic,
            doc_type=request.doc_type,
            system_prompt_override=request.system_prompt,
            retrieval_limit=request.retrieval_limit,
        )
        return ChatResponseSchema(
            answer=result["answer"],
            search=result["search"],
            timing=result["timing"],
            verification=result.get("verification"),
        )

    async def stream_events(
        self,
        request: ChatRequestSchema,
        clerk_user_id: str,
    ) -> AsyncIterator[str]:
        clerk_id = clerk_user_id
        try:
            conv_id, history = await self._chat.begin_turn(
                clerk_id,
                request.question.strip(),
                request.conversation_id,
            )
        except ValueError:
            yield self._sse("error", {"message": "Conversation not found"})
            return

        logger.info(
            "[chat] POST /chat/stream conversation_id=%s history=%d retrieval_limit=%s",
            conv_id,
            len(history),
            request.retrieval_limit,
        )
        try:
            async for item in self._chat.chat_stream(
                question=request.question,
                chat_history=history or None,
                topic=request.topic,
                doc_type=request.doc_type,
                system_prompt_override=request.system_prompt,
                retrieval_limit=request.retrieval_limit,
            ):
                if item["event"] == "status":
                    logger.info("[chat] sse status phase=%s", item["data"].get("phase"))
                    yield self._sse(item["event"], item["data"])
                elif item["event"] == "done":
                    data = dict(item["data"])
                    data["conversation_id"] = conv_id
                    await self._chat.finish_turn(
                        clerk_id,
                        conv_id,
                        data.get("answer") or "",
                        search=data.get("search"),
                        timing=data.get("timing"),
                        verification=data.get("verification"),
                    )
                    logger.info(
                        "[chat] sse done conversation_id=%s answer_chars=%d",
                        conv_id,
                        len(data.get("answer") or ""),
                    )
                    yield self._sse("done", data)
                elif item["event"] == "error":
                    raw = item["data"].get("message", "")
                    safe = user_facing_message(Exception(raw), context="chat")
                    logger.error("[chat] sse error %s", raw)
                    yield self._sse(item["event"], {"message": safe})
        except Exception as e:
            logger.error("[chat] stream error: %s", e, exc_info=True)
            yield self._sse("error", {"message": user_facing_message(e, context="chat")})

    @staticmethod
    def _sse(event: str, data: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
