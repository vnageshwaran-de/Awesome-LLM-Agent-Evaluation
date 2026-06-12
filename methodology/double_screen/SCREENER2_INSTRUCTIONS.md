# Instructions for the second (independent) full-text screener

Thanks for doing the second screen — this gives us the inter-screener
reliability (Cohen's κ) for the methods section. The most important thing is
**independence**: please decide on your own, without seeing anyone else's calls.

## 1. What to open
- File: `methodology/double_screen/screener2_blind.csv`
- It has 185 candidate records, one per row, with: `Tier, Source,
  Candidate title, Link, screener2_decision, screener2_notes`.
- The decision/notes columns are intentionally blank.

## 2. Stay blind (please)
- **Do not open `coauthor_screening_returned.csv` or discuss the calls with the
  first screener until you're finished.** The κ is only meaningful if your
  decisions are made independently.
- Decide from the **full text** of each paper (open the `Link`), not from the
  title alone.

## 3. The decision rule
Mark **Include** only if the paper **proposes, formalizes, or analyzes a
procedure for measuring an LLM-driven agent that takes sequential,
state-altering actions over ≥ 2 dependent steps** (IC1–IC3). In plain terms, all
of these must hold:
- the agent is **LLM-driven** (not RL/MARL, control-theoretic, robotics-policy,
  or optimization), **and**
- it takes **actions that change an external environment/state** (tool/API calls,
  GUI/OS/web operations, code execution, game moves) — not just answering or
  generating text, **and**
- the task chains **≥ 2 dependent steps** (later steps depend on earlier
  observations), **and**
- the paper contributes a **measurement procedure** — a reusable benchmark/task
  suite or an evaluation methodology — applied to the above.

Otherwise mark **Exclude**. Common exclude reasons (for your notes):
- **EC1 / EC3** — static QA, text generation, or a single-hop / single-action
  task (no dependent multi-step external actions).
- **EC4** — an application/system paper ("we built an agent for domain X") or an
  architecture comparison, with no reusable evaluation procedure; or the agent
  is the *evaluator* (LLM-as-judge) rather than the thing being measured.
- **EC5** — survey, review, position paper, taxonomy round-up, or news item.
- **EC6** — the "agent" is not LLM-driven (RL/MARL, robotics, control,
  optimization).
- **Out of scope** — "agent" used in a non-AI sense (chemical/biological agent,
  software daemon, human call-center agent, etc.).

## 4. How to record each decision
- In **column E (`screener2_decision`)** type exactly `Include` or `Exclude`.
- In **column F (`screener2_notes`)** add a brief one-line reason (optional but
  helpful for reconciliation), e.g. "EC6 — RL policy, not LLM."
- If you genuinely can't decide, leave it blank or write `Uncertain` — those rows
  are simply excluded from the κ (we'll reconcile them separately).
- Don't change the other columns. Save in the **same CSV format** (UTF-8).

## 5. Scope
- Screening **all 185** is ideal. If time is short, a stratified subset is fine —
  just complete whole rows; the scorer reports κ on whatever is completed and
  tells us n.

## 6. When you're done
Send the file back. We run `compute_screening_kappa.py` (it joins your sheet to
the first screener's on title, maps Include/Exclude to 1/0, and reports κ,
percent agreement, n, and the confusion counts). Disagreements are then
reconciled by discussion (third senior author if needed); κ is reported from the
**pre-reconciliation** decisions.
