# Self-grading rubric — AI-assisted work

> The four dimensions interviewers score (Ch 1), turned into a checklist you run on your own attempt
> (Ch 12). Score each 0–2: **0** absent · **1** present but weak · **2** clear and unprompted. With the
> typing automated, an interviewer can only see what you *say and check* — so grade what would have been
> visible to an observer, not what you did in your head.

## Technical Correctness — *can you reason about code you didn't type?*
- [ ] I can explain every accepted line and **name where it breaks**, not "it looks fine".
- [ ] I caught issues by reading **against the spec**, not by style.
- [ ] When the AI and my own check disagreed, I **resolved it** rather than deferring.

Score: ___ / 2

## Trade-off Awareness — *did you aim and decide on purpose?*
- [ ] I clarified the pivotal term before delegating.
- [ ] I chose one-shot vs decompose by where architecture/risk lives — out loud.
- [ ] I sized verification and scope to the stakes, not all-or-nothing.

Score: ___ / 2

## Evaluation Rigor — *did you commit a standard before prompting, and verify against it?*
- [ ] I preregistered invariants + boundary tests **before** the first prompt.
- [ ] I verified against that gate, not the handed-down example.
- [ ] "Green" means something because the standard was independent of the code.

Score: ___ / 2

## Communication *(weighted)* — *could a listener reconstruct your reasoning?*
- [ ] I led with intent and the pivotal decision, not the keystrokes.
- [ ] I voiced the delegate/verify split and rewrote vague into specific live.
- [ ] I owned the result — no "the AI wrote it" hedging (Ch 11).

Score: ___ / 2 → **count this dimension double when totaling.**

---

**Total:** ___ / 10 (Communication double-weighted). 

**Read your lowest score, then your most-skipped loop stage (`loop-checklist.md`) — they're usually the
same one. That overlap is your highest-leverage rehearsal target** (Ch 1 stretch, Ch 12). The goal isn't
a perfect score on one problem; it's the loop surviving the next, unseen one — that's transfer.
