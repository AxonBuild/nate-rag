"""Chat turn persistence around the RAG stream."""
import logging
from typing import Any, AsyncIterator, Optional

from backend.app.infrastructure.database.session import AsyncSessionLocal
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.services.rag.search_service import SearchService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        search_service: SearchService,
        conversation_repo: Optional[ConversationRepository] = None,
    ):
        self._search = search_service
        self._repo = conversation_repo or ConversationRepository()

    async def begin_turn(
        self,
        clerk_user_id: str,
        question: str,
        conversation_id: Optional[str],
    ) -> tuple[str, list[dict[str, str]]]:
        async with AsyncSessionLocal() as session:
            if conversation_id:
                conv = await self._repo.get(session, conversation_id, clerk_user_id)
                if not conv:
                    raise ValueError("Conversation not found")
            else:
                conv = await self._repo.create(session, clerk_user_id)

            msgs = await self._repo.list_messages(session, conv.id)
            history = self._repo.messages_to_chat_history(msgs)
            await self._repo.add_message(session, conv, "user", question)
            cid = conv.id
            logger.info(
                "[chat] persisted user message conversation_id=%s history_turns=%d",
                cid,
                len(history),
            )
            return cid, history

    async def finish_turn(
        self,
        clerk_user_id: str,
        conversation_id: str,
        answer: str,
        *,
        search: Optional[dict[str, Any]] = None,
        timing: Optional[dict[str, Any]] = None,
        verification: Optional[dict[str, Any]] = None,
    ) -> None:
        meta: dict[str, Any] = {}
        if search is not None:
            meta["search"] = search
        if timing is not None:
            meta["timing"] = timing
        if verification is not None:
            meta["verification"] = verification

        async with AsyncSessionLocal() as session:
            conv = await self._repo.get(session, conversation_id, clerk_user_id)
            if not conv:
                logger.warning("[chat] finish_turn: conversation %s not found", conversation_id)
                return
            await self._repo.add_message(
                session,
                conv,
                "assistant",
                answer,
                metadata=meta or None,
            )
            logger.info(
                "[chat] persisted assistant message conversation_id=%s chars=%d",
                conversation_id,
                len(answer),
            )

    async def chat(
        self,
        *,
        question: str,
        chat_history: Optional[list[dict[str, str]]] = None,
        topic: Optional[str] = None,
        doc_type: Optional[str] = None,
        system_prompt_override: Optional[str] = None,
        retrieval_limit: Optional[int] = None,
    ) -> dict[str, Any]:
        return await self._search.chat(
            question=question,
            chat_history=chat_history,
            topic=topic,
            doc_type=doc_type,
            system_prompt_override=system_prompt_override,
            retrieval_limit=retrieval_limit,
        )

    def chat_stream(
        self,
        *,
        question: str,
        chat_history: Optional[list[dict[str, str]]] = None,
        topic: Optional[str] = None,
        doc_type: Optional[str] = None,
        system_prompt_override: Optional[str] = None,
        retrieval_limit: Optional[int] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        return self._search.chat_stream(
            question=question,
            chat_history=chat_history,
            topic=topic,
            doc_type=doc_type,
            system_prompt_override=system_prompt_override,
            retrieval_limit=retrieval_limit,
        )
