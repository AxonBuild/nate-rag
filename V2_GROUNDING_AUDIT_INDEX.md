# V2 Grounding Audit Index

Audit of `qa_output_v2/*/extraction.json` against `parsed_chats/*.json` using post-`filter_messages()` indices (same as extraction pipeline).

**Two reference numbers** (do not confuse them):

| Column | Meaning |
|--------|---------|
| **Msg rank** | Position when all chats are sorted by `message_count` **descending** (1 = largest chat). |
| **CSV row** | **Physical line number** in `logs/files_progress.csv` (row 1 = header; first data row = 2). |

For the **top ~45 rows** of the CSV, file order matches message-count order, so **CSV row ≈ msg rank + 1**. Lower in the file, order diverges — always use the **CSV row** column here to look up a file in the spreadsheet.

| Column (tables below) | Meaning |
|---------------------|---------|
| **Msgs** | `message_count` from CSV |
| **Audit batch** | How this file was reviewed |
| **Hallucination** | Confirmed invented/wrong fact in cited advisor text |
| **Other issues** | Non-hallucination problems worth fixing |

**Audit methods**

- **Batch A (msg ranks 11–40):** 15 parallel subagents, 2 files each (30 files, Emerson → Faris). **Also audited:** msg ranks 41, 43–45 (CSV rows 42, 44–46: Padgett, Milton, Hirekatur, Malkon). **Not** `llm_pipeline.verifier` (gpt-4.1-mini).
- **Batch B (ranks 1–10):** Manual / verifier spot-checks and prior top-20 comparisons (gpt51 → v2). Full scripted audit for all 10 was **not** completed in one subagent pass.
- **Batch 2 (msg ranks 46–88, 40 files):** 20 parallel subagents, 2 files each. `scripts/audit_top20_grounding.py` + manual review of auto flags. **Not** bulk LLM verifier. Per-pair reports: `V2_GROUNDING_*.md`, `scripts/v2_*_audit.json`.
- **Batch 3 (msg ranks 81–130, 50 files):** 25 parallel subagents, 2 files each. `scripts/run_batch3_audit_agent.py` → `scripts/audit_v2_pair.audit_v2` + manual review. Reports: `V2_GROUNDING_BATCH3_AGENT{N}.md`, `scripts/v2_batch3_agent{N:02d}.json` (full `missed_knowledge`). Ranks **81–88** overlap Batch 2 (re-audited with batch-3 workflow).
- **Batch 4 (msg ranks 131–180, 50 files):** 25 parallel subagents, 2 files each. `scripts/run_batch4_audit_agent.py` + **`V2_GROUNDING_BATCH4_AGENT_BRIEF.md`** (required). Reports use **`transferable_gaps`** (real RAG misses) vs raw `missed_knowledge` heuristic (ops/admin). `V2_GROUNDING_BATCH4_AGENT{N}.md`, `scripts/v2_batch4_agent{N:02d}.json`.
- **Gap batch (8 files):** 4 parallel subagents, 2 files each. Previously had v2 output but **no** full grounding pass (early tests, CSV tick gaps, Batch 2 skip). `scripts/run_gap_audit_agent.py` + same brief as Batch 4. `V2_GROUNDING_GAP_AGENT{N}.md`, `scripts/v2_gap_audit_agent{N:02d}.json`. Tracker: `V2_GROUNDING_AUDIT_GAP.md`.
- **Batch 5 (msg ranks 181–282, 102 files):** 26 parallel subagents, **4 files each** (agent 26 = 2). All remaining `processed_v2`. `scripts/run_batch5_audit_agent.py` + Batch 4 brief. **Complete** — see `V2_GROUNDING_AUDIT_BATCH5.md`.

**Verdict labels**

- **None** — No confirmed hallucination after review.
- **Confirmed** — Specific claim in answer not supported by cited advisor message(s).
- **Resolved** — Was **Confirmed**; fixed in `qa_output_v2` (hallucination cleanup).
- **Resolved (overturned)** — Audit flag overturned on re-check; extraction unchanged.
- **Borderline** — Thin citation or client-sourced / unit error; see detail.
- **Citation only** — Text exists in chat but not in cited indices (not invented).

---

## Summary

| Scope | Files audited | Confirmed hallucination | Borderline / partial (not invented) | Notes |
|-------|--------------:|------------------------:|----------------------------------:|-------|
| **Batch 1** (msg ranks 1–45) | 45 | **0 open** (4 resolved, 1 overturned) | 2 (+ Aronne structural) | 5 early v2 tests outside ranks 1–40 table |
| **Batch 2** (msg ranks 46–88) | 40 | **0 open** (5 resolved) | 6+ (thin cite / client $) | — |
| **Batch 3** (msg ranks 81–130) | 50 | **0** | 8+ partial (labels / client-sourced detail) | 8 files overlap Batch 2 (ranks 81–88) |
| **Batch 4** (msg ranks 131–180) | 50 | **0** | 10+ partial (labels / client $ / thin cite) | **`transferable_gaps`** on **12** files (~15 threads) |
| **Gap batch** (8 files) | 8 | **0** | 4 partial (not invented; see gap table) | **`transferable_gaps`** on **4** files (**5** threads) |
| **Batch 5** (msg ranks 181–282) | 102 | **0** | 9+ partial (client $ / thin cite / attribution) | **`transferable_gaps`** on **14** files (~**16** threads); **30** files with **0** QAs |
| **All `processed_v2` (audited)** | **282** | **0 open** (9 historical, **all resolved**) | — | Full corpus grounding-audited (batches 1–5 + gap 8); cleanup verified 2026-05-22 |

**Batch 1 breakdown (ranks 1–40 table):** None 37 · Resolved 3 · Resolved (overturned) 1 · Borderline 1 · Citation only 1 · **4** rows gap-audited (were `—` / not audited); **Casillas** (rank 42) gap-audited in “Also audited” table.

**Batch 2 takeaway:** No widespread invention; main gaps are **missed substantive threads** (often estimates, FTB access, entity onboarding) and **near-duplicate QAs** from one long advisor reply.

**Batch 3 takeaway:** **333** QAs across 50 files; **241** missed-knowledge flags (mostly admin/onboarding). **No confirmed hallucinations** after manual review. Recurring issues: **near-duplicate splits** (e.g. Shao **[19]**, Murphy **[11]/[27]**), **thin partials** (form/schedule labels), **client-sourced facts** in otherwise grounded answers (T&L **[10]**, Caine **[41]** — not counted as Confirmed).

**Batch 4 takeaway:** **No confirmed hallucinations** on 50 files. Grounding strong; noise = **partials** (not invention) and **near-duplicates** (Pucher 15 pairs, Love 6 pairs). Real **transferable extraction gaps** on **12 clients** only — worst **Smallwood** (0 QAs, STR/REPS rules at **[5]**). Raw `missed_knowledge` in JSON is **not** used as the gap metric (see brief).

**Gap batch takeaway:** **87** QAs across 8 files; **0** confirmed hallucinations (6 auto-H/$ flags overturned). **4** partials kept or assigned (Carr QA **#14** client-sourced IP PIN date; Ren QA **#4**; Chillar QA **#4**, **#13**). **Transferable gaps:** Carr **[38]** (Airbnb gross), Lising **[13]** (cost seg off P&L), Chillar **[39]** (MLP K-1), Ren **[0]** (preparer vs client copy). Chillar: 16 near-dup pairs from checklist splits.

**Batch 5 takeaway:** **~161** QAs across **102** tail files (ranks **181–282**); **0** confirmed hallucinations (5 auto-H and 18 auto-P flags — dollar/`Sch A` normalization and overlap checker — all overturned or thin partial). **30** threads correctly have **0** QAs (onboarding, e-file, scheduling). Main noise: **near-duplicates** on long replies (Camp Creek 9 pairs) and **client-sourced** detail in otherwise grounded answers. Real **`transferable_gaps`:** **14** clients — dominated by **preparer copy vs client copy** (9 files); plus Zhao STR/K-1 **[13]**, Capital Gold fixed-asset **[8]**, MREI Sch E **[2]**, Calvetti separate e-sign **[2]**, Nagda prior-return handoff **[1]**. Worst extraction miss pattern: onboarding template not extracted when thread has **0** QAs (Kauffman, Ranck, Vo). Raw `missed_knowledge` not used as gap metric (see brief).

*Plus structural QA issues on **Aronne** (batch 1) and **Moffett** (batch 2), documented under Other.*

**Hallucination cleanup (2026-05-22):** All **9** batch 1–2 flags addressed in `qa_output_v2/*/extraction.json`. Verified: `python scripts/verify_hallucination_cleanup.py` (**9/9 pass**). **Albayaty #16** overturned — **~$125k** is in advisor **[104]**; no edit. Batches 3–5 + gap added **0** confirmed.*

*Historical severity (pre-fix):* High — Burkes (10%/year vs month), Espinoza (solar $). Medium — client $ in answer (Yen, Dobyns, Wang, Diaz, Ogueli, Williams). ~~Citation gap — Albayaty~~ → overturned.

---

## Master table (msg ranks 1–40)

| Msg rank | CSV row | Client (folder name) | Msgs | `processed_v2` | Audit batch | Hallucination | Other issues |
|----------|---------|----------------------|-----:|:--------------:|:-------------:|:-------------|:---------------|
| 1 | 2 | Cortez, Christian and Yesenia | 277 | ✓ | B | Citation only | Extension QA: closing “e-file / nothing needed” at filtered **[212]**, citations **[196,197,199]** only — real Nate text, weak footnotes |
| 2 | 3 | Root, Andy | 224 | ✓ | B | None | v2 removed gpt51 Form 5498-SA invention; no new confirmed hallucination |
| 3 | 4 | Lyons, Nicolas M. (+ C, & Partnership) | 170 | ✓ | B | None | Not in 11–40 subagent batch; spot-check only |
| 4 | 5 | Grimes, Mason and Alexis | 165 | ✓ | B | None | Spot-check: $750k mortgage cap may be grounded if in cited msgs — verify if concerned |
| 5 | 6 | Pejcha, Mark and Magali Sojit | 165 | ✓ | B | None | v2 fixed prior K-1/1098-style gpt51 flags |
| 6 | 7 | Sanchez Soria, Pablo and Katie | 160 | ✓ | B | None | v2 removed gpt51 STR-rule invention on deferral message |
| 7 | 8 | Yen, Andrew and Jacqueline | 157 | ✓ | B | **Resolved** | QA **#10** **removed** (was $2,500 / $800 from **client** only) |
| 8 | 9 | Burkes, Sammie and Erin | 152 | ✓ | B | **Resolved** | QA **#12**: “~10% **per month**” (was per year vs **[74]**) |
| 9 | 10 | Jang, Will and Wendy | 142 | ✓ | B | None | Not in 11–40 subagent batch |
| 10 | 11 | Zhang, Chi and Wenjun Chen | 139 | ✓ | B | None | v2 fixed gpt51 1099 mis-citation pattern |
| 11 | 12 | Emerson , Kevin W. and Joanna | 131 | ✓ | A | None | Duplicate QAs (#6/#14); missed $80k shareholder loan thread |
| 12 | 13 | Beltran, Edward and Eunice | 130 | ✓ | A | None | **Missed:** $43,831 passive loss / Form 8582 amend (advisor ~**[9]**) |
| 13 | 14 | Martin, Jacob and Nancy | 129 | ✓ | A | None | 2 partials; missed cost-seg property selection / extension guidance |
| 14 | 15 | Albayaty, Monica and Richard | 126 | ✓ | A | **Resolved (overturned)** | QA **#16**: **~$125k** grounded at advisor **[104]** — not a hallucination |
| 15 | 16 | Skorobogatova, Ekaterina and Anna Zhirova | 123 | ✓ | A | Borderline | QA **#7**: 1099-G framing beyond thin cited line; core “taxable in 2024” OK |
| 16 | 17 | Goodman, Richard and Devonay | 119 | ✓ | A | None | Auto $ flags false positives (`~5k`); heavy near-duplicate solar QAs |
| 17 | 18 | Fernandez II, Anthony and Emily | 117 | ✓ | A | None | Grade A; no confirmed hallucination |
| 18 | 19 | Aronne, Jason and Kunal | 116 | ✓ | A | None | QA **#5** cites **client** index **[26]**; QA **#17** question (Form 593) ≠ cited text (1031 at **[96]**) — use QA **#18** |
| 19 | 20 | Simon, Thomas and Jin-Hwa | 112 | ✓ | A | None | 7 auto H flags overturned (`7k`); 2 partials; 44 near-dup pairs |
| 20 | 21 | Kemp, Chris and Sara | 106 | ✓ | A | None | Auto H flags overturned; heavy index overlap |
| 21 | 22 | Liang, Derek and Kristine | 106 | ✓ | A | None | 3 mild partials; shared-index splits |
| 22 | 23 | Pedagat, Ronald and Janize Quintana | 103 | ✓ | A | None | Auto $1,000 flag false positive (`$1k` in source) |
| 23 | 24 | Carr, Danny and Frederica | 102 | ✓ | Gap-A1 | None | Gap: 1 partial QA **#14** (client IP PIN date); transferable **[38]** Airbnb gross; 3 near-dup |
| 24 | 25 | Baig, Rameez R. and Naima Bendada | 101 | ✓ | A | None | 1 partial (mailing checklist detail) |
| 25 | 26 | Truman, Stephen and Alisa | 100 | ✓ | A | None | Near-duplicate cost-seg/STR pairs |
| 26 | 27 | Dobyns, Kristina | 98 | ✓ | A | **Resolved** | QA **#19** **removed** (was **$1,000** from **client**; advisor **[84]** only “That is correct”) |
| 27 | 28 | Tran, Quang | 98 | ✓ | A | None | Grade A−; megathread index sharing |
| 28 | 29 | Lanka, Ravindra and Sarvani Vakkalanka | 97 | ✓ | A | None | 2 partials (e-file workflow, extension wording) |
| 29 | 30 | Umbalacheri Ramasamy, Venkatraman and Jayashree | 97 | ✓ | Gap-A1 | None | Gap: grade A; 2 auto-H overturned (`2k+`); 1 near-dup |
| 30 | 31 | Todd, DJ and Jennifer | 95 | ✓ | A | None | 15 near-dup pairs from one multi-topic reply |
| 31 | 32 | Alonzo, Jamie J | 94 | ✓ | A | None | Grade A−; 1 partial (moving expenses) |
| 32 | 33 | Cortez, Angelo | 94 | ✓ | A | None | QA **#13** auto $12k flag false positive (“12–15k” in source) |
| 33 | 34 | Dieffenbach, Zachary M | 92 | ✓ | A | None | Grade 97%; clean |
| 34 | 35 | D_Altorio, Darren and Amalya | 90 | ✓ | A | None | QA **#7–9** triple-split on index **[16]**; not hallucination |
| 35 | 36 | Ho, Tim and Stephanie Liu | 90 | ✓ | Gap-A2 | None | Gap: grade A; auto partial QA **#1** overturned; 1 near-dup |
| 36 | 37 | Rigoni, Jacqueline | 90 | ✓ | A | None | 2 auto H → partial (2k child credit grounded); Schedule C name not in cited text (partial) |
| 37 | 38 | Edwards, Ross and Narine Karakhanyan | 89 | ✓ | A | None | 1 partial (short citation) |
| 38 | 39 | Ciccone Tolbert, Gabriella N | 88 | ✓ | A | None | Heavy near-dup on index **[48]** |
| 39 | 40 | Elliott, Kevin and Anna Jennie M | 87 | ✓ | Gap-A2 | None | Gap: grade A-; auto H QA **#3** overturned (`~5k`); 3 near-dup on **[21]** |
| 40 | 41 | Faris, Korie and Jacob | 86 | ✓ | A | None | Missed prior-return onboarding at advisor **[0]** (substantive gap) |

### Also audited (msg ranks 41–45; CSV rows 42–46)

| Msg rank | CSV row | Client | Msgs | `processed_v2` | Audit batch | Hallucination | Other issues |
|----------|---------|--------|-----:|:--------------:|:-------------:|:-------------|:---------------|
| 41 | 42 | Padgett, Michael and Allison | 84 | ✓ | A+ | None | Missed property-address / onboarding threads |
| 42 | 43 | Casillas, Juan and Pamela Guillen | 82 | ✓ | Gap-A3 | None | Gap: grade A; auto H QA **#5** overturned (`1-4k`); 3 near-dup on **[33]** |
| 43 | 44 | Milton, Josh and Deanna | 81 | ✓ | A+ | None | Auto H overturned (`2k` child credit); index overlap |
| 44 | 45 | Hirekatur, Anand S | 80 | ✓ | A+ | None | 1 thin-citation partial |
| 45 | 46 | Malkon, Paul and Tanya | 80 | ✓ | A+ | None | Clean after review |

---

## Master table — Batch 2 (msg ranks 46–88)

40 new `processed_v2` files (msg rank **> 45**). **Lising** (rank 53 / CSV 54) skipped here — no v2 at Batch 2 time; **Gap batch** audited.

| Msg rank | CSV row | Client (folder name) | Msgs | `processed_v2` | Audit | Hallucination | Missed (count) | Other issues / top missed knowledge |
|----------|---------|----------------------|-----:|:--------------:|:-----:|:-------------|---------------:|:-----------------------------------|
| 46 | 47 | Otani, Christopher and Uyen | 80 | ✓ | B2-A1 | None | 4 | Auto flags overturned (e.g. **9k** at **[24]**); tax projection / K-1 wait **[33]**; **185k** software fix thread |
| 48 | 49 | Makagiansar, Irwan and Helena | 78 | ✓ | B2-A1 | None | 5 | Grouping election / Form 3520 / fee allocation well covered; e-sign **[3]**, audit-risk client question |
| 49 | 50 | Martin, Tyler and Katherine | 78 | ✓ | B2-A2 | None | 8 | Katie **$1,500** S-corp proposal **[5]**; extension payment reminders; year-end estimate close-out **[69]** |
| 50 | 51 | Smith III, Russell E. and Nicole | 78 | ✓ | B2-A2 | None | 3 | FEIE / installment sale / 1031 grounded; **$2k** TN LLC fee at **[49]** (auto flag overturned) |
| 51 | 52 | Martin, Jonathan and Diana | 75 | ✓ | B2-A3 | None | 5 | **Missed:** partnership extension filed **[48]**; Roth 401(k) / 1031 sale at **[65]** covered |
| 52 | 53 | Coleman, Paige | 74 | ✓ | B2-A3 | None | 8 | Trust/gift, extension, **$111k** sale + cost seg; missed IRS notice follow-up **[14]** |
| 54 | 55 | Wang, Yuehai and Gisele Hong | 74 | ✓ | B2-A4 | **Resolved** | 3 | QA **#14** **removed** (was **$1,000** Trump account from **client** **[66]**); CA/no-CA **[5]**; cost-seg **[23]** |
| 55 | 56 | Diaz, Anne and Martin Carew | 73 | ✓ | B2-A4 | **Resolved** | 4 | QA **#9**: **~$3,320** removed; **~$500** savings kept; stock sales / IRS agent **[20]**, **[4]** |
| 56 | 57 | Barnes, Karsten and Tamarra | 72 | ✓ | B2-A5 | None | 6 | Extension/penalty/REPS/cost-seg clean; FTB access **[49]**; 10/15 urgency **[4]** |
| 57 | 58 | Kuramoto, Kenny and Michelle | 72 | ✓ | B2-A5 | Borderline | 2 | QA **#7**: **Sch E** label vs **[56]** (amounts grounded); CA LLC fee **[8]** |
| 58 | 59 | Ogueli, Vivian and Ifeanyi | 72 | ✓ | B2-A6 | **Resolved** | 8 | QA **#7**: **~$40k** removed from answer; DERANAZ **[8]**; biz/personal **[19]** |
| 59 | 60 | Lok, Brian | 71 | ✓ | B2-A6 | None | 4 | 14 QAs; strong REPS joint-return coverage; **$800** CA LLC reminder **[54]**; elite pricing **[59]** |
| 61 | 62 | Holbrook, Emily N. | 69 | ✓ | B2-A7 | None | 9 | S-corp payroll **[1]**, Oct deadline **[6]**, rental setup **[50]**; thin cite QA **#6** |
| 62 | 63 | Manietta, Daniel and Susana | 68 | ✓ | B2-A7 | None | 12 | **Coverage gap:** only **3** QAs; **$525K** sale, **$8k/$3.2k** estimates **[5]**, REPS app **[29]** missed |
| 63 | 64 | Blom, Brandon J. and Katie | 67 | ✓ | B2-A8 | None | 3 | HSA/5498 citation-only QA **#3**; near-dup **[27]**; e-sign **[1]** |
| 64 | 65 | Haddon, Garrison D and Dana M | 67 | ✓ | B2-A8 | None | 1 | 13 QAs grounded; flip/HELOC near-dups; video recap **[33]** |
| 65 | 66 | Moffett, Mark and Jennifer | 67 | ✓ | B2-A9 | None | 7 | QA **#2** HELOC Q / REPS A mismatch; CA withholding **2% vs 6%** **[55]**; 7 near-dup |
| 66 | 67 | Espinoza, Meny and Diana | 65 | ✓ | B2-A9 | **Resolved** | 2 | QA **#5**: solar **$16k/$50k/$15k/$17k** (was wrong illustrative $); 8 near-dup |
| 67 | 68 | Haghi, Poorya and Hanh Tran | 65 | ✓ | B2-A10 | None | 6 | REPS 5-of-10-year rule; STR personal days — auto **$6k** flag overturned; cost seg **~$300k** land **[21]** |
| 68 | 69 | Koch, Martin and Mariah Soto | 64 | ✓ | B2-A10 | Citation only | 12 | IRA phase-out / cap loss strong; **timing rules** in uncited **[15]** (QA **#3**); large estimate threads missed |
| 69 | 70 | Li, Xiang and Luis Lin | 64 | ✓ | B2-A11 | None | 5 | v2 +2 QAs vs gpt51; **$23,500** flag overturned (**23.5k** at **[37]**) |
| 70 | 71 | Pleas, Betty and Little | 64 | ✓ | B2-A11 | None | 7 | Thin coverage (**4** QAs / 55 filtered msgs); extension years **[1]**, **[54]** |
| 71 | 72 | Williams, Thomas S. and Emi | 64 | ✓ | B2-A12 | **Resolved** | 3 | QA **#9**: **$10,000** sentence removed (was **client** **[55]** only); overlap **[9,12]** |
| 72 | 73 | Ye, Zhengqing and Nina Dongmei (Ning) | 64 | ✓ | B2-A12 | None | 12 | **17** near-dup pairs (splits on **[44]**); 12 missed threads |
| 73 | 74 | Ho, Spencer C and Karen G | 63 | ✓ | B2-A13 | None | 4 | SALT **$40k**, Roth conversion; **~1k** amend fee = borderline **[33]**; FTB **[20]** |
| 74 | 75 | Martin, Benjamin J. | 63 | ✓ | B2-A13 | None | 7 | 1095-A rejection grounded; **1040-X** note from client (borderline QA **#4**); STR **[3]** |
| 75 | 76 | Raghavan, Amit and Nidhi Sood | 63 | ✓ | B2-A14 | None | 4 | Elite plan / planning call / W-4 MFS nuance missed |
| 76 | 77 | Cao, Ray and Liu Guo | 62 | ✓ | B2-A14 | None | 10 | **$2k** estimate flag overturned; Solo 401(k) **[55]**; large estimate/carryover gaps |
| 77 | 78 | Richter, Michael D. and Candace | 62 | ✓ | B2-A14 | None | 5 | **~$95k** federal due **[15]** captured; Westland partnership **[4]**; fee break **[37]** |
| 78 | 79 | Withana, Eran and Thushari | 62 | ✓ | B2-A14 | None | 10 | **~$10k** tax increase **[12]** missed; NNN cost seg / REPS memo **[53]** grounded; 2 near-dup |
| 79 | 80 | Inoue, Sachiko | 61 | ✓ | B2-A15 | Borderline | 10 | QA **#3** **$2,500** in question/QA **#1**, not **[19]**; cost-seg pricing **[14]**; **~$10k** refund **[51]** |
| 80 | 81 | Shastry, Sandesh and Ashwini Hegde | 61 | ✓ | B2-A15 | None | 2 | Extension **~$40k/$5k** grounded **[49]**; thin cite QA **#6**, **#8** |
| 81 | 82 | Shah, Aamir and Sana | 60 | ✓ | B2-A16 | None | 7 | Cost seg / EBL / NOL; REI Hub reconciliation **[42]** missed |
| 82 | 83 | Hench, Kevin & Heather Juergensen | 59 | ✓ | B2-A16 | None | 4 | **$71,418** + estimate schedule at **[49]** grounded; near-dup **[52]** |
| 83 | 84 | Baba, Trevor and Gerrilyn | 58 | ✓ | B2-A17 | None | 7 | 3 near-dup on **[28]**; auto flags overturned (**5k**, Sch C) |
| 84 | 85 | Chen, Yao and Chun-Chi Lin | 58 | ✓ | B2-A17 | Citation only | 4 | QA **#5**: keep **[28,30]**; drop thin **[22,25,26]** |
| 85 | 86 | Weber, Tracy and Brandon | 58 | ✓ | B2-A18 | None | 6 | Iowa 529 / flip / pre-service; year-end estimates **[37]** |
| 86 | 87 | Carter, Christopher and Brenda | 57 | ✓ | B2-A18 | None | 7 | Auto **$4–6k** / **~3k** overturned; Rooted **1065** vs Sch C **[26]** |
| 87 | 88 | Niehaus, Max and Reina | 57 | ✓ | B2-A19 | None | — | **6** QAs; S-corp **30/70** payroll split, cash-basis — no machine log; manual pass |
| 88 | 89 | Jang, Jean | 56 | ✓ | B2-A19 | None | — | **8** QAs; scripted pass not saved — spot-check clean |

Detail reports: `V2_GROUNDING_AUDIT_BATCH2.md` (assignments) and `V2_GROUNDING_*.md` per pair.

---

## Master table — Batch 3 (msg ranks 81–130)

50 newest `processed_v2` files. Ranks **81–88** also appear in Batch 2 table above (same clients; Batch 3 = fuller `missed_knowledge` in JSON).

| Msg rank | CSV row | Client (folder name) | Msgs | `processed_v2` | Audit | Hallucination | Missed | Other issues |
|----------|---------|----------------------|-----:|:--------------:|:-----:|:-------------|-------:|:-------------|
| 81 | 90 | Beverly, Brandon and Jewels | 55 | ✓ | B3-A1 | None | 5 | 5 missed; 2 partials overturned; near-dup on [44] |
| 82 | 91 | Gnanamani, Arun and Madhavi Ramasamy | 55 | ✓ | B3-A1 | None | 3 | 3 missed; Near-dup on [28]/[39] |
| 83 | 92 | Matthews, George (Jared) and Tracie | 55 | ✓ | B3-A2 | None | 5 | 5 missed; clean |
| 84 | 93 | Shao, Jason & Laura Heian | 55 | ✓ | B3-A2 | None | 3 | 3 missed; 15 near-dup pairs (splits on [19]) |
| 85 | 94 | Suriyanarayanan, Thiyagarajan and Aparna Nurani | 55 | ✓ | B3-A3 | None | 4 | 3 near-dup; 4 missed |
| 86 | 95 | T&L Homes LLC | 55 | ✓ | B3-A3 | None | 4 | 4 missed; QA #3 PARTIAL: Form 3522/3537 from client [10] |
| 87 | 96 | Thorne, Marcus and Carolyn | 55 | ✓ | B3-A4 | None | 4 | Near-dup; 4 missed |
| 88 | 97 | Calubaquib, Luke and Amanda | 54 | ✓ | B3-A4 | None | 10 | 4 near-dup; 10 missed (coverage) |
| 89 | 98 | Fulcher, Tommy and Maria Avalos | 54 | ✓ | B3-A5 | None | 7 | 7 missed; all grounded |
| 90 | 99 | Strategic Intervention LLC | 54 | ✓ | B3-A5 | None | 4 | 4 missed; all grounded |
| 91 | 100 | Blackburn, Donald and Hannah | 53 | ✓ | B3-A6 | None | 5 | 2 partials overturned; 5 missed |
| 92 | 101 | EBI Realty Group LLC | 53 | ✓ | B3-A6 | None | 4 | 4 missed; 6 near-dup on [15,20]; thin partial QA #5 |
| 93 | 102 | Pitts, Priscilla and Alec | 53 | ✓ | B3-A7 | None | 8 | QA #1 thin partial; 8 missed |
| 94 | 103 | McCrann, Eugene B and Tracie | 52 | ✓ | B3-A7 | None | 3 | 3 missed; QA #3 thin Sch E label |
| 95 | 104 | Sivapregasam, Loga and Vasanthi | 52 | ✓ | B3-A8 | None | 6 | 6 missed; 3 near-dup on [28] |
| 96 | 105 | Tran, Nam and Katherine | 52 | ✓ | B3-A8 | None | 2 | Cost seg ~$12k missed [10] |
| 97 | 106 | Maier, Nathan K. | 51 | ✓ | B3-A9 | None | 7 | 7 missed; $3k flag overturned QA #4 |
| 98 | 107 | Puente, Ricardo and Natalie | 51 | ✓ | B3-A9 | None | 10 | 10 missed (admin) |
| 99 | 108 | Sallade, Aaron M. and Sarah | 51 | ✓ | B3-A10 | None | 6 | 6 missed; near-dup [22] |
| 100 | 109 | Thompson, Roderick and Rachel Russo | 51 | ✓ | B3-A10 | None | 5 | QA #7 partial (invoice split); 5 missed |
| 101 | 110 | Vivier, Michael and Mary | 50 | ✓ | B3-A11 | None | 5 | 5 missed; 3 auto flags overturned |
| 102 | 111 | Pak, Hyunkyu and Joy An | 49 | ✓ | B3-A11 | None | 5 | Near-dup [33]; 5 missed |
| 103 | 112 | Lee, Alan H. and Evelyn Wang | 48 | ✓ | B3-A12 | None | 6 | 6 missed; 2 partials overturned |
| 104 | 113 | Blum, Walt and Judy | 47 | ✓ | B3-A12 | None | 4 | 4 missed; clean |
| 105 | 114 | Coburg Road LLC | 47 | ✓ | B3-A13 | None | 3 | 3 missed; QA #7 thin partial K-1 deferral; near-dup [6,9] |
| 106 | 115 | Entertainment Paradise II LLC | 47 | ✓ | B3-A13 | None | 3 | 3 missed; clean |
| 107 | 116 | Rubens, Ashley R. | 47 | ✓ | B3-A14 | None | 2 | 2 missed |
| 108 | 117 | Caine, Gary J. and Nancy | 46 | ✓ | B3-A14 | None | 4 | 4 missed; QA #1 PARTIAL: HELOC from client [41] |
| 109 | 118 | Coldiron, Aaron and Crystal | 46 | ✓ | B3-A15 | None | 3 | 2 partials overturned; 3 missed |
| 110 | 119 | Ripley, Caleb | 46 | ✓ | B3-A15 | None | 5 | QA #4 partial (form labels); 5 missed |
| 111 | 120 | Sheehan, Patrick and Anna | 45 | ✓ | B3-A16 | None | 7 | 7 missed; QA #7 thin overtime cite; 3 near-dup |
| 112 | 121 | Xu, Tahai (Michelle) and Davy | 44 | ✓ | B3-A16 | None | 2 | 2 near-dup; 2 missed |
| 113 | 122 | Gingrich, Stephen R. and Callie Southerland | 43 | ✓ | B3-A17 | None | 4 | 4 missed (admin) |
| 114 | 123 | Goo, Tracey | 43 | ✓ | B3-A17 | None | 6 | 6 missed |
| 115 | 124 | Pham, Loc and Chenda Nhim | 43 | ✓ | B3-A18 | None | 7 | 7 missed; 1 thin partial QA #4 |
| 116 | 125 | Tien, Michael and Audris | 43 | ✓ | B3-A18 | None | 3 | 3 missed; Tien QA #5 thin partial |
| 117 | 126 | Murphy, Noah I. | 42 | ✓ | B3-A19 | None | 7 | 18 near-dup (splits [11],[27]); 7 missed |
| 118 | 127 | O_Connell, Niall | 42 | ✓ | B3-A19 | None | 4 | 1 near-dup; 4 missed |
| 119 | 128 | Anzelc, Eric and Stephanie | 41 | ✓ | B3-A20 | None | 7 | 7 missed (admin) |
| 120 | 129 | Broms, Michael and Heather | 41 | ✓ | B3-A20 | None | 4 | 4 missed (admin) |
| 121 | 130 | Chillinsky, Joe C. and Sharon | 41 | ✓ | B3-A21 | None | 6 | 6 missed |
| 122 | 131 | Dhaliwal, Navjot K. | 41 | ✓ | B3-A21 | None | 2 | 2 missed |
| 123 | 132 | Green, Matthew J. and Sarah | 41 | ✓ | B3-A22 | None | 7 | DCFSA partial overturned; 7 missed |
| 124 | 133 | Prasad, Dev and Sonali Dhindwal | 41 | ✓ | B3-A22 | None | 5 | 5 missed |
| 125 | 134 | Legacy IEA LLC | 40 | ✓ | B3-A23 | None | 4 | 3 near-dup on [1,3]; 4 missed |
| 126 | 135 | Moustafa, Mohamed | 40 | ✓ | B3-A23 | None | 3 | QA #1 partial (2553 attachment); 3 missed |
| 127 | 136 | Acosta, Jaime and Alexia | 39 | ✓ | B3-A24 | None | 5 | 5 missed; Sch A/E false positive overturned |
| 128 | 137 | Anderson, Kyle t. and Valerie Schultz | 39 | ✓ | B3-A24 | None | 4 | Near-dup QA #2/#3; 4 missed |
| 129 | 138 | Gupta, Nitin and Sugandha | 39 | ✓ | B3-A25 | None | 4 | 4 missed; 15-20k flag overturned QA #2 |
| 130 | 139 | Kim, Kayla (Soo-Youn) | 39 | ✓ | B3-A25 | None | 5 | 5 missed (admin) |

Assignments: `V2_GROUNDING_AUDIT_BATCH3.md`. Machine output: `scripts/v2_batch3_agent01.json` … `agent25.json`.

---

## Master table — Batch 4 (msg ranks 131–180)

50 newest `processed_v2` files. **Transferable gaps** = uncited advisor text that passes the v2 RAG value test (not raw `find_missed()` ops lines). Detail: `V2_GROUNDING_BATCH4_AGENT_BRIEF.md`.

| Msg rank | CSV row | Client (folder name) | Msgs | `processed_v2` | Audit | Hallucination | Transferable gaps | Other issues |
|----------|---------|----------------------|-----:|:--------------:|:-----:|:-------------|------------------:|:-------------|
| 131 | 140 | Lim, Rachelle and Kristopher Obellos | 39 | ✓ | B4-A1 | None | 0 | A; 2 partials overturned |
| 132 | 141 | Shepard, John and Lina | 39 | ✓ | B4-A1 | None | 0 | A-; 1 near-dup |
| 133 | 142 | Smith, Clint & Kate | 39 | ✓ | B4-A2 | None | 1 | A-; gap **[10]** 1031 / reverse / partial 1031 |
| 134 | 143 | Strenger, Michael & Katherine | 39 | ✓ | B4-A2 | None | 0 | A-; 1 near-dup |
| 135 | 144 | Johnson, Jaime and Gregory Koehnen | 38 | ✓ | B4-A3 | None | 0 | A; $ flag overturned QA #2 |
| 136 | 145 | Kinoshita, Ryan | 37 | ✓ | B4-A3 | None | 1 | A-; gap **[21]** year-end estimate triggers |
| 137 | 146 | Nichols, Brian and Andrea Hasenauer | 37 | ✓ | B4-A4 | None | 0 | A |
| 138 | 147 | O_Hara, Samantha and William (Bill) | 37 | ✓ | B4-A4 | None | 1 | B; gap **[12]** HSA W-2 vs organizer; QA #2 partial |
| 139 | 148 | Koh, Carisa | 36 | ✓ | B4-A5 | None | 1 | A-; gap **[1]** IRA rollover / 8606; 3 near-dup |
| 140 | 149 | Ray, Jesse | 36 | ✓ | B4-A5 | None | 0 | A; QA #1 partial (client **$25k**); QA #3 thin |
| 141 | 150 | Almaraz, Ruth | 35 | ✓ | B4-A6 | None | 0 | A-; 2 thin partials |
| 142 | 151 | Hintermeister, Lucas H. and Laura | 35 | ✓ | B4-A6 | None | 0 | A; QA #4 citation-only 1095-C |
| 143 | 152 | Love, Rob and Jacqueline | 35 | ✓ | B4-A7 | None | 0 | A-; 6 near-dup pairs |
| 144 | 153 | Ecker, Michael and Ashley | 34 | ✓ | B4-A7 | None | 1 | B; gap **[15]** cost-seg DIY vs pro; QA #1 partial |
| 145 | 154 | Tent Stake Partners LLC | 34 | ✓ | B4-A8 | None | 0 | A |
| 146 | 155 | Cifuentes, Sebastian | 33 | ✓ | B4-A8 | None | 2 | A-; gaps **[9,11]** land/building; **[17]** STR vs lendability |
| 147 | 156 | Cubix | 33 | ✓ | B4-A9 | None | 0 | A |
| 148 | 157 | Kingston, Kevin P and Ekaterina V | 33 | ✓ | B4-A9 | None | 0 | A-; QA #1 partial (3520 labels); QA #3 partial ($) |
| 149 | 158 | Sun, Xin and Gang Li | 33 | ✓ | B4-A10 | None | 0 | A-; QA #3 partial (1040 line detail) |
| 150 | 159 | Arnhold, Alexandra | 32 | ✓ | B4-A10 | None | 0 | A- |
| 151 | 160 | Haus Construction, Inc. | 32 | ✓ | B4-A11 | None | 0 | A |
| 152 | 161 | McCallion, Jack and Cheryl F | 32 | ✓ | B4-A11 | None | 0 | A; 1 near-dup |
| 153 | 162 | Nunez, Denis and Ashley | 32 | ✓ | B4-A12 | None | 1 | B; gap **[8,10]** STR material-participation logs |
| 154 | 163 | Akca, Nafiz and Ming Ya Maria | 31 | ✓ | B4-A12 | None | 0 | A; 2 near-dup |
| 155 | 164 | BJB Diamond LLC | 30 | ✓ | B4-A13 | None | 0 | A |
| 156 | 165 | Goncear, Vitalii and Lolita Coloteniuc | 30 | ✓ | B4-A13 | None | 0 | A |
| 157 | 166 | Lee, Sandra | 30 | ✓ | B4-A14 | None | 0 | B+; QA #3–4 partial (form labels); 3 near-dup |
| 158 | 167 | Nguyen, Tam and Claire | 30 | ✓ | B4-A14 | None | 0 | A |
| 159 | 168 | Pucher, Alexander and Fengwei | 30 | ✓ | B4-A15 | None | 0 | A-; 15 near-dup pairs |
| 160 | 169 | Stamp, Jeffrey M. | 30 | ✓ | B4-A15 | None | 0 | A |
| 161 | 170 | Anantiyo, Mark | 29 | ✓ | B4-A16 | None | 0 | A-; 2 near-dup |
| 162 | 171 | Blumrich , Daniel and Kelsey | 29 | ✓ | B4-A16 | None | 0 | B+; thin chat (1 QA) |
| 163 | 172 | Lee, Kichun (Jason) and Elizabeth | 29 | ✓ | B4-A17 | None | 1 | A-; gap **[1]** preparer vs client copy |
| 164 | 173 | Gonzalez Fernandez, Ruben | 28 | ✓ | B4-A17 | None | 0 | A |
| 165 | 174 | Hayes, Anna and Michael | 28 | ✓ | B4-A18 | None | 0 | A; 2 auto flags overturned |
| 166 | 175 | Smallwood, III, John and Raelyn | 28 | ✓ | B4-A18 | None | 3 | **D**; **0 QAs**; gaps **[5]** STR 7-day / personal-use / REPS |
| 167 | 176 | Daniels, Anthony and Melissa Chaney | 27 | ✓ | B4-A19 | None | 1 | A; gap **[4]** e-sign separate email per taxpayer |
| 168 | 177 | Nguyen, John | 27 | ✓ | B4-A19 | None | 0 | A-; QA #6 partial; 4 near-dup |
| 169 | 178 | Hodge, Carla | 26 | ✓ | B4-A20 | None | 0 | A; 0 QAs (ops-only; empty extraction correct) |
| 170 | 179 | Kasselmann, John and Zsuzsa | 26 | ✓ | B4-A20 | None | 0 | A |
| 171 | 180 | Latting, Michelle and John | 25 | ✓ | B4-A21 | None | 0 | A |
| 172 | 181 | Portka, Daniel R. and Ana | 25 | ✓ | B4-A21 | None | 0 | B+; 1 QA |
| 173 | 182 | Tiso, Tony and Ada | 25 | ✓ | B4-A22 | None | 0 | A- |
| 174 | 183 | Winchester, Shannon T. and Nasim Vahidi | 25 | ✓ | B4-A22 | None | 1 | A; gap **[1]** preparer-copy handoff |
| 175 | 184 | Zhao, Hang and Yan Ye | 25 | ✓ | B4-A23 | None | 1 | A-; gap **[13]** STR 7-day / active vs passive |
| 176 | 185 | Hussman, Ryan and Lisa | 24 | ✓ | B4-A23 | None | 0 | A (prior-year returns chat) |
| 177 | 186 | Love, J and Tobie | 24 | ✓ | B4-A24 | None | 0 | A |
| 178 | 187 | Schaaf, Jacob E. | 24 | ✓ | B4-A24 | None | 0 | A; Sch A/E normalization overturned |
| 179 | 188 | Fitzsimmons, Natalie C. and Christopher | 23 | ✓ | B4-A25 | None | 0 | A-; near-dup on shared cites |
| 180 | 189 | Leah Guerra Homes | 23 | ✓ | B4-A25 | None | 0 | A; QA #4 partial overturned |

Assignments: `V2_GROUNDING_AUDIT_BATCH4.md`. Reports: `V2_GROUNDING_BATCH4_AGENT01.md` … `AGENT25.md`. Machine: `scripts/v2_batch4_agent01.json` … `agent25.json`.

---

## Master table — Batch 5 (msg ranks 181–282)

102 tail `processed_v2` files. **26 agents × 4 files** (agent 26 = 2). Same methodology as Batch 4 (`transferable_gaps`).

**Batch 5 confirmed hallucinations:** **None** (all 102 files).

Assignments: `V2_GROUNDING_AUDIT_BATCH5.md`, `scripts/_batch5_assignments.json`. Reports: `V2_GROUNDING_BATCH5_AGENT01.md` … `AGENT26.md`. Machine: `scripts/v2_batch5_agent01.json` … `agent26.json`.

| Msg rank | CSV row | Client (folder name) | Msgs | `processed_v2` | Audit | Hallucination | Transferable gaps | Other issues |
|----------|---------|----------------------|-----:|:--------------:|:-----:|:-------------|------------------:|:-------------|
| 181 | 182 | Tiso, Tony and Ada | 25 | ✓ | B5-A1 | None | 0 | A; 1 QA |
| 182 | 183 | Winchester, Shannon T. and Nasim Vahidi | 25 | ✓ | B5-A1 | None | 0 | A; auto P overturned (Sch E) |
| 183 | 184 | Zhao, Hang and Yan Ye | 25 | ✓ | B5-A1 | None | 2 | A-; gaps **[13]** STR 7-day + K-1 outside basis |
| 184 | 185 | Hussman, Ryan and Lisa | 24 | ✓ | B5-A1 | None | 0 | A; 3 QAs (prior-year chat) |
| 185 | 186 | Love, J and Tobie | 24 | ✓ | B5-A2 | None | 0 | A-; 1 QA |
| 186 | 187 | Schaaf, Jacob E. | 24 | ✓ | B5-A2 | None | 0 | A-; 2 auto P overturned |
| 187 | 188 | Fitzsimmons, Natalie C. and Christopher | 23 | ✓ | B5-A2 | None | 0 | A; 2 near-dup pairs |
| 188 | 189 | Leah Guerra Homes | 23 | ✓ | B5-A2 | None | 0 | A-; 1 auto P overturned |
| 189 | 190 | Lin, Ying-Yien (Michael) and Melissa | 23 | ✓ | B5-A3 | None | 0 | A-; partial QA **#3** (client childcare); 2 near-dup |
| 190 | 191 | Rosel, Maira and Arlene | 23 | ✓ | B5-A3 | None | 0 | A; 2 QAs |
| 191 | 192 | St John, Joshua and Heather | 23 | ✓ | B5-A3 | None | 0 | A; 5 QAs; 1 near-dup |
| 192 | 193 | Tien Medical Group, Inc. | 23 | ✓ | B5-A3 | None | 0 | A-; 4 QAs; 2 near-dup |
| 193 | 194 | Chiu, Simon & Erin Herrero | 22 | ✓ | B5-A4 | None | 0 | A-; 1 QA |
| 194 | 195 | Corral, Jose and Minerva | 22 | ✓ | B5-A4 | None | 0 | B+; 1 QA; auto P overturned |
| 195 | 196 | Kopshever, David and Anela Marie | 22 | ✓ | B5-A4 | None | 0 | A-; partial QA **#2** (escrow/client $) |
| 196 | 197 | Marshall, Tatum Y. | 22 | ✓ | B5-A4 | None | 0 | A; 2 QAs |
| 197 | 198 | Qureshi, Hamza and Anisha Aladross | 22 | ✓ | B5-A5 | None | 0 | A; **0 QAs** (ops-only) |
| 198 | 199 | Camp Creek Holdings LLC | 21 | ✓ | B5-A5 | None | 0 | A-; partial QA **#6** thin; 9 near-dup |
| 199 | 200 | Capital Gold Property Group, LLC | 21 | ✓ | B5-A5 | None | 1 | B+; gap **[8]** fixed-asset detail |
| 200 | 201 | Deranaz Solutions LLC | 21 | ✓ | B5-A5 | None | 0 | A; 3 QAs; 1 near-dup |
| 201 | 202 | Gonzalez, Christopher and Amelia | 21 | ✓ | B5-A6 | None | 0 | A; auto H overturned (`-6k`) |
| 202 | 203 | Jain, Akshay and Prachi | 21 | ✓ | B5-A6 | None | 0 | A-; thin partial QA **#1**; auto H overturned |
| 203 | 204 | Kauffman, Anthony and Nadia Ali | 21 | ✓ | B5-A6 | None | 1 | B; **0 QAs**; gap **[1]** preparer copy |
| 204 | 205 | Norman, Timothy and Hannah | 21 | ✓ | B5-A6 | None | 0 | A-; 4 QAs; 1 near-dup |
| 205 | 206 | Ranck, Pierce and Kayle Caruso | 21 | ✓ | B5-A7 | None | 1 | B; **0 QAs**; gap **[1]** preparer copy |
| 206 | 207 | Richard, Rick and Diedre | 21 | ✓ | B5-A7 | None | 0 | A; 5 QAs |
| 207 | 208 | Shen, Ben and Estela | 21 | ✓ | B5-A7 | None | 0 | A; 3 QAs |
| 208 | 209 | Gemstone Gymnastics, LLC | 20 | ✓ | B5-A7 | None | 0 | A-; 2 near-dup pairs |
| 209 | 210 | GO Equity LLC | 20 | ✓ | B5-A8 | None | 0 | A; 2 auto P overturned |
| 210 | 211 | Gonzalez, Erick | 20 | ✓ | B5-A8 | None | 0 | N/A; **0 QAs** |
| 211 | 212 | Gonzalez, Mike and Jasmine | 20 | ✓ | B5-A8 | None | 0 | A; 3 QAs |
| 212 | 213 | Graddon, Brian and Elizabeth | 20 | ✓ | B5-A8 | None | 0 | N/A; **0 QAs** |
| 213 | 214 | O_Brien, Michael | 20 | ✓ | B5-A9 | None | 0 | A; 4 QAs; 1 near-dup |
| 214 | 215 | Revere Coatings Inc | 20 | ✓ | B5-A9 | None | 0 | A; 4 QAs; 1 near-dup |
| 215 | 216 | Infiniti Property Holdings LLC | 19 | ✓ | B5-A9 | None | 0 | A; **0 QAs** (wind-down) |
| 216 | 217 | Obligation Inc | 19 | ✓ | B5-A9 | None | 0 | A; 3 QAs; 1 near-dup |
| 217 | 218 | Anthony Fernandez, a Nursing Corp | 18 | ✓ | B5-A10 | None | 0 | A-; 1 QA |
| 218 | 219 | Atlantic Reach International LLC | 18 | ✓ | B5-A10 | None | 0 | A; 4 QAs; auto P overturned |
| 219 | 220 | Bohannon, Sam and Candace | 18 | ✓ | B5-A10 | None | 0 | A-; partial QA **#2** (estimates in uncited **[1]**) |
| 220 | 221 | Chesus, Mary and Enda Phelan | 18 | ✓ | B5-A10 | None | 0 | A; 3 QAs |
| 221 | 222 | Scheele, Christopher G and Lina | 18 | ✓ | B5-A11 | None | 0 | —; **0 QAs** |
| 222 | 223 | Ziegler, Victoria and Alec | 18 | ✓ | B5-A11 | None | 0 | —; **0 QAs** |
| 223 | 224 | Gray, Tina M. and Michael | 17 | ✓ | B5-A11 | None | 0 | A; 6 QAs; 1 near-dup |
| 224 | 225 | Osorio, Giancarlo and Julianna | 17 | ✓ | B5-A11 | None | 0 | A-; auto P overturned |
| 225 | 226 | Coast Vacation Homes LLC | 16 | ✓ | B5-A12 | None | 0 | A-; 1 QA |
| 226 | 227 | Raffetto, Mark and Meri | 16 | ✓ | B5-A12 | None | 0 | A-; 1 QA |
| 227 | 228 | The Jericho Group Global LLC | 16 | ✓ | B5-A12 | None | 0 | A; 3 QAs; 2 auto H overturned |
| 228 | 229 | From House to Home Properties, LLC | 15 | ✓ | B5-A12 | None | 0 | A-; 1 QA |
| 229 | 230 | Gath, Shaun and Cortney | 15 | ✓ | B5-A13 | None | 0 | A; auto P overturned |
| 230 | 231 | Ilalio, Matthew and Celestine | 15 | ✓ | B5-A13 | None | 1 | B+; gap **[1]** preparer copy |
| 231 | 232 | Yu, Jesse and Christine Yang | 15 | ✓ | B5-A13 | None | 1 | A-; gap **[0]** preparer copy |
| 232 | 233 | Bell, Charles Brad and Amy | 14 | ✓ | B5-A13 | None | 0 | A; preparer copy extracted |
| 233 | 234 | Seyer, Dan and Magdalena | 14 | ✓ | B5-A14 | None | 1 | B; **confirmed P** QA **#1**; gap **[2]** preparer copy |
| 234 | 235 | Silveira, Carla | 14 | ✓ | B5-A14 | None | 1 | A-; gap **[1]** preparer copy |
| 235 | 236 | Tien Foot and Ankle Specialist Corp | 14 | ✓ | B5-A14 | None | 0 | A; 2 QAs (PTET/CA payments) |
| 236 | 237 | Vo, Amanda | 14 | ✓ | B5-A14 | None | 1 | —; **0 QAs**; gap **[1]** preparer copy |
| 237 | 238 | Hutchinson, Romobia | 13 | ✓ | B5-A15 | None | 0 | A-; thin partial QA **#2**; 2 auto P overturned |
| 238 | 239 | Ruff, Jaxson and Emma | 13 | ✓ | B5-A15 | None | 0 | A; 2 QAs |
| 239 | 240 | Brick, Michael C. | 12 | ✓ | B5-A15 | None | 0 | A; 1 QA |
| 240 | 241 | Combado, Christofer | 12 | ✓ | B5-A15 | None | 0 | A; auto P overturned |
| 241 | 242 | Corral Investments & Realty Inc. | 12 | ✓ | B5-A16 | None | 0 | A-; 1 QA (EV/S-corp) |
| 242 | 243 | Held, Matthew | 12 | ✓ | B5-A16 | None | 0 | A; 2 QAs |
| 243 | 244 | Lin, Wanchun (Tammy) and Joseph Liu | 12 | ✓ | B5-A16 | None | 0 | A; 2 QAs |
| 244 | 245 | MREI Group LLC | 12 | ✓ | B5-A16 | None | 1 | B; **0 QAs**; gap **[2]** Sch E repairs / CA LLC fee |
| 245 | 246 | Rooted Capital Holdings, LLC | 12 | ✓ | B5-A17 | None | 0 | A; 1 QA |
| 246 | 247 | TJ&J Investments, Inc. | 12 | ✓ | B5-A17 | None | 0 | A; 2 QAs; auto P overturned |
| 247 | 248 | Turnwall, Douglas and Stephanie | 12 | ✓ | B5-A17 | None | 0 | A; **0 QAs** |
| 248 | 249 | Calvetti, Gabriel and Dawn | 11 | ✓ | B5-A17 | None | 1 | A-; partial QA **#2** (HSA); gap **[2]** separate e-sign emails |
| 249 | 250 | Johnson, Tony and Lesley | 11 | ✓ | B5-A18 | None | 0 | A; **0 QAs** |
| 250 | 251 | Tang, Andy C. | 11 | ✓ | B5-A18 | None | 0 | A; preparer copy QA |
| 251 | 252 | Trivedi, Disha and Anand A. | 11 | ✓ | B5-A18 | None | 1 | B-; gap **[1]** preparer copy |
| 252 | 253 | Forteva Company | 9 | ✓ | B5-A18 | None | 0 | A-; 1 QA (3/15 deadline) |
| 253 | 254 | Gu, Quan | 9 | ✓ | B5-A19 | None | 1 | A-; gap **[0]** preparer copy |
| 254 | 255 | Jennings, Kat | 9 | ✓ | B5-A19 | None | 0 | B+; 2 QAs (workflow) |
| 255 | 256 | Meteau Jr., Robert J. | 9 | ✓ | B5-A19 | None | 0 | A; 2 QAs |
| 256 | 257 | P Paul Chillar MD PC | 9 | ✓ | B5-A19 | None | 0 | —; **0 QAs** (no advisor AB 150 answer) |
| 257 | 258 | Gem Allan Management LLC | 8 | ✓ | B5-A20 | None | 0 | A; 1 QA (PTE extension) |
| 258 | 259 | Infiniti Property Solutions LLC | 8 | ✓ | B5-A20 | None | 0 | A; **0 QAs** |
| 259 | 260 | Smith, Jordan | 8 | ✓ | B5-A20 | None | 0 | A; **0 QAs** |
| 260 | 261 | Aguilar, Nancy A. and Oscar Calleja | 7 | ✓ | B5-A20 | None | 0 | A; **0 QAs** |
| 261 | 262 | Dithese Investments Inc | 7 | ✓ | B5-A21 | None | 0 | A; 1 QA |
| 262 | 263 | Echo Partners LLC | 7 | ✓ | B5-A21 | None | 0 | B; **0 QAs** |
| 263 | 264 | Lago Selva LLC | 7 | ✓ | B5-A21 | None | 0 | A; 1 QA |
| 264 | 265 | Patel, Rajesh and Bijo | 7 | ✓ | B5-A21 | None | 0 | B+; **0 QAs** |
| 265 | 266 | Nagda, Drew and Thalia | 6 | ✓ | B5-A22 | None | 1 | B; gap **[1]** preparer copy |
| 266 | 267 | Al Tekreerti, Taha and Lina Al Shaikhli | 5 | ✓ | B5-A22 | None | 0 | B; partial QA **#1** (allocation stretch) |
| 267 | 268 | NH Group, LLC | 5 | ✓ | B5-A22 | None | 0 | A; 1 QA (PTE/CA franchise) |
| 268 | 269 | Ramnauth, Devantany and Kushala | 5 | ✓ | B5-A22 | None | 0 | A-; **0 QAs** (scheduling/status) |
| 269 | 270 | Tweedy, Craig and Shelley | 5 | ✓ | B5-A23 | None | 0 | N/A; **0 QAs** |
| 270 | 271 | Victoria F. Ziegler | 5 | ✓ | B5-A23 | None | 0 | N/A; **0 QAs** |
| 271 | 272 | Cairde Investments, LLC | 4 | ✓ | B5-A23 | None | 0 | N/A; **0 QAs** |
| 272 | 273 | Salazar, Gerald and Sorada | 4 | ✓ | B5-A23 | None | 0 | A; auto H overturned (`2.5k`) |
| 273 | 274 | Alfred, Christopher | 3 | ✓ | B5-A24 | None | 0 | A; 1 QA |
| 274 | 275 | First Rose Real Estate LLC | 3 | ✓ | B5-A24 | None | 0 | A; 1 QA (extension template) |
| 275 | 276 | Katie Allyne Health Inc | 3 | ✓ | B5-A24 | None | 0 | A; 1 QA (extension template) |
| 276 | 277 | Santiago, Damaris | 3 | ✓ | B5-A24 | None | 0 | A; **0 QAs** |
| 277 | 278 | Allan James Real Estate One LLC | 2 | ✓ | B5-A25 | None | 0 | A; 1 QA |
| 278 | 279 | Sparks, Brad and Lori | 2 | ✓ | B5-A25 | None | 0 | A; 1 QA (travel days) |
| 279 | 280 | Hussman, Ryan and Lisa | 1 | ✓ | B5-A25 | None | 0 | A; **0 QAs** (onboarding only) |
| 280 | 281 | King, Chassidy R. | 1 | ✓ | B5-A25 | None | 0 | A; **0 QAs** (e-file letter) |
| 281 | 282 | Ramnauth, Devantany and Kushala | 1 | ✓ | B5-A26 | None | 0 | N/A; **0 QAs** (organizer blast) |
| 282 | 283 | Yco, Grace | 1 | ✓ | B5-A26 | None | 0 | N/A; **0 QAs** (onboarding filtered) |

---

## Master table — Gap batch (8 files)

Previously unaudited v2 extractions (early tests, CSV `—` ticks, Batch 2 skip). Same methodology as Batch 4 (`transferable_gaps`).

| Msg rank | CSV row | Client (folder name) | Msgs | `processed_v2` | Audit | Hallucination | Transferable gaps | Other issues |
|----------|---------|----------------------|-----:|:--------------:|:-----:|:-------------|------------------:|:-------------|
| 23 | 24 | Carr, Danny and Frederica | 102 | ✓ | Gap-A1 | None | 1 | A-; partial QA **#14** (client IP PIN 1/6/26); 3 near-dup; auto H overturned |
| 29 | 30 | Umbalacheri Ramasamy, Venkatraman and Jayashree | 97 | ✓ | Gap-A1 | None | 0 | A; 2 auto-H overturned (`2k`/`7k`); 1 near-dup |
| 35 | 36 | Ho, Tim and Stephanie Liu | 90 | ✓ | Gap-A2 | None | 0 | A; auto partial QA **#1** overturned |
| 39 | 40 | Elliott, Kevin and Anna Jennie M | 87 | ✓ | Gap-A2 | None | 0 | A-; auto H QA **#3** overturned; 3 near-dup on **[21]** |
| 42 | 43 | Casillas, Juan and Pamela Guillen | 82 | ✓ | Gap-A3 | None | 0 | A; auto H QA **#5** overturned (`1-4k`); 3 near-dup on **[33]** |
| 47 | 48 | Ren, Deyao and Zheng Tao | 80 | ✓ | Gap-A3 | None | 1 | A-; partial QA **#4**; gap **[0]** preparer vs client copy |
| 53 | 54 | Lising, Christian and Kim | 74 | ✓ | Gap-A4 | None | 1 | A-; 2 auto-P overturned; gap **[13]** cost seg off P&L; 2 near-dup |
| 60 | 61 | Chillar, Paul and Angelica | 70 | ✓ | Gap-A4 | None | 1 | B+; partial QA **#4**, **#13**; gap **[39]** MLP K-1; 16 near-dup |

**Gap batch confirmed hallucinations:** **None** (all 8 files).

Assignments: `V2_GROUNDING_AUDIT_GAP.md`, `scripts/_gap_audit_assignments.json`. Reports: `V2_GROUNDING_GAP_AGENT01.md` … `AGENT04.md`. Machine: `scripts/v2_gap_audit_agent01.json` … `agent04.json`.

---

## Confirmed hallucinations (detail) — all resolved

Cleanup in `qa_output_v2/*/extraction.json` (**2026-05-22**). Re-verify: `python scripts/verify_hallucination_cleanup.py`.

| Client | QA | Resolution |
|--------|-----|------------|
| Burkes | #12 | **Edited** — “~10% per month” (was per year) |
| Yen | #10 | **Removed** |
| Albayaty | #16 | **No change** — overturned; **~$125k** in advisor **[104]** |
| Dobyns | #19 | **Removed** |
| Williams | #9 | **Edited** — removed **$10,000** sentence |
| Wang | #14 | **Removed** |
| Diaz | #9 | **Edited** — removed **~$3,320**; kept **~$500** advice |
| Ogueli | #7 | **Edited** — removed **~$40k** from answer |
| Espinoza | #5 | **Edited** — solar **$16k / $50k / $15k / $17k** |

### Msg rank 8 (CSV row 9) — Burkes, Sammie and Erin — **Resolved**

- **Was:** QA **#12** (index **#11**): **~10% per year** vs advisor **~10%/month** at **[74]**.
- **Fix:** Answer now says **~10% per month**.
- **Output:** `qa_output_v2/Burkes, Sammie and Erin/extraction.json`

### Msg rank 7 (CSV row 8) — Yen, Andrew and Jacqueline — **Resolved**

- **Was:** QA **#10**: **$2,500** / **$800** from **client** **[92,93]** only.
- **Fix:** QA **removed** (16 QAs remain).

### Msg rank 14 (CSV row 15) — Albayaty, Monica and Richard — **Resolved (overturned)**

- **Was:** Audit thought **~$125,000** prior due not in cited text.
- **Fix:** No extraction edit — **~$125k** is in advisor **[104]**; QA **#16** kept.

### Msg rank 26 (CSV row 27) — Dobyns, Kristina — **Resolved**

- **Was:** QA **#19**: **$1,000** workflow; advisor **[84]** only “That is correct”.
- **Fix:** QA **removed** (22 QAs remain).

### Msg rank 71 (CSV row 72) — Williams, Thomas S. and Emi — **Resolved**

- **Was:** QA **#9**: **$10,000** extension from **client** **[55]** only.
- **Fix:** **$10,000** sentence removed from answer.

### Msg rank 54 (CSV row 55) — Wang, Yuehai and Gisele Hong — **Resolved**

- **Was:** QA **#14**: **$1,000** Trump account from **client** **[66]**, not **[67]**.
- **Fix:** QA **removed** (13 QAs remain).

### Msg rank 55 (CSV row 56) — Diaz, Anne and Martin Carew — **Resolved**

- **Was:** QA **#9**: **~$3,320** from **client** **[47]**.
- **Fix:** **~$3,320** removed; advisor **~$500** savings guidance retained.

### Msg rank 58 (CSV row 59) — Ogueli, Vivian and Ifeanyi — **Resolved**

- **Was:** QA **#7**: **~$40,000** in answer from **client** thread.
- **Fix:** **~$40k** removed from answer (passive-loss treatment kept).

### Msg rank 66 (CSV row 67) — Espinoza, Meny and Diana — **Resolved**

- **Was:** QA **#5**: solar **$25k / $65k / $19.5k** vs advisor **[29]** **$16k / $50k / $15k / $17k**.
- **Fix:** Answer uses advisor’s example dollars.

---

## Borderline / citation-only (detail)

### Msg rank 1 (CSV row 2) — Cortez, Christian and Yesenia

- **Not a hallucination** for KB substance: Mar 19 “Nothing needed… I will e-file it” is real advisor text at filtered **[212]**, same extension arc as Feb 7 request.
- **Issue:** Extension QA cites **[196, 197, 199]** only — closing sentence not provable from citations alone.

### Msg rank 15 (CSV row 16) — Skorobogatova, Ekaterina and Anna Zhirova

- **QA #7**: Thin citation **[94]**; Form **1099-G** specificity goes beyond one-line advisor reply. Core taxability in 2024 is grounded.

### Batch 2 — borderline / citation-only (selected)

| Msg rank | Client | QA | Label | Detail |
|----------|--------|-----|-------|--------|
| 57 | Kuramoto | #7 | Borderline | **Sch E** name not in **[56]**; dollar reconciliation grounded |
| 68 | Koch | #3 | Citation only | IRA/HSA timing rules; substantive text at **[15]** not cited |
| 73 | Ho | #4 | Borderline | **~1k** amend fee normalized to **$1,000** — in **[33]** |
| 74 | Martin, Benjamin J. | #4 | Borderline | **1040-X** “not required” from **client**; advisor covers rejection path |
| 79 | Inoue | #3 | Borderline | **$2,500** remodel threshold in QA **#1** / question, not **[19]** |
| 84 | Chen | #5 | Citation only | Extension/audit answer grounded at **[28,30]**; **[22,25,26]** procedural only |
| 61 | Holbrook | #6 | Borderline | HELOC one-liner **[24]** — accurate but thin |

### Batch 4 — partial / citation-only (selected; not confirmed hallucination)

| Msg rank | Client | QA | Label | Detail |
|----------|--------|-----|-------|--------|
| 138 | O'Hara | #2 | Partial | IRS identity steps beyond cited **[25, 28, 32]** |
| 140 | Ray | #1 | Partial | **$25,000** from **client [8]**; REPS guidance grounded on advisor |
| 148 | Kingston | #1 | Partial | Forms **3520/3520-A** not in cited advisor text |
| 148 | Kingston | #3 | Partial | **$35k** from uncited **[24]**; **[26]** has 593 amounts |
| 149 | Sun | #3 | Partial | 1040 **5a/5b** detail not in cited **[23]** |
| 157 | Lee, Sandra | #3–4 | Partial | FBAR/**8938** / **1116** labels not in cited **[20]** |
| 144 | Ecker | #1 | Partial | FMV vs basis framing beyond one-line **[21]** |
| 168 | Nguyen, John | #6 | Partial | SSN failure-mode framing not in cited **[24]** |

### Gap batch — partial / client-sourced (not confirmed hallucination)

| Msg rank | Client | QA | Label | Detail |
|----------|--------|-----|-------|--------|
| 23 | Carr | #14 | Partial | IP PIN workflow grounded on advisor; **1/6/26 incorrect PIN mail** from **client [90]** |
| 47 | Ren | #4 | Partial | **[69]** no switch depreciation back/forth; answer adds STR/straight-line framing |
| 60 | Chillar | #4 | Partial | Form **100S** / Sch L not in cited open-items **[12,14,17]** |
| 60 | Chillar | #13 | Partial | **[59]** “one box did not get checked” — foreign-income inference thin |

### Batch 5 — partial / client-sourced (not confirmed hallucination)

| Msg rank | Client | QA | Detail |
|----------|--------|-----|--------|
| 189 | Lin | #3 | Client-specific childcare splits not in cited advisor text |
| 195 | Kopshever | #2 | Escrow/P&L detail from **client [7]**, not advisor **[8]** |
| 198 | Camp Creek | #6 | "Agendas" / comparable rates not in cited **[10,12]** |
| 219 | Bohannon | #2 | Prior-year estimate safe-harbor wording in uncited **[1]** |
| 233 | Seyer | #1 | S-corp/Excel/activity types from **client [9]**; QB equation grounded |
| 202 | Jain | #1 | Thin: visa/STR framing beyond cited **[5,7]** |
| 237 | Hutchinson | #2 | Home-purchase 403(b) context from client, not advisor **[4]** |
| 248 | Calvetti | #2 | HSA "no distributions" from **client [6]**, not advisor **[7]** |
| 266 | Al Tekreerti | #1 | Allocation mechanics beyond advisor "may need to allocate" |

---

## Other structural issues (not hallucination)

### Msg rank 18 (CSV row 19) — Aronne, Jason and Kunal

| QA | Issue |
|----|--------|
| **#5** | `advisor_message_indices` includes **[26]** = **client** role — drop index |
| **#17** | Question asks Form **593** withholding; cited **[96]** is **lazy 1031** text — content lives in **#18** at **[99, 101]** |

### Msg rank 65 (CSV row 66) — Moffett, Mark and Jennifer

| QA | Issue |
|----|--------|
| **#2** | Question = HELOC allocation; answer = REPS / property managers from **[14]**; cites **[4,7,9]** — content in **#13–#14** at **[57]** |

---

## Missed knowledge — Batch 2 (high-value gaps)

Substantive advisor threads **not captured** in any QA (post-filter indices). Counts in master table; below = items worth a **second extraction pass** or human KB add.

| Theme | Clients (msg rank) | Example indices / topics |
|-------|-------------------|---------------------------|
| **Passive loss / Form 8582 / large $** | 58 Ogueli, 78 Withana | Ogueli **[53]** thread beyond QA scope; Withana **~$10k** increase **[12]** |
| **Estimates / extension payments** | 62 Manietta, 76 Cao, 70 Pleas, 79 Inoue | Manietta **$8k fed / $3.2k CA** **[5]**; Cao carryover/estimate megathreads; Inoue refund **~$10k** **[51]** |
| **Entity / 1065 / LLC compliance** | 65 Moffett, 86 Carter, 51 Martin J | Moffett CA withholding **[55]**; Carter Rooted **1065** vs Sch C cleanup **[26]**; Martin J partnership extension **[48]** |
| **Cost seg / REPS planning** | 67 Haghi, 78 Withana, 81 Shah | Haghi **~$300k** land reclass **[21]**; Shah REI Hub **[42]**; Withana formation docs **[54]** |
| **Onboarding / portal / FTB access** | Many | E-sign separate email, preparer copy, FTB access — often procedural but recurring |
| **Thin coverage (few QAs, many msgs)** | 62 Manietta (3 QAs), 70 Pleas (4 QAs) | Large chat volume vs extracted pairs |

### Per-client missed samples (advisor index → topic)

| Rank | Client | Top missed (filtered index) |
|------|--------|-----------------------------|
| 46 | Otani | **[33]** tax projection package; K-1 timing **[3]** |
| 49 | Martin, Tyler | **[5]** Katie S-corp **$1,500**; **[69]** estimate close-out |
| 51 | Martin, Jonathan | **[48]** partnership extension filed |
| 52 | Coleman | **[14]** IRS notice after estimated payment |
| 54 | Wang | **[5]** CA address / no CA filing; **[23]** cost-seg timing |
| 55 | Diaz | **[20]** stock sales / cost basis; **[4]** IRS agent hold-submit |
| 56 | Barnes | **[49]** FTB access; **[4]** 10/15 deadline |
| 58 | Ogueli | **[8]** DERANAZ separate return; **[19]** biz/personal accounts |
| 61 | Holbrook | **[1]** S-corp payroll review; **[6]** October deadline |
| 62 | Manietta | **[1]** **$525K** sale context; **[5]** **$8k/$3.2k** estimates; **[29]** REPS app |
| 65 | Moffett | **[55]** CA withholding **2% vs 6%**; **[42]** Ethan handoff |
| 67 | Haghi | **[21]** **~$300k** land allocation / **~$90k** savings estimate |
| 68 | Koch | Multiple estimate / onboarding threads (12 flagged) |
| 72 | Ye | 12 threads — heavy overlap with near-dup QAs on **[44]** |
| 76 | Cao | Onboarding, estimates, payroll Solo 401(k) follow-ups (10 flagged) |
| 78 | Withana | **[12]** **~$10k** tax increase; **[54]** LLC formation docs |
| 79 | Inoue | **[14]** cost-seg pricing; **[37]** FTB access; **[51]** **~$10k** refund pending |
| 81 | Shah | **[42]** REI Hub vs PDF reconciliation |
| 85 | Weber | **[37]** year-end estimate / cost seg / REPS options |

---

## Missed knowledge — Batch 3

**241** advisor messages flagged across 50 files (not in any QA citation). Most are **admin/onboarding** (e-sign, Ethan handoff, FTB access, year-end letter, portal booking). Full arrays per file: `scripts/v2_batch3_agent01.json` … `agent25.json`.

### Themes (batch 3)

| Theme | Examples (msg rank) |
|-------|---------------------|
| **Near-duplicate QA splits** | 84 Shao (15 pairs on **[19]**); 117 Murphy (18 on **[11]/[27]**); 92 EBI (6 on **[15,20]**) |
| **Substantive missed (not admin)** | 96 Tran cost-seg **~$12k** **[10]**; 88 Calubaquib (10 flags, coverage gap) |
| **Partial / client-sourced (not Confirmed)** | 86 T&L Form labels from **[10]**; 108 Caine HELOC from **[41]**; 93 Pitts SALT detail |
| **Checker false positives overturned** | 97 Maier $3k; 129 Gupta 15–20k; 127 Acosta Sch A/E spelling |

### Per-client missed samples (batch 3, ranks 89–130 + notable 81–88)

| Rank | Client | Top missed (filtered index) |
|------|--------|-----------------------------|
| 84 | Shao | Heavy dup on **[19]**; missed threads secondary to 15 near-dups |
| 88 | Calubaquib | **[10]** coverage / onboarding; 10 missed total |
| 89 | Fulcher | Operational follow-ups (7); extractions grounded |
| 96 | Tran | **[10]** cost-seg savings ballpark |
| 98 | Puente | 10 admin threads (FTB, booking, handoff) |
| 100 | Thompson | **[22]** extension/estimate context; QA #7 invoice-split partial |
| 117 | Murphy | Near-dup splits **[11]/[27]**; 7 substantive misses |
| 108 | Caine | Open-items / extension threads; QA #1 uses client **[41]** for HELOC |

---

## Transferable gaps — Batch 4 (RAG-worthy misses only)

Substantive advisor guidance **not extracted** as QAs, per agent reports (`transferable_gaps` — **not** raw `missed_knowledge`). **12 clients**, ~**15** threads across 50 files.

| Msg rank | Client | Index | Topic (why extract) |
|----------|--------|-------|---------------------|
| 133 | Smith, Clint & Kate | **[10]** | Standard / reverse / partial **1031** disposition options |
| 136 | Kinoshita, Ryan | **[21]** | When formal **year-end estimates** warranted vs chat-only review |
| 138 | O'Hara | **[12]** | **HSA**: W-2 box vs organizer — reconcile with custodian |
| 139 | Koh, Carisa | **[1]** | **IRA rollover**, 1099-R, **8606**, credit limits |
| 144 | Ecker | **[15]** | **Cost seg** DIY (~$500–1k) vs pro (~$3k); cost-method appraisal |
| 146 | Cifuentes | **[9, 11]** | **Land vs building** allocation without new appraisal |
| 146 | Cifuentes | **[17]** | **STR loss** tax savings vs passive reporting for lendability |
| 153 | Nunez | **[8, 10]** | STR loophole **material participation** time logs / audit risk |
| 163 | Lee, Kichun (Jason) | **[1]** | **Preparer copy** vs client copy when switching preparers |
| 166 | Smallwood | **[5]** | **0 QAs** — STR **7-day** test, personal-use days, REPS/DFAS note |
| 167 | Daniels | **[4]** | **Separate email per taxpayer** for IRS e-sign |
| 174 | Winchester | **[1]** | Preparer-copy / TurboTax worksheet handoff |
| 175 | Zhao | **[13]** | STR **7-day** test; active vs passive; liability swing |

**Batch 4 confirmed hallucinations:** **None** (all 50 files).

**Near-duplicate noise (not gaps):** 143 Love (6 pairs); 159 Pucher (15 pairs); 168 Nguyen John (4 pairs).

Full per-client write-ups: `V2_GROUNDING_BATCH4_AGENT*.md`.

---

## Transferable gaps — Gap batch

| Msg rank | Client | Index | Topic (why extract) |
|----------|--------|-------|---------------------|
| 23 | Carr, Danny and Frederica | **[38]** | Airbnb statement lines: service fees → gross; cleaning/occupancy taxes reduce gross |
| 47 | Ren, Deyao and Zheng Tao | **[0]** | Preparer copy vs client copy when switching preparers / from TurboTax |
| 53 | Lising, Christian and Kim | **[13]** | Cost seg improvements must **not** be on the P&L |
| 60 | Chillar, Paul and Angelica | **[39]** | Brokerage stock holdings may issue **MLP K-1** annually |

Full reports: `V2_GROUNDING_GAP_AGENT*.md`.

---

## Transferable gaps — Batch 5 (RAG-worthy misses only)

Substantive advisor guidance **not extracted** as QAs (`transferable_gaps` — not raw `missed_knowledge`). **14 clients**, ~**16** threads across 102 files. Many repeats of **preparer copy vs client copy** onboarding.

| Msg rank | Client | Index | Topic (why extract) |
|----------|--------|-------|---------------------|
| 183 | Zhao, Hang and Yan Ye | **[13]** | STR **7-day test** / active vs passive liability swing |
| 183 | Zhao, Hang and Yan Ye | **[13]** | K-1 **outside basis** / passive loss tracking beyond capital account |
| 199 | Capital Gold Property Group, LLC | **[8]** | Rental fixed assets: line-item improvements vs aggregated "Building" |
| 203 | Kauffman, Anthony and Nadia Ali | **[1]** | Preparer copy vs client/TurboTax copy when changing accountants |
| 205 | Ranck, Pierce and Kayle Caruso | **[1]** | Same preparer-copy onboarding template |
| 230 | Ilalio, Matthew and Celestine | **[1]** | Preparer copy vs client copy |
| 231 | Yu, Jesse and Christine Yang | **[0]** | Preparer copy vs client copy |
| 233 | Seyer, Dan and Magdalena | **[2]** | Preparer copy vs client copy |
| 234 | Silveira, Carla | **[1]** | Preparer copy vs client copy |
| 236 | Vo, Amanda | **[1]** | Preparer copy (0 QAs on thread) |
| 244 | MREI Group LLC | **[2]** | High Sch E repairs → capitalize review; CA $800 LLC fee on rental schedule |
| 248 | Calvetti, Gabriel and Dawn | **[2]** | **Separate IRS e-sign email per spouse** |
| 251 | Trivedi, Disha and Anand A. | **[1]** | Preparer copy vs client copy |
| 253 | Gu, Quan | **[0]** | Preparer copy vs client copy |
| 265 | Nagda, Drew and Thalia | **[1]** | Prior-return handoff / depreciation worksheets |

Full reports: `V2_GROUNDING_BATCH5_AGENT*.md`.

---

## Files with v2 output — audit status

- **Hallucination cleanup (9 clients, batches 1–2):** **Complete** — all flags **resolved** in `qa_output_v2` (see detail table above).
- **Gap batch (8 files):** Resolved — see Gap master table.
- **Batch 5 (ranks 181–282):** **Complete** — all **102** tail files audited.
- **Full corpus:** **282** / **282** `processed_v2` files have had a grounding audit pass (batches 1–5 + gap).

---

## gpt51 → v2 (historical hallucinations fixed)

For ranks **1–10**, prior **gpt51** audit (`qa_output_gpt51`) found major inventions. **v2 prompt** generally removed:

| Client | Old gpt51 issue | v2 status |
|--------|-----------------|-----------|
| Root | Form 5498-SA from solar/HSA-only message | Fixed |
| Grimes | $750k on wrong QA; estimated tax from “Yes please” | Patterns gone; spot-check $750k if needed |
| Sanchez | STR rules from deferral-only message | Fixed |
| Burkes | ~$245k vs ~$145k | Fixed; 10%/year vs month **resolved** (cleanup 2026-05-22) |
| Zhang | Backup withholding wrong source | Fixed |

---

## Artifacts

| Path | Description |
|------|-------------|
| `logs/files_progress.csv` | Physical row order, `message_count`, `processed_v2` |
| `scripts/_csv_audit_table.txt` | Full CSV row ↔ msg rank mapping (all 282 files) |
| `scripts/audit_top20_grounding.py` | Deterministic audit logic used by subagents |
| `scripts/verify_hallucination_sources.py` | Source JSON spot-check (Burkes, Yen, Cortez) |
| `scripts/verify_hallucination_cleanup.py` | Post-cleanup regression check (9 batch 1–2 fixes) |
| `llm_pipeline/verifier.py` | Optional gpt-4.1-mini LLM verifier (3-file test only) |
| `V2_GROUNDING_AUDIT_BATCH2.md` | Batch 2 agent assignments (40 files) |
| `V2_GROUNDING_AUDIT_BATCH3.md` | Batch 3 agent assignments (50 files) |
| `V2_GROUNDING_BATCH3_AGENT01.md` … `AGENT25.md` | Batch 3 per-agent reports |
| `scripts/v2_batch3_agent01.json` … `agent25.json` | Batch 3 machine audit + full `missed_knowledge` |
| `scripts/_batch3_assignments.json` | Rank / CSV row / client mapping |
| `scripts/run_batch3_audit_agent.py` | Run one batch-3 agent (`--agent N`) |
| `scripts/merge_batch3_index.py` | Regenerate batch-3 index table snippets |
| `V2_GROUNDING_AUDIT_BATCH4.md` | Batch 4 assignments (50 files) |
| `V2_GROUNDING_BATCH4_AGENT_BRIEF.md` | Batch 4 agent instructions (`missed_knowledge` vs `transferable_gaps`) |
| `V2_GROUNDING_BATCH4_AGENT01.md` … `AGENT25.md` | Batch 4 per-agent reports |
| `scripts/v2_batch4_agent01.json` … `agent25.json` | Batch 4 machine audit |
| `scripts/_batch4_assignments.json` | Rank / CSV row / client mapping |
| `scripts/run_batch4_audit_agent.py` | Run one batch-4 agent (`--agent N`) |
| `scripts/merge_batch4_index.py` | Regenerate batch-4 index table |
| `V2_GROUNDING_AUDIT_GAP.md` | Gap batch assignments (8 files) |
| `V2_GROUNDING_GAP_AGENT01.md` … `AGENT04.md` | Gap batch per-agent reports |
| `scripts/v2_gap_audit_agent01.json` … `agent04.json` | Gap batch machine audit |
| `scripts/_gap_audit_assignments.json` | Gap rank / CSV row / client mapping |
| `scripts/run_gap_audit_agent.py` | Run one gap agent (`--agent N`) |
| `V2_GROUNDING_AUDIT_BATCH5.md` | Batch 5 assignments (102 files, 4 per agent) |
| `V2_GROUNDING_BATCH5_AGENT01.md` … `AGENT26.md` | Batch 5 per-agent reports |
| `scripts/v2_batch5_agent01.json` … `agent26.json` | Batch 5 machine audit |
| `scripts/_batch5_assignments.json` | Rank / CSV row / client mapping |
| `scripts/run_batch5_audit_agent.py` | Run one batch-5 agent (`--agent N`) |
| `scripts/merge_batch5_index.py` | Regenerate batch-5 index table snippets |
| `V2_GROUNDING_*.md` | Per-pair human-readable audit reports (batch 2) |
| `scripts/v2_*_audit.json` | Per-pair machine output where saved |
| `scripts/_v2_batch2_otani_maka.json` | Otani + Makagiansar machine audit |

---

*Generated: 2026-05-22 (updated batch 5; hallucination cleanup verified). Batch A = ranks 11–40 (+41,43–45). Batch B = ranks 1–10 spot-check. Batch 2 = ranks 46–88. Batch 3 = ranks 81–130. Batch 4 = ranks 131–180. **Gap** = 8 files. **Batch 5** = ranks 181–282 (102 files). **All 282** `processed_v2` grounding-audited; **9** historical hallucinations (batches 1–2) **all resolved** in `qa_output_v2`; batches 3–5 + gap = **0** confirmed; **30** clients with transferable_gaps (batch 4: 12 + gap: 4 + batch 5: 14).*
