---
name: start-issues
description: Pick 1-3 of the most relevant open GitHub issues to work on next, confirm the pick with the user, and move the approved ones to "In Progress" on the "Energy dashboard" project.
disable-model-invocation: true
argument-hint: "[focus area or issue numbers]"
---

# Start issues

Invoking this skill authorizes one thing: moving the issues the user approves to "In Progress" on the project. Don't comment on, assign, label or close issues, create branches, or start implementing.

## Scripts

Run from the repo root. Each prints its reason on failure and exits non-zero.

| Script | Step | Exit codes |
|---|---|---|
| `scripts/candidates.sh` | 1 | 0 OK, 1 `gh` failed |
| `scripts/start.sh N [N...]` | 4 | 0 all moved, 1 aborted |

## 1. List candidates

Run `.claude/skills/start-issues/scripts/candidates.sh`. `IN_PROGRESS` lines are context (work already underway); `CANDIDATE` lines are what you pick from. If there are no candidates, say so and stop. If there are already 3 or more `IN_PROGRESS` issues, mention it in step 3 so the user can reconsider.

If the user passed an argument, treat issue numbers as the picks (skip to step 3, still confirm) and a phrase as a focus area to weigh in step 2.

## 2. Choose 1-3

Read the bodies of the plausible candidates (`gh issue view N`) and weigh:

- **Dependencies**: a task that needs another open issue done first is not ready. Check bodies for "depends on", "blocked by", and sub-issue relationships (`gh api repos/{owner}/{repo}/issues/N/parent` for a parent).
- **Epics** (label `feature`) are tracked via sub-issues: pick their ready sub-tasks, not the epic itself, unless the epic has no sub-tasks.
- **`backlog` label** means not in active scope: skip it unless the user asked for it.
- **Continuity**: prefer work that builds on what is `IN_PROGRESS` or on recent commits (`git log --oneline -15`), and 2-3 issues that fit together in one area over unrelated ones.
- **Size**: don't pick more than the user can reasonably do in one stretch; 1 is fine.

## 3. Confirm

Print the proposal as text first: for each pick, the issue number, title, and one line on why now (and anything it unblocks). Then ask with `AskUserQuestion` (don't ask in plain chat): a multi-select question with one option per proposed issue so the user can drop some, plus (if useful) up to a couple of the next-best alternatives. Treat "Other" text as an instruction (e.g. a different issue number).

If nothing is selected, stop without changing anything.

## 4. Move to In Progress

Run `.claude/skills/start-issues/scripts/start.sh N [N...]` with the approved numbers. Report each `STARTED` line; if the script aborts, report its message and which issues were already moved. Finish with the issue numbers and links, and remind that commits should reference them with `Closes #N`.
