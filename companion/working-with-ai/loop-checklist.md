# The working-with-AI loop — checklist

> The six stages (Ch 0). Five run in sequence; the sixth runs the whole time. Each is a stage you can
> skip under pressure — and each skipped stage is an anti-pattern (Ch 8). Run the list until it's reflex.

## 1. Clarify (Ch 2) — *scores Trade-off Awareness*
- [ ] Restated the problem in my own words.
- [ ] Found and resolved the pivotal term (the word the solution turns on).
- [ ] Narrated any assumption I couldn't get answered, and kept it swappable.

## 2. Preregister (Ch 3) — *scores Evaluation Rigor*
- [ ] Committed the shape (interface / units).
- [ ] Committed the invariants (incl. the one guarding the hidden failure).
- [ ] Wrote the boundary tests **from the spec**, before prompting.

## 3. Prompt (Ch 4) — *scores Trade-off Awareness*
- [ ] Handed over the spec (invariants + constraints), not a wish.
- [ ] Decided one-shot vs decompose by where the architecture/risk lives.
- [ ] Stated the constraints, including the negatives (no new deps, keep the signature).

## 4. Review (Ch 5) — *scores Technical Correctness*
- [ ] Read against the spec, not for style — read hardest where it looks cleanest.
- [ ] Checked the boundaries first; verified comments against the code.
- [ ] I can explain every line I'm about to accept.

## 5. Run (Ch 6) — *scores Evaluation Rigor*
- [ ] Ran the **preregistered gate**, not the handed-down example.
- [ ] Treated the gate as binary; didn't negotiate with happy-path green.
- [ ] On failure: fed the **specific** failure back as the debugging prompt.

## 6. Explain (Ch 7) — *scores Communication (the weighted dimension), throughout*
- [ ] Led with intent and the pivotal decision, not the keystrokes.
- [ ] Voiced the delegate/verify split ("I'll take X, but I'm checking Y myself, because…").
- [ ] Rewrote vague into specific out loud; stated how I verified, unprompted.

---

**At scale (Ch 9–11):** apply the loop to *units*, not lines — the plan is your preregistration,
checkpoints are your gates; govern the seams + the gate + the riskiest units; own what you approve.
