# Evaluation guide — independent review findings (2026-06-08)

Five fresh, independent reviewer agents (no access to the build reasoning) audited the
complete guide along the dimensions in `REVIEW_BRIEF_2026-06-08.md`. This is the
deduped, severity-ranked, **synthesis** — top items re-verified by hand (marked ✓VERIFIED).

## Verdict

The guide is in good shape. **Build is green** (`book-scaffold validate ✓ 13 chapters`,
19 pages, all 9 island chunks bundled, **0 `undefined`/`NaN` in rendered pages**), all
**12 island↔JSON data contracts are clean**, **all prose numbers are honest** save one
code-comment, the generated data is **deterministic**, factual claims are overwhelmingly
correct, and **19/19 companion tests pass**. The defects are: one wrong number in a code
comment, structural anchor bookkeeping, several real-but-latent companion math bugs (none
surfaced in any chapter), and a set of editorial/terminology judgment calls.

Reviewer tallies (raw, pre-dedup): math 1B/3M/4m/2n · demo-honesty 0B(det. clean)/1M/2m/1n
· factual 1B/1M/4m/3n · pedagogical 3 dangling-anchor B/2M/3m/2n · island+MDX 0B/0M/2m/2n.

---

## TIER 1 — Must-fix (correctness / rubric-breaking; user-visible or build-invisible-but-promised)

### 1. ✓VERIFIED — `pass@k` code comment is wrong  ·  `10-agentic-task-eval.mdx:111`
Found independently by the demo-honesty **and** factual reviewers; reproduced by hand.
Comment says `pass_at_k(n=10, c=4, k=5)   # ~0.93`, but the function the chapter is
*teaching* returns **0.9762**. (`0.93` is the k=4 value, 0.9286.) Runnable snippet in the
defining chapter → a reader who runs it sees the contradiction.
**Fix:** change the comment to `# ~0.98 — at least one of 5 tries works` (0.98 also better
makes the "looks near-perfect" point). *(Alt: change `k=5`→`k=4` to match 0.93 — but 0.98 is better pedagogy.)*

### 2. ✓VERIFIED — three dangling LOS anchors  ·  `06:43` `07:44` `08:43`
Each chapter's third learning objective (the `design`-bloom LOS) declares an `anchor:` in
frontmatter that has **no** matching `{/* anchor: … */}` in prose (confirmed: frontmatter=1,
prose=0 for each). The build cannot catch this. The teaching content exists; only the marker is missing.
- `06-reference-based-vs-free.mdx` — add `{/* anchor: ref-choose */}` to the route-by-checkability prose (~line 122–124, or the `<Practice>` lead-in).
- `07-llm-as-judge.mdx` — add `{/* anchor: judge-mitigation */}` to the swap-and-aggregate/debias prose (~line 121–122).
- `08-benchmark-literacy.mdx` — add `{/* anchor: bench-read */}` to the "which of the three? = the literacy" prose (~line 131–133).

### 3. ✓VERIFIED — Ch9 orphan prose anchor  ·  `09-rag-evaluation.mdx:122`
Inverse of #2: prose has **4** anchors (`rag-decompose`, `rag-retrieval-metrics`,
**`rag-faithfulness`**, `rag-diagnose`) but frontmatter declares only **3** LOS. Make the
sets bijective like every other chapter. **Fix (pick one):** (a) drop `{/* anchor: rag-faithfulness */}`
from line 122 if EVAL-9.2 already covers faithfulness, or (b) add/retarget a 4th LOS for the
faithfulness objective. *(Recommend (b): faithfulness is a distinct objective worth its own LOS.)*

---

## TIER 2 — Should-fix (real code/content defects — mostly latent today, or editorial)

### 4. ✓VERIFIED — `average_precision` is order-dependent on tied scores  ·  `metrics.py:103-124`
Same score vector, three orderings → **AP = 0.833 / 1.0 / 0.417** (correct answer for that
input is 0.5). Wrong whenever scores tie (common with calibrated/quantized scores). **Not**
surfaced as a quoted number in any chapter, so invisible to a reader today — but a learner
running the function gets a number that secretly encodes list order. **Fix:** group items by
score and accumulate `prec·Δrecall` once per score level (sklearn behavior).

### 5. `recall_at_k`/`precision_at_k` count duplicate retrievals  ·  `retrieval.py:20-33`
`recall_at_k(['a','a'], {'a'}, 2)` returns **2.0** (impossible). Demo uses distinct chunk
IDs so it's latent. **Fix:** `hits = len(set(retrieved[:k]) & relevant)`.

### 6. Tests use degenerate inputs — don't exercise estimator middles  ·  `test_mini_eval.py`
AP / permutation / Brier are tested only at saturated endpoints (perfect-vs-nothing, 0/1);
they'd pass even if the interior logic were wrong (and indeed the AP test cannot catch #4).
**Fix:** add one closed-form interior assertion each (e.g. AP of `[1,0,1,1,0]` desc ≈ 0.8056;
Brier of `[1,0]`@`[0.7,0.2]` = 0.065; a moderate-gap permutation p in a checked range).

### 7. `judge.py` "unbiased ⇒ flip_rate 0" is false on equal-quality pairs  ·  `judge.py:55-57,68-74`
`>=` tie-break sends ties to the first response, so an equal-quality equal-length pair always
"flips," contradicting the docstring. Demo uses unequal qualities → latent. **Fix:** treat
near-ties as no-decision (don't count as flips), or document the restriction + add a test.

### 8. "Type-I / Type-II hallucination" is non-standard terminology  ·  `09` (62, 164-174, 188, 213)
The field standard is **intrinsic/extrinsic** (or generation-side/retrieval-side); presenting
"the Type-I/II hallucination split" as if standard risks a knowledgeable reader/interviewer.
The analogy is internally coherent. **Fix (editorial):** rename to "generation-side / retrieval-side"
(optionally noting intrinsic/extrinsic), **or** keep the mnemonic but explicitly flag it as a
borrowed analogy to false-positive/false-negative, not a standard taxonomy.

### 9. Three "single most common failure" superlatives, asserted as fact  ·  `00:70` `01:71` `12:162`
Three chapters each assert a *different* "the most common reason candidates fail" as a hard,
ranked statistic, sourced only to the (private, unciteable) demand research. Honesty/credibility
risk **and** internal inconsistency. The specific Ch1-"most"/Ch12-"second-most" pair is itself
consistent. **Fix (editorial):** soften modality ("a very common…") and/or designate one canonical
#1 and have the others reference it as the same gap.

### 10. RAGAS "triad" undercounts  ·  `09:122-133`
RAGAS's canonical core is **four** metrics (faithfulness, answer relevancy, context precision,
context recall). **Fix:** "the RAGAS metrics," or regroup to honestly total three.

### 11. Temperature scaling "$T>1$" stated as the definition  ·  `04:148`
T>1 is the overconfidence-fix case, not the general definition (T<1 sharpens). **Fix:**
"divide the logits by a single learned scalar $T$ (with $T>1$ softening an overconfident model)."

---

## TIER 3 — Polish (minors / nits)

- **`02:138`** — "**four** legitimate for every real fraud" rounds 3.55 up; say "about three or four" / "~3.5".
- **`metrics.py:100`** — `threshold_sweep(n_steps=1)` → ZeroDivisionError; guard `n_steps >= 2`.
- **`PassAtKExplorer.tsx:72`** — caption hardcodes "The flaky agent"; under the *Reliable* tab it reads "The flaky agent… 79%". Number is correct; use `{s.label}`. *(Found by 2 reviewers.)*
- **`11:182`** — "the same independent-then-reconcile move from the start of the guide" — no such move is introduced; drop the callback or introduce it.
- **`01:86`** — "(Chapter 2 **turned** …)" past-tense forward ref; make present/future.
- **`08:103`** — saturation "89–91%" vs the quiz JSON's 89–90.3%; align to "89–90%".
- **`ConfidenceExplorer.tsx:50`** — CI bar has no upper clamp; defensive `Math.min(1, …)` (safe today, max hi 0.847).
- **`retrieval.py:20-25`** — precision denominator is `k` even when fewer than k retrieved; document the convention.
- **`05:56`** — `<YouWillLearn>` lists Ch8 (downstream) as a *prerequisite*; reword to "pairs with Chapter 8". *(Found by 2 reviewers.)*
- **`04:192`** — "(the Chapter 1 stretch)" loosely characterizes Ch1's actual stretch; soften to "cf.".
- **`JudgeBiasExplorer.tsx:17`** — `verbosity` typed but never read (dead field); drop or wire up.
- **`11:126`** — lone `$` (currency) in a math-enabled chapter; renders fine, optional `\$`.
- **`03:210`** — "twenty tests → one false positive" is correct; optional add "(~64% chance of ≥1)".
- **`confidence.py:108`, `141`; `calibration.py:60-61`** — boundary/sentinel conventions are correct; add one-line doc notes.

---

## Non-defect (do not "fix")

- **Ch0 omits the teaching template** — intentional (`mode: explanation`, orientation chapter).
  Not a defect; just note the exemption so future template-lint runs don't re-flag it.

## After applying fixes
Re-run the verification block (`python3 companion/tests/test_mini_eval.py`;
`python3 scripts/build_demo_data.py && git diff --stat src/data` → no change; `npm run build`).
If #6 (test hardening) lands, expect the test count to rise above 19. Then the publish bar
is clean for the push decision (user's call).

---

## Resolution — applied 2026-06-09 (all three tiers)

Every finding above was addressed. User decisions: keep the Type-I/II **mnemonic but flag
it** (#8); **soften** the superlatives (#9). Two findings resolved by judgment rather than a
code change, with rationale.

**Tier 1 (all fixed & verified in rendered HTML):**
- #1 `10:111` — comment now `# ~0.98` (confirmed `pass_at_k(10,4,5)=0.9762`; rendered HTML shows 0.98).
- #2 — added `{/* anchor: ref-choose */}` (06, on `## See it`), `{/* anchor: judge-mitigation */}`
  (07, after the debias paragraph), `{/* anchor: bench-read */}` (08, on `## See it`).
- #3 — removed the orphan `{/* anchor: rag-faithfulness */}` (09). Chose drop-the-orphan over
  add-a-4th-LOS: lowest-risk, keeps 3 LOS, and faithfulness stays covered by EVAL-9.2's statement.
- **Anchor bijection audit now passes for all 13 chapters** (fm == prose, 3/3 each).

**Tier 2:**
- #4 `metrics.py` — `average_precision` groups tied scores; verified order-independent
  (0.5 for all three orderings of the tie case; interior `[1,0,1,1,0]` = 0.8056). Docstring
  corrected to "sum of precision × Δrecall (no interpolation)".
- #5 `retrieval.py` — `precision_at_k`/`recall_at_k` count distinct hits (`set(...) & relevant`);
  recall on `['a','a']`/`{'a'}` now 1.0, not 2.0.
- #6 `test_mini_eval.py` — **+5 interior tests** (AP ties+order-independence+interior, Brier
  interior, moderate-gap permutation with monotonicity, retrieval dedup, judge equal-pair).
  Suite **19 → 24, all pass**.
- #7 `judge.py` — `position_flip_rate` now skips exact ties (added `_decisive`); an unbiased
  judge scores 0 on an equal-quality pair. Demo `position_flip_rate` unchanged (no ties in data).
- #8 `09` — flagged the Type-I/II label as a borrowed mnemonic (not standard; lit. uses
  intrinsic/extrinsic) at its definition NoteBox; kept the device.
- #9 `00`,`01`,`12` — softened "the single most common…" → "one of the most common / a very
  common…"; also softened `12:74` "second-most-common" for consistency (no dangling ranking).
- #10 `09` — "the RAGAS triad" → "the core RAGAS metrics" (RAGAS core is four).
- #11 `04` — temperature scaling reworded to "a single learned scalar $T$ — here $T>1$, softening
  an overconfident model".

**Tier 3:** `02` "four"→"about three or four" (3.55:1); `metrics.py` `threshold_sweep` guards
`n_steps>=2`; `PassAtKExplorer` caption scenario-aware (`{s.label}`, `pass@{s.K}`, "only"→neutral);
`11` phantom "independent-then-reconcile" callback replaced; `01:86` past-tense forward-ref → present;
`08:103` saturation "89–91%"→"89–90%" (matches quiz JSON); `ConfidenceExplorer` CI bar clamped to [0,1];
`retrieval`/`confidence`/`calibration` boundary-convention doc notes added; `JudgeBiasExplorer` dead
`verbosity` type member dropped; `03:210` added "(~64% chance of at least one)".

**Two findings resolved by judgment, not edits (with rationale):**
- **Ch11 lone `$` (`11:126`)** — left unescaped. It renders as currency `$2` (confirmed in HTML),
  matches the guide's convention (`$10` in Ch9 also unescaped), and escaping just one would be
  inconsistent and risk a visible backslash. Confirmed non-issue.
- **Ch0 template exemption** — unchanged by design (orientation chapter, `mode: explanation`).

**Verification (2026-06-09):** `test_mini_eval.py` → **24/24, exit 0**; demo JSON **byte-identical**
after regenerate (companion edits changed no demo number); `npm run build` → **`validate ✓ 13
chapters; no errors`, 19 pages, all 9 island chunks**, only the pre-existing `/` route-collision WARN.
Rendered-HTML spot-checks (0.98, scenario-aware caption with no leaked JSX, `$2`, Type-I/II flag,
`core RAGAS metrics`, 89–90%, KaTeX in 03/04/09/10) all confirmed. **Publish bar clean; push is the user's call.**
