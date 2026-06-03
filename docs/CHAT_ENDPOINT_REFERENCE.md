# Chat Endpoint Reference — Automated Testing

## Endpoint

```
POST /chat/
Content-Type: application/json
```

---

## Request

```json
{
  "question": "If I close on a short-term rental late in the year, can I still get the STR tax benefits?",
  "chat_history": null
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `question` | string | ✅ | The query to evaluate |
| `chat_history` | array\|null | ❌ | Pass `null` for independent queries (each eval item is standalone) |
| `topic` | string\|null | ❌ | Optional filter e.g. `"STR Loophole"` |
| `doc_type` | string\|null | ❌ | Optional filter e.g. `"guide"` |
| `system_prompt` | string\|null | ❌ | Leave null — use the default prompt |

---

## Response

```json
{
  "answer": "Yes. You can close late in the year and still qualify...",
  "search": {
    "query": "original question text",
    "refined_query": "LLM-expanded version of the query",
    "keywords": ["str", "material", "participation", "year"],
    "results": [...],
    "total_results": 8,
    "kb_content": [...],
    "qa_results": [...]
  },
  "timing": {
    "query_refinement_ms": 420,
    "embedding_ms": 180,
    "retrieval_ms": 310,
    "answer_generation_ms": 1850,
    "total_chat_ms": 2760
  }
}
```

---

## Fields an AI Evaluation Agent Should Use

### Primary — answer quality

| Field | Path | What to check |
|-------|------|---------------|
| **Model answer** | `answer` | Is it grounded in context? Does it match the expected answer? Does it hallucinate? Does it correctly deflect when it should? |

### Secondary — retrieval quality

| Field | Path | What to check |
|-------|------|---------------|
| **All merged results** | `search.results` | Top-ranked chunks that were actually used to build the context. Check `score`, `file_type`, `document_name`, `text`/`answer` fields. |
| **Top result score** | `search.results[0].score` | Score ≥ 0.8 = strong retrieval. Score < 0.5 = weak / off-topic retrieval. |
| **Result type** | `search.results[n].file_type` | `"qa_pair"` = matched a past client Q&A. `"normal"` = matched a KB document chunk. |
| **Source document** | `search.results[n].document_name` | Verify the expected source document surfaced in top results. |
| **QA answer text** | `search.results[n].answer` | For `qa_pair` hits — this is what the model saw as context. Check if the answer to the question is actually present here. |
| **KB chunk text** | `search.results[n].text` | For `normal` hits — the raw chunk text passed as context. |
| **Keywords extracted** | `search.keywords` | Confirms the query refinement step worked correctly. |

### Diagnostic — for failures only

| Field | Path | When to use |
|-------|------|-------------|
| `search.kb_content` | raw L2 KB chunks before merge | If `results` looks weak, check if KB-only retrieval was the problem |
| `search.qa_results` | raw QA pairs before merge | If `results` looks weak, check if QA-only retrieval was the problem |
| `timing.retrieval_ms` | ms for Qdrant search | Flag if > 2000ms |
| `timing.answer_generation_ms` | ms for LLM call | Flag if > 5000ms |

---

## Verdict Logic for Evaluation Agent

```
1. Read `answer`
2. Read `search.results` — check top 3-5 chunks (score, file_type, text/answer)

IF answer is correct AND grounded in search.results:
    → PASS

IF answer is correct but search.results don't contain supporting content:
    → FLAG — model may be using training knowledge (hallucination risk)

IF answer is wrong/incomplete:
    → Check search.results:
        - If top results are irrelevant (score < 0.5 or wrong topic) → RETRIEVAL FAILURE
        - If top results are relevant but answer missed them → MODEL FAILURE

IF answer deflects ("I don't have enough information"):
    → Check search.results:
        - If results are empty or off-topic → CORRECT DEFLECTION
        - If results contain the answer → MODEL FAILURE (should have answered)
```

---

## Example — Correct Pass

```
answer: "Yes. You need at least two paid third-party stays before year-end..."

search.results[0]:
  score: 0.83
  file_type: "qa_pair"
  document_name: "McCallion, Jack and Cheryl F"
  answer: "The advisor confirms that the new short-term rental can be purchased
           at any time during the tax year... at least two stays by unrelated guests..."

→ PASS — answer is grounded in results[0].answer
```

## Example — Retrieval Failure

```
answer: "I don't have enough information on that..."

search.results[0]:
  score: 0.61
  file_type: "normal"
  document_name: "Tax Research.docx"
  text: "Under §6511 and related authority, a taxpayer has three years..."

→ RETRIEVAL FAILURE — context is off-topic; correct answer is not in KB
```
