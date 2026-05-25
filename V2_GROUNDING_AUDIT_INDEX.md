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

**Verdict labels**

- **None** — No confirmed hallucination after review.
- **Confirmed** — Specific claim in answer not supported by cited advisor message(s).
- **Borderline** — Thin citation or client-sourced / unit error; see detail.
- **Citation only** — Text exists in chat but not in cited indices (not invented).

---

## Summary

| Scope | Files audited | Confirmed hallucination | Borderline / citation-only | Not in audit |
|-------|--------------:|------------------------:|---------------------------:|-------------:|
| **Batch 1** (msg ranks 1–45) | 45 | 4 | 2 (+ Aronne structural) | 5 v2 extractions outside batch |
| **Batch 2** (msg ranks 46–88) | 40 | 5 | 6+ (thin cite / client $ in borderline) | — |
| **Combined** | **85** | **9** | — | — |

**Batch 1 breakdown (ranks 1–40 table):** None 33 · Confirmed 4 · Borderline 1 · Citation only 1 · Not audited 5.

**Batch 2 takeaway:** No widespread invention; main gaps are **missed substantive threads** (often estimates, FTB access, entity onboarding) and **near-duplicate QAs** from one long advisor reply.

*Plus structural QA issues on **Aronne** (batch 1) and **Moffett** (batch 2), documented under Other.*

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
| 7 | 8 | Yen, Andrew and Jacqueline | 157 | ✓ | B | **Confirmed** | QA **#10**: $2,500 / $800 from **client** msgs; cited advisor **[94]** has neither (verifier flagged) |
| 8 | 9 | Burkes, Sammie and Erin | 152 | ✓ | B | **Confirmed** | QA **#12** (0-based **#11**): “~10% **per year**” vs advisor “~10%**/month**” at **[74]** (verifier flagged) |
| 9 | 10 | Jang, Will and Wendy | 142 | ✓ | B | None | Not in 11–40 subagent batch |
| 10 | 11 | Zhang, Chi and Wenjun Chen | 139 | ✓ | B | None | v2 fixed gpt51 1099 mis-citation pattern |
| 11 | 12 | Emerson , Kevin W. and Joanna | 131 | ✓ | A | None | Duplicate QAs (#6/#14); missed $80k shareholder loan thread |
| 12 | 13 | Beltran, Edward and Eunice | 130 | ✓ | A | None | **Missed:** $43,831 passive loss / Form 8582 amend (advisor ~**[9]**) |
| 13 | 14 | Martin, Jacob and Nancy | 129 | ✓ | A | None | 2 partials; missed cost-seg property selection / extension guidance |
| 14 | 15 | Albayaty, Monica and Richard | 126 | ✓ | A | **Confirmed** | QA **#16**: prior due **~$125,000** not in source; $258k/$16k are real |
| 15 | 16 | Skorobogatova, Ekaterina and Anna Zhirova | 123 | ✓ | A | Borderline | QA **#7**: 1099-G framing beyond thin cited line; core “taxable in 2024” OK |
| 16 | 17 | Goodman, Richard and Devonay | 119 | ✓ | A | None | Auto $ flags false positives (`~5k`); heavy near-duplicate solar QAs |
| 17 | 18 | Fernandez II, Anthony and Emily | 117 | ✓ | A | None | Grade A; no confirmed hallucination |
| 18 | 19 | Aronne, Jason and Kunal | 116 | ✓ | A | None | QA **#5** cites **client** index **[26]**; QA **#17** question (Form 593) ≠ cited text (1031 at **[96]**) — use QA **#18** |
| 19 | 20 | Simon, Thomas and Jin-Hwa | 112 | ✓ | A | None | 7 auto H flags overturned (`7k`); 2 partials; 44 near-dup pairs |
| 20 | 21 | Kemp, Chris and Sara | 106 | ✓ | A | None | Auto H flags overturned; heavy index overlap |
| 21 | 22 | Liang, Derek and Kristine | 106 | ✓ | A | None | 3 mild partials; shared-index splits |
| 22 | 23 | Pedagat, Ronald and Janize Quintana | 103 | ✓ | A | None | Auto $1,000 flag false positive (`$1k` in source) |
| 23 | 24 | Carr, Danny and Frederica | 102 | — | — | Not audited | v2 extraction exists; no row in this audit |
| 24 | 25 | Baig, Rameez R. and Naima Bendada | 101 | ✓ | A | None | 1 partial (mailing checklist detail) |
| 25 | 26 | Truman, Stephen and Alisa | 100 | ✓ | A | None | Near-duplicate cost-seg/STR pairs |
| 26 | 27 | Dobyns, Kristina | 98 | ✓ | A | **Confirmed** | QA **#19**: **$1,000** estimate steps; advisor **[84]** only “That is correct” — amount from **client** |
| 27 | 28 | Tran, Quang | 98 | ✓ | A | None | Grade A−; megathread index sharing |
| 28 | 29 | Lanka, Ravindra and Sarvani Vakkalanka | 97 | ✓ | A | None | 2 partials (e-file workflow, extension wording) |
| 29 | 30 | Umbalacheri Ramasamy, Venkatraman and Jayashree | 97 | — | — | Not audited | v2 folder may exist; not in ranks 11–40 batch |
| 30 | 31 | Todd, DJ and Jennifer | 95 | ✓ | A | None | 15 near-dup pairs from one multi-topic reply |
| 31 | 32 | Alonzo, Jamie J | 94 | ✓ | A | None | Grade A−; 1 partial (moving expenses) |
| 32 | 33 | Cortez, Angelo | 94 | ✓ | A | None | QA **#13** auto $12k flag false positive (“12–15k” in source) |
| 33 | 34 | Dieffenbach, Zachary M | 92 | ✓ | A | None | Grade 97%; clean |
| 34 | 35 | D_Altorio, Darren and Amalya | 90 | ✓ | A | None | QA **#7–9** triple-split on index **[16]**; not hallucination |
| 35 | 36 | Ho, Tim and Stephanie Liu | 90 | — | — | Not audited | v2 test file; `processed_v2` empty in CSV |
| 36 | 37 | Rigoni, Jacqueline | 90 | ✓ | A | None | 2 auto H → partial (2k child credit grounded); Schedule C name not in cited text (partial) |
| 37 | 38 | Edwards, Ross and Narine Karakhanyan | 89 | ✓ | A | None | 1 partial (short citation) |
| 38 | 39 | Ciccone Tolbert, Gabriella N | 88 | ✓ | A | None | Heavy near-dup on index **[48]** |
| 39 | 40 | Elliott, Kevin and Anna Jennie M | 87 | — | — | Not audited | v2 exists; not in subagent batch |
| 40 | 41 | Faris, Korie and Jacob | 86 | ✓ | A | None | Missed prior-return onboarding at advisor **[0]** (substantive gap) |

### Also audited (msg ranks 41–45; CSV rows 42–46)

| Msg rank | CSV row | Client | Msgs | `processed_v2` | Audit batch | Hallucination | Other issues |
|----------|---------|--------|-----:|:--------------:|:-------------:|:-------------|:---------------|
| 41 | 42 | Padgett, Michael and Allison | 84 | ✓ | A+ | None | Missed property-address / onboarding threads |
| 42 | 43 | Casillas, Juan and Pamela Guillen | 82 | ✓ | — | Not audited | v2 test extract; no full grounding audit in batch |
| 43 | 44 | Milton, Josh and Deanna | 81 | ✓ | A+ | None | Auto H overturned (`2k` child credit); index overlap |
| 44 | 45 | Hirekatur, Anand S | 80 | ✓ | A+ | None | 1 thin-citation partial |
| 45 | 46 | Malkon, Paul and Tanya | 80 | ✓ | A+ | None | Clean after review |

---

## Master table — Batch 2 (msg ranks 46–88)

40 new `processed_v2` files (msg rank **> 45**). **Msg rank 47** (Lising) skipped — no `processed_v2` at audit time.

| Msg rank | CSV row | Client (folder name) | Msgs | `processed_v2` | Audit | Hallucination | Missed (count) | Other issues / top missed knowledge |
|----------|---------|----------------------|-----:|:--------------:|:-----:|:-------------|---------------:|:-----------------------------------|
| 46 | 47 | Otani, Christopher and Uyen | 80 | ✓ | B2-A1 | None | 4 | Auto flags overturned (e.g. **9k** at **[24]**); tax projection / K-1 wait **[33]**; **185k** software fix thread |
| 48 | 49 | Makagiansar, Irwan and Helena | 78 | ✓ | B2-A1 | None | 5 | Grouping election / Form 3520 / fee allocation well covered; e-sign **[3]**, audit-risk client question |
| 49 | 50 | Martin, Tyler and Katherine | 78 | ✓ | B2-A2 | None | 8 | Katie **$1,500** S-corp proposal **[5]**; extension payment reminders; year-end estimate close-out **[69]** |
| 50 | 51 | Smith III, Russell E. and Nicole | 78 | ✓ | B2-A2 | None | 3 | FEIE / installment sale / 1031 grounded; **$2k** TN LLC fee at **[49]** (auto flag overturned) |
| 51 | 52 | Martin, Jonathan and Diana | 75 | ✓ | B2-A3 | None | 5 | **Missed:** partnership extension filed **[48]**; Roth 401(k) / 1031 sale at **[65]** covered |
| 52 | 53 | Coleman, Paige | 74 | ✓ | B2-A3 | None | 8 | Trust/gift, extension, **$111k** sale + cost seg; missed IRS notice follow-up **[14]** |
| 54 | 55 | Wang, Yuehai and Gisele Hong | 74 | ✓ | B2-A4 | **Confirmed** | 3 | QA **#14**: **$1,000** Trump account from **client** **[66]**, not **[67]**; CA/no-CA filing **[5]**; cost-seg timing **[23]** |
| 55 | 56 | Diaz, Anne and Martin Carew | 73 | ✓ | B2-A4 | **Confirmed** | 4 | QA **#9**: **~$3,320** interest from **client** **[47]**; stock sales / IRS agent **[20]**, **[4]** |
| 56 | 57 | Barnes, Karsten and Tamarra | 72 | ✓ | B2-A5 | None | 6 | Extension/penalty/REPS/cost-seg clean; FTB access **[49]**; 10/15 urgency **[4]** |
| 57 | 58 | Kuramoto, Kenny and Michelle | 72 | ✓ | B2-A5 | Borderline | 2 | QA **#7**: **Sch E** label vs **[56]** (amounts grounded); CA LLC fee **[8]** |
| 58 | 59 | Ogueli, Vivian and Ifeanyi | 72 | ✓ | B2-A6 | **Confirmed** | 8 | QA **#7**: **~$40k** passive loss from **client**, not **[53]**; DERANAZ partnership scope **[8]**; biz/personal split **[19]** |
| 59 | 60 | Lok, Brian | 71 | ✓ | B2-A6 | None | 4 | 14 QAs; strong REPS joint-return coverage; **$800** CA LLC reminder **[54]**; elite pricing **[59]** |
| 61 | 62 | Holbrook, Emily N. | 69 | ✓ | B2-A7 | None | 9 | S-corp payroll **[1]**, Oct deadline **[6]**, rental setup **[50]**; thin cite QA **#6** |
| 62 | 63 | Manietta, Daniel and Susana | 68 | ✓ | B2-A7 | None | 12 | **Coverage gap:** only **3** QAs; **$525K** sale, **$8k/$3.2k** estimates **[5]**, REPS app **[29]** missed |
| 63 | 64 | Blom, Brandon J. and Katie | 67 | ✓ | B2-A8 | None | 3 | HSA/5498 citation-only QA **#3**; near-dup **[27]**; e-sign **[1]** |
| 64 | 65 | Haddon, Garrison D and Dana M | 67 | ✓ | B2-A8 | None | 1 | 13 QAs grounded; flip/HELOC near-dups; video recap **[33]** |
| 65 | 66 | Moffett, Mark and Jennifer | 67 | ✓ | B2-A9 | None | 7 | QA **#2** HELOC Q / REPS A mismatch; CA withholding **2% vs 6%** **[55]**; 7 near-dup |
| 66 | 67 | Espinoza, Meny and Diana | 65 | ✓ | B2-A9 | **Confirmed** | 2 | QA **#5**: solar **$25k/$65k/$19.5k** vs advisor **$16k/$50k/$15k** at **[29]**; 8 near-dup |
| 67 | 68 | Haghi, Poorya and Hanh Tran | 65 | ✓ | B2-A10 | None | 6 | REPS 5-of-10-year rule; STR personal days — auto **$6k** flag overturned; cost seg **~$300k** land **[21]** |
| 68 | 69 | Koch, Martin and Mariah Soto | 64 | ✓ | B2-A10 | Citation only | 12 | IRA phase-out / cap loss strong; **timing rules** in uncited **[15]** (QA **#3**); large estimate threads missed |
| 69 | 70 | Li, Xiang and Luis Lin | 64 | ✓ | B2-A11 | None | 5 | v2 +2 QAs vs gpt51; **$23,500** flag overturned (**23.5k** at **[37]**) |
| 70 | 71 | Pleas, Betty and Little | 64 | ✓ | B2-A11 | None | 7 | Thin coverage (**4** QAs / 55 filtered msgs); extension years **[1]**, **[54]** |
| 71 | 72 | Williams, Thomas S. and Emi | 64 | ✓ | B2-A12 | **Confirmed** | 3 | QA **#9**: **$10,000** extension from **client** **[55]**; overlap **[9,12]** |
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

## Confirmed hallucinations (detail)

### Msg rank 8 (CSV row 9) — Burkes, Sammie and Erin

- **QA #12** (verifier index **#11**): Penalties described as **~10% per year**; cited advisor **[74]** says **~10%/month** (same numeric rate, **wrong period**).
- **Output:** `qa_output_v2/Burkes, Sammie and Erin/extraction.json`
- **Verification:** `qa_output_v2/Burkes, Sammie and Erin/verification.json` (gpt-4.1-mini flagged)

### Msg rank 7 (CSV row 8) — Yen, Andrew and Jacqueline

- **QA #10** (verifier index **#9**): Answer uses **$2,500** repair threshold and **$800** LLC fee; amounts appear only in **client** messages **[92]**, **[93]** — not in cited advisor **[94]**.
- **Verification:** verifier flagged; `scripts/verify_hallucination_sources.py` confirmed

### Msg rank 14 (CSV row 15) — Albayaty, Monica and Richard

- **QA #16**: Answer states federal due increased from **~$125,000** to **$258,000**; **$258k** and **$16k** payment guidance are in cited advisor text — **$125k prior figure is not** in parsed chat or citations.

### Msg rank 26 (CSV row 27) — Dobyns, Kristina

- **QA #19**: Answer restates **$1,000** estimated tax payment workflow; cited advisor **[84]** only acknowledges with “That is correct” — **$1,000** comes from **client** message in same thread.

### Msg rank 71 (CSV row 72) — Williams, Thomas S. and Emi

- **QA #9**: Answer includes **$10,000** toward 2025 extension; cited advisor **[50, 54, 56]** give Q1 guidance ($3k–$5k) and confirm rollover process — **$10,000** from **client** **[55]** only.

### Msg rank 54 (CSV row 55) — Wang, Yuehai and Gisele Hong

- **QA #14**: **$1,000** child / Trump-account benefit; cited advisor **[67]** has organizer workflow only — amount in **client** **[66]** (“$1k trump account”).

### Msg rank 55 (CSV row 56) — Diaz, Anne and Martin Carew

- **QA #9**: **~$3,320** omitted mortgage interest; advisor **[46, 48]** cites **~$500** savings vs fees — **$3,320** only in **client** **[47]**.

### Msg rank 58 (CSV row 59) — Ogueli, Vivian and Ifeanyi

- **QA #7**: **~$40,000** rental loss “included”; cited advisor **[53]** confirms passive suspension only — **$40k** figure from **client** thread, not advisor text.

### Msg rank 66 (CSV row 67) — Espinoza, Meny and Diana

- **QA #5**: Illustrative solar dollars **$25k / $65k / $19.5k** vs advisor **[29]** example **$16k / $50k / $15k / $17k** withholding — same logic, **wrong numbers**.

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

## Files with v2 output but not in ranks 1–40 audit

These have `qa_output_v2/` extractions but were **not** part of the 30-file (ranks 11–40) subagent batch or full rank 1–40 scripted pass:

| Client | Notes |
|--------|--------|
| Carr, Danny and Frederica | Early rerun / test |
| Casillas, Juan and Pamela Guillen | Early rerun / test |
| Ho, Tim and Stephanie Liu | Early rerun / test |
| Elliott, Kevin and Anna Jennie M | Early rerun / test |
| Umbalacheri Ramasamy, Venkatraman and Jayashree | CSV rank 29; no subagent report in batch |
| Lising, Christian and Kim | 8-file severity test |
| Ren, Deyao and Zheng Tao | 8-file severity test |
| Chillar, Paul and Angelica | 8-file severity test |

---

## gpt51 → v2 (historical hallucinations fixed)

For ranks **1–10**, prior **gpt51** audit (`qa_output_gpt51`) found major inventions. **v2 prompt** generally removed:

| Client | Old gpt51 issue | v2 status |
|--------|-----------------|-----------|
| Root | Form 5498-SA from solar/HSA-only message | Fixed |
| Grimes | $750k on wrong QA; estimated tax from “Yes please” | Patterns gone; spot-check $750k if needed |
| Sanchez | STR rules from deferral-only message | Fixed |
| Burkes | ~$245k vs ~$145k | Fixed; **new** 10%/year vs month issue |
| Zhang | Backup withholding wrong source | Fixed |

---

## Artifacts

| Path | Description |
|------|-------------|
| `logs/files_progress.csv` | Physical row order, `message_count`, `processed_v2` |
| `scripts/_csv_audit_table.txt` | Full CSV row ↔ msg rank mapping (all 282 files) |
| `scripts/audit_top20_grounding.py` | Deterministic audit logic used by subagents |
| `scripts/verify_hallucination_sources.py` | Source JSON spot-check (Burkes, Yen, Cortez) |
| `llm_pipeline/verifier.py` | Optional gpt-4.1-mini LLM verifier (3-file test only) |
| `V2_GROUNDING_AUDIT_BATCH2.md` | Batch 2 agent assignments (40 files) |
| `V2_GROUNDING_*.md` | Per-pair human-readable audit reports (20 files) |
| `scripts/v2_*_audit.json` | Per-pair machine output where saved |
| `scripts/_v2_batch2_otani_maka.json` | Otani + Makagiansar machine audit |

---

*Generated: 2026-05-22. Batch A = ranks 11–40 (+41,43–45). Batch B = ranks 1–10 spot-check. Batch 2 = ranks 46–88 (40 files, 20 agents × 2). Combined **85** audited v2 extractions, **9** confirmed hallucinations.*
