"""
Hierarchical search service for nate-rag.

Two parallel tracks per query:
  1. KB docs  — L0 → L1 → L2 hierarchical drill-down (file_type="normal")
  2. QA pairs — flat single-vector search        (file_type="qa_pair")

Results from both tracks are merged by score and the top N are passed to the LLM.
"""
import asyncio
import logging
import time
from typing import Any, Optional

from backend.app.config.settings import settings
from backend.app.infrastructure.openai.embeddings import EmbeddingService
from backend.app.infrastructure.qdrant.client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, MatchAny,
    Prefetch, Fusion, FusionQuery, SparseVector,
)
from backend.app.services.rag.llm_client import LLMClient
from backend.app.services.rag.prompts.chat_answer import build_context_text
from backend.app.services.rag import chat_logging as chat_log
from backend.app.utils.errors import user_facing_message

logger = logging.getLogger(__name__)


def _payload(hit) -> dict:
    return hit.payload or {}


def _format_hits(hits) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id":      _payload(h).get("chunk_id"),
            "score":         h.score,
            "text":          _payload(h).get("text", ""),
            "level":         _payload(h).get("level"),
            "file_type":     _payload(h).get("file_type"),
            "document_name": _payload(h).get("document_name"),
            "document_id":   _payload(h).get("document_id"),
            "topic":         _payload(h).get("topic"),
            "doc_type":      _payload(h).get("doc_type"),
            "parent_id":     _payload(h).get("parent_id"),
            "prev_chunk":    _payload(h).get("prev_chunk"),
            "next_chunk":    _payload(h).get("next_chunk"),
            "page_number":   _payload(h).get("page_number"),
            # QA-specific
            "answer":        _payload(h).get("answer"),
            "tags":          _payload(h).get("tags"),
            "reasoning":     _payload(h).get("reasoning"),
        }
        for h in hits
    ]


class SearchService:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.qdrant = QdrantClient()
        self.llm = LLMClient()

    # ------------------------------------------------------------------
    # KB hierarchical track (file_type="normal")
    # ------------------------------------------------------------------

    async def _search_kb_l0(
        self,
        query_vector: list[float],
        limit: int,
        prefetch_limit: int,
        topic: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Level-0 page retrieval — plain vector search on content."""
        must = [
            FieldCondition(key="level",     match=MatchValue(value=0)),
            FieldCondition(key="file_type", match=MatchValue(value="normal")),
        ]
        if topic:
            must.append(FieldCondition(key="topic", match=MatchValue(value=topic)))
        if doc_type:
            must.append(FieldCondition(key="doc_type", match=MatchValue(value=doc_type)))

        results = await asyncio.to_thread(
            self.qdrant.client.query_points,
            collection_name=self.qdrant.collection_name,
            query=query_vector,
            using="content",
            query_filter=Filter(must=must),
            limit=limit,
            with_payload=True,
        )
        return _format_hits(results.points)

    async def _search_kb_l1(
        self,
        query_vector: list[float],
        page_chunk_ids: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Level-1 paragraph retrieval filtered to children of selected L0 pages."""
        if not page_chunk_ids:
            return []
        must = [
            FieldCondition(key="level",     match=MatchValue(value=1)),
            FieldCondition(key="file_type", match=MatchValue(value="normal")),
            FieldCondition(key="parent_id", match=MatchAny(any=page_chunk_ids)),
        ]
        results = await asyncio.to_thread(
            self.qdrant.client.query_points,
            collection_name=self.qdrant.collection_name,
            query=query_vector,
            using="content",
            query_filter=Filter(must=must),
            limit=limit,
            with_payload=True,
        )
        return _format_hits(results.points)

    async def _search_kb_l2(
        self,
        query_vector: list[float],
        paragraph_chunk_ids: list[str],
        keywords: list[str],
        limit: int,
        score_threshold: Optional[float],
        prefetch_limit: int,
    ) -> list[dict[str, Any]]:
        """Level-2 content retrieval with RRF fusion (vector + BM25) on paragraph children."""
        if not paragraph_chunk_ids:
            return []

        must = [
            FieldCondition(key="level",     match=MatchValue(value=2)),
            FieldCondition(key="file_type", match=MatchValue(value="normal")),
            FieldCondition(key="parent_id", match=MatchAny(any=paragraph_chunk_ids)),
        ]
        q_filter = Filter(must=must)

        vector_prefetch = Prefetch(
            query=query_vector,
            using="content",
            limit=prefetch_limit,
            filter=q_filter,
        )

        sparse_prefetch = None
        if keywords and settings.use_keyword_search_level2:
            kw_text = " ".join(k.strip() for k in keywords if k.strip())
            sv = await self.qdrant._generate_sparse_vector(kw_text)
            if sv:
                sparse_prefetch = Prefetch(
                    query=SparseVector(indices=sv["indices"], values=sv["values"]),
                    using="content_sparse",
                    limit=prefetch_limit,
                    filter=q_filter,
                )

        if sparse_prefetch:
            prefetch_list = [vector_prefetch, sparse_prefetch]
            try:
                results = await asyncio.to_thread(
                    self.qdrant.client.query_points,
                    collection_name=self.qdrant.collection_name,
                    prefetch=prefetch_list,
                    query=FusionQuery(fusion=Fusion.RRF),
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True,
                )
                return _format_hits(results.points)
            except Exception as e:
                logger.warning(f"L2 RRF fusion failed, falling back to vector-only: {e}")

        # Fallback: vector-only
        results = await asyncio.to_thread(
            self.qdrant.client.query_points,
            collection_name=self.qdrant.collection_name,
            query=query_vector,
            using="content",
            query_filter=q_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
        return _format_hits(results.points)

    async def _search_kb(
        self,
        query_vector: list[float],
        keywords: list[str],
        page_limit: int,
        paragraph_limit: int,
        content_limit: int,
        score_threshold: Optional[float],
        prefetch_limit: int,
        topic: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """Full KB hierarchical search: L0 → L1 → L2."""
        pages = await self._search_kb_l0(query_vector, page_limit, prefetch_limit, topic, doc_type)
        page_ids = [p["chunk_id"] for p in pages if p.get("chunk_id")]
        logger.info(f"L0 pages: {len(pages)} | IDs: {page_ids}")

        paragraphs = await self._search_kb_l1(query_vector, page_ids, paragraph_limit)
        para_ids = [p["chunk_id"] for p in paragraphs if p.get("chunk_id")]
        logger.info(f"L1 paragraphs: {len(paragraphs)}")

        content = await self._search_kb_l2(
            query_vector, para_ids, keywords, content_limit, score_threshold, prefetch_limit
        )
        logger.info(f"L2 content: {len(content)}")

        return {"pages": pages, "paragraphs": paragraphs, "content": content}

    # ------------------------------------------------------------------
    # QA pairs track (file_type="qa_pair")
    # ------------------------------------------------------------------

    async def _search_qa(
        self,
        query_vector: list[float],
        keywords: list[str],
        limit: int,
        score_threshold: Optional[float],
        topic_tags: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """3-way RRF fusion over QA pairs: question dense + answer dense + answer BM25 sparse."""
        must = [FieldCondition(key="file_type", match=MatchValue(value="qa_pair"))]
        if topic_tags:
            must.append(FieldCondition(key="tags", match=MatchAny(any=topic_tags)))
        q_filter = Filter(must=must)

        prefetch_list = [
            Prefetch(query=query_vector, using="content",        limit=limit * 2, filter=q_filter),
            Prefetch(query=query_vector, using="answer_content", limit=limit * 2, filter=q_filter),
        ]

        # Add sparse prefetch over answer text if keywords are available
        if keywords and settings.use_keyword_search_level2:
            kw_text = " ".join(k.strip() for k in keywords if k.strip())
            sv = await self.qdrant._generate_sparse_vector(kw_text)
            if sv:
                prefetch_list.append(Prefetch(
                    query=SparseVector(indices=sv["indices"], values=sv["values"]),
                    using="answer_content_sparse",
                    limit=limit * 2,
                    filter=q_filter,
                ))

        try:
            results = await asyncio.to_thread(
                self.qdrant.client.query_points,
                collection_name=self.qdrant.collection_name,
                prefetch=prefetch_list,
                query=FusionQuery(fusion=Fusion.RRF),
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )
            return _format_hits(results.points)
        except Exception as e:
            logger.warning(f"QA RRF fusion failed, falling back to question-only search: {e}")
            results = await asyncio.to_thread(
                self.qdrant.client.query_points,
                collection_name=self.qdrant.collection_name,
                query=query_vector,
                using="content",
                query_filter=q_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )
            return _format_hits(results.points)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_n_chunks(
        refinement: dict[str, Any],
        retrieval_limit: Optional[int] = None,
    ) -> int:
        """Final merged chunk cap: explicit override, else refinement, else config default."""
        if retrieval_limit is not None:
            return max(5, min(20, int(retrieval_limit)))
        n = refinement.get("number_of_chunks")
        if n is not None:
            return max(5, min(20, int(n)))
        return settings.retrieval_limit_final

    async def search(
        self,
        query: str,
        chat_history: list[dict[str, Any]] | None = None,
        topic: Optional[str] = None,
        doc_type: Optional[str] = None,
        retrieval_limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Full retrieval pipeline: refine → embed → parallel KB+QA search → merge.

        Returns a result dict with kb_content, qa_results, merged results, and timing.
        """
        start = time.time()
        timing: dict[str, float] = {}

        # 1. Query refinement
        t0 = time.time()
        refinement = await self.llm.refine_query(query, chat_history=chat_history)
        timing["query_refinement_ms"] = (time.time() - t0) * 1000
        refined_query    = refinement["refined_query"]
        keywords         = refinement["keywords"]
        n_chunks = self._resolve_n_chunks(refinement, retrieval_limit)

        chat_log.log_refinement(refinement, n_chunks, timing["query_refinement_ms"])

        # 2. Embed
        t0 = time.time()
        query_vector = await self.embedding_service.generate_embedding(refined_query)
        timing["embedding_ms"] = (time.time() - t0) * 1000

        # 3. Parallel KB + QA search
        score_threshold = settings.retrieval_min_score_final or None
        prefetch_limit  = settings.retrieval_page_prefetch_limit

        t0 = time.time()
        kb_result, qa_results = await asyncio.gather(
            self._search_kb(
                query_vector=query_vector,
                keywords=keywords,
                page_limit=settings.retrieval_limit_pages,
                paragraph_limit=settings.retrieval_limit_paragraphs,
                content_limit=n_chunks,
                score_threshold=score_threshold,
                prefetch_limit=prefetch_limit,
                topic=topic,
                doc_type=doc_type,
            ),
            self._search_qa(
                query_vector=query_vector,
                keywords=keywords,
                limit=5,
                score_threshold=score_threshold,
            ),
        )
        timing["retrieval_ms"] = (time.time() - t0) * 1000

        kb_content = kb_result["content"]

        # 4. Merge + re-rank by score, cap at n_chunks each track
        merged = sorted(
            kb_content + qa_results,
            key=lambda x: x.get("score", 0.0),
            reverse=True,
        )[:n_chunks]

        timing["total_ms"] = (time.time() - start) * 1000

        kb_n = len([r for r in merged if r.get("file_type") != "qa_pair"])
        qa_n = len([r for r in merged if r.get("file_type") == "qa_pair"])
        top = merged[0].get("score") if merged else None
        chat_log.log_retrieval(
            elapsed_ms=timing["retrieval_ms"],
            n_chunks=n_chunks,
            kb_count=kb_n,
            qa_count=qa_n,
            context_chars=0,
            top_score=top,
        )
        self._log_results(merged)

        return {
            "query":          query,
            "refined_query":  refined_query,
            "keywords":       keywords,
            "pages":          kb_result["pages"],
            "paragraphs":     kb_result["paragraphs"],
            "kb_content":     kb_content,
            "qa_results":     qa_results,
            "results":        merged,
            "total_results":  len(merged),
            "timing":         timing,
        }

    async def _finalize_answer(
        self,
        question: str,
        context_text: str,
        draft: str,
        timing: dict[str, float],
    ) -> tuple[str, dict[str, Any] | None]:
        """Verify draft against context; return final answer and optional metadata."""
        if not settings.enable_answer_verification:
            chat_log.logger.info("[chat] verification skipped (disabled)")
            return draft, None

        chat_log.logger.info(
            "[chat] phase=verifying draft_chars=%d context_chars=%d",
            len(draft),
            len(context_text),
        )
        t0 = time.time()
        verdict, attempts = await self.llm.verify_answer(
            question=question,
            context_text=context_text,
            draft_answer=draft,
        )
        timing["verification_ms"] = (time.time() - t0) * 1000
        if attempts > 1:
            timing["verification_attempts"] = attempts

        if verdict["is_correct"]:
            final = draft
        else:
            final = (verdict.get("corrected_answer") or "").strip() or draft
            chat_log.logger.info(
                "[chat] verification applied correction final_chars=%d (was draft_chars=%d)",
                len(final),
                len(draft),
            )

        meta = {
            "is_correct": verdict["is_correct"],
            "reasoning": verdict["reasoning"],
            "was_corrected": not verdict["is_correct"],
        }
        return final, meta

    @staticmethod
    def format_client_search(search_result: dict[str, Any]) -> dict[str, Any]:
        """Shape search payload for the frontend (ranked source cards)."""
        results = []
        for i, r in enumerate(search_result.get("results") or [], 1):
            row = dict(r)
            row["rank"] = i
            results.append(row)
        return {
            "refined_query": search_result.get("refined_query", ""),
            "keywords": search_result.get("keywords", []),
            "results": results,
        }

    async def chat(
        self,
        question: str,
        chat_history: list[dict[str, Any]] | None = None,
        topic: Optional[str] = None,
        doc_type: Optional[str] = None,
        system_prompt_override: Optional[str] = None,
        retrieval_limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """Retrieve context then generate a grounded answer."""
        chat_start = time.time()
        chat_log.log_request(
            mode="sync",
            question=question,
            history_len=len(chat_history or []),
            retrieval_limit=retrieval_limit,
            topic=topic,
            doc_type=doc_type,
            has_system_override=bool(system_prompt_override and system_prompt_override.strip()),
        )

        search_result = await self.search(
            query=question,
            chat_history=chat_history,
            topic=topic,
            doc_type=doc_type,
            retrieval_limit=retrieval_limit,
        )

        kb_chunks = [r for r in search_result["results"] if r.get("file_type") != "qa_pair"]
        qa_chunks = [r for r in search_result["results"] if r.get("file_type") == "qa_pair"]
        context_text = build_context_text(kb_chunks, qa_chunks)
        merged_results = search_result["results"]
        chat_log.log_retrieval(
            elapsed_ms=search_result["timing"].get("retrieval_ms", 0),
            n_chunks=len(merged_results),
            kb_count=len(kb_chunks),
            qa_count=len(qa_chunks),
            context_chars=len(context_text),
            top_score=merged_results[0].get("score") if merged_results else None,
        )

        t0 = time.time()
        draft = await self.llm.generate_answer(
            question=question,
            context_text=context_text,
            chat_history=chat_history,
            system_prompt_override=system_prompt_override,
        )
        search_result["timing"]["answer_generation_ms"] = (time.time() - t0) * 1000
        chat_log.log_generation(
            elapsed_ms=search_result["timing"]["answer_generation_ms"],
            model=self.llm.model,
            draft_chars=len(draft),
            context_chars=len(context_text),
            history_len=len(chat_history or []),
        )

        answer, verification = await self._finalize_answer(
            question=question,
            context_text=context_text,
            draft=draft,
            timing=search_result["timing"],
        )
        search_result["timing"]["total_chat_ms"] = (time.time() - chat_start) * 1000
        formatted = self.format_client_search(search_result)
        chat_log.log_complete(
            mode="sync",
            timing=search_result["timing"],
            verification=verification,
            answer_chars=len(answer),
            source_count=len(formatted.get("results") or []),
        )

        return {
            "answer": answer,
            "search": formatted,
            "timing": search_result["timing"],
            "verification": verification,
        }

    async def chat_stream(
        self,
        question: str,
        chat_history: list[dict[str, Any]] | None = None,
        topic: Optional[str] = None,
        doc_type: Optional[str] = None,
        system_prompt_override: Optional[str] = None,
        retrieval_limit: Optional[int] = None,
    ):
        """
        Async generator of SSE-style events:
          status (refining | retrieving | generating | verifying)
          done   (full answer + search + timing + verification)
          error  (message)
        """
        chat_start = time.time()
        timing: dict[str, float] = {}
        chat_log.log_request(
            mode="stream",
            question=question,
            history_len=len(chat_history or []),
            retrieval_limit=retrieval_limit,
            topic=topic,
            doc_type=doc_type,
            has_system_override=bool(system_prompt_override and system_prompt_override.strip()),
        )

        try:
            yield {"event": "status", "data": {"phase": "refining"}}
            chat_log.logger.info("[chat] phase=refining started")

            t0 = time.time()
            refinement = await self.llm.refine_query(question, chat_history=chat_history)
            timing["query_refinement_ms"] = (time.time() - t0) * 1000

            refined_query = refinement["refined_query"]
            keywords = refinement["keywords"]
            n_chunks = self._resolve_n_chunks(refinement, retrieval_limit)
            chat_log.log_refinement(refinement, n_chunks, timing["query_refinement_ms"])

            yield {"event": "status", "data": {"phase": "retrieving"}}
            chat_log.logger.info("[chat] phase=retrieving started n_chunks=%d", n_chunks)

            t0 = time.time()
            query_vector = await self.embedding_service.generate_embedding(refined_query)
            timing["embedding_ms"] = (time.time() - t0) * 1000
            chat_log.log_phase("embedding", timing["embedding_ms"])

            score_threshold = settings.retrieval_min_score_final or None
            prefetch_limit = settings.retrieval_page_prefetch_limit

            t1 = time.time()
            kb_result, qa_results = await asyncio.gather(
                self._search_kb(
                    query_vector=query_vector,
                    keywords=keywords,
                    page_limit=settings.retrieval_limit_pages,
                    paragraph_limit=settings.retrieval_limit_paragraphs,
                    content_limit=n_chunks,
                    score_threshold=score_threshold,
                    prefetch_limit=prefetch_limit,
                    topic=topic,
                    doc_type=doc_type,
                ),
                self._search_qa(
                    query_vector=query_vector,
                    keywords=keywords,
                    limit=5,
                    score_threshold=score_threshold,
                ),
            )
            timing["retrieval_ms"] = (time.time() - t1) * 1000

            kb_content = kb_result["content"]
            merged = sorted(
                kb_content + qa_results,
                key=lambda x: x.get("score", 0.0),
                reverse=True,
            )[:n_chunks]

            search_result = {
                "query": question,
                "refined_query": refined_query,
                "keywords": keywords,
                "results": merged,
                "timing": timing,
            }

            kb_chunks = [r for r in merged if r.get("file_type") != "qa_pair"]
            qa_chunks = [r for r in merged if r.get("file_type") == "qa_pair"]
            context_text = build_context_text(kb_chunks, qa_chunks)
            chat_log.log_retrieval(
                elapsed_ms=timing["retrieval_ms"],
                n_chunks=n_chunks,
                kb_count=len(kb_chunks),
                qa_count=len(qa_chunks),
                context_chars=len(context_text),
                top_score=merged[0].get("score") if merged else None,
            )
            self._log_results(merged)

            yield {"event": "status", "data": {"phase": "generating"}}
            chat_log.logger.info("[chat] phase=generating started context_chars=%d", len(context_text))

            t0 = time.time()
            draft = await self.llm.generate_answer(
                question=question,
                context_text=context_text,
                chat_history=chat_history,
                system_prompt_override=system_prompt_override,
            )
            timing["answer_generation_ms"] = (time.time() - t0) * 1000
            chat_log.log_generation(
                elapsed_ms=timing["answer_generation_ms"],
                model=self.llm.model,
                draft_chars=len(draft),
                context_chars=len(context_text),
                history_len=len(chat_history or []),
            )

            if settings.enable_answer_verification:
                yield {"event": "status", "data": {"phase": "verifying"}}

            answer, verification = await self._finalize_answer(
                question=question,
                context_text=context_text,
                draft=draft,
                timing=timing,
            )
            timing["total_chat_ms"] = (time.time() - chat_start) * 1000
            formatted = self.format_client_search(search_result)
            chat_log.log_complete(
                mode="stream",
                timing=timing,
                verification=verification,
                answer_chars=len(answer),
                source_count=len(formatted.get("results") or []),
            )
            chat_log.logger.info("[chat] emitting done event to client")

            yield {
                "event": "done",
                "data": {
                    "answer": answer,
                    "search": formatted,
                    "timing": timing,
                    "verification": verification,
                },
            }
        except Exception as e:
            logger.error("[chat] stream failed: %s", e, exc_info=True)
            yield {"event": "error", "data": {"message": user_facing_message(e, context="chat")}}

    def _log_results(self, results: list[dict[str, Any]]) -> None:
        logger.info("=" * 70)
        logger.info(f"Final merged results: {len(results)}")
        for i, r in enumerate(results, 1):
            logger.info(
                f"  [{i:2d}] score={r.get('score', 0):.4f} | "
                f"type={r.get('file_type','?'):8s} | "
                f"level={str(r.get('level','?')):>4s} | "
                f"doc={r.get('document_name','?')}"
            )
        logger.info("=" * 70)
