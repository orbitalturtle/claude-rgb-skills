---
name: tidy-commits
description: Check whether a PR's or branch's commits form a clean, atomic history — each commit a coherent, self-contained change — and suggest a concrete reorganization (squash/split/reorder) if not. Use when the user says "/tidy-commits", asks "are these commits atomic", "should I squash these", "can you clean up my commit history", or wants feedback on commit organization before opening/merging a PR. This is about the commit *set's* structure, not individual message wording — see the review skill's hygiene check for that.
---

# Tidy Commits

Check whether a PR's/branch's commits are organized atomically — not whether any single message is well-written (that's `review`'s job).

## 1. What to look at
See `../_shared/diff-and-guidelines.md` for determining the diff target, but look at the commit *list*, not the combined diff: `git log <base>..<head> --oneline` or `gh pr view <number> --json commits`.

## 2. What makes a commit atomic
- Compiles and passes tests on its own — not "WIP, fixed next commit."
- Does one coherent thing — not an unrelated mix (e.g. a formatting pass bundled with a logic change, or two unrelated fixes in one commit).
- No commits that exist only because of review back-and-forth ("fix typo," "address comments") rather than belonging in the feature's logical history.
- Sensible order — e.g. a refactor that enables a feature comes before the feature, not after.

## 3. Report
Already atomic and clean? Say so briefly — don't invent problems. Otherwise, suggest a concrete reorganization: which commits to squash (and why), which to split (and along what boundary), and a suggested message for each resulting commit. Name actual commit hashes/subjects, not "some commits could be cleaner."

## 4. Suggest, don't execute
Give the reorganization plan (e.g. the exact interactive-rebase steps) in chat. Don't run `git rebase`, `reset`, or force-push yourself — rewriting history is the user's call to make and execute, not something to do on their behalf.
