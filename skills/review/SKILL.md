---
name: review
description: Review a PR, branch, or diff in an RGB protocol repo (rgb-lightning-node, rgb-lib, UTEXO forks, and similar) for RGB/consensus-sensitive logic, commit-message/doc hygiene, and (in rgb-lightning-node) the conventions upstream maintainers repeatedly request in review, while delegating generic correctness and Rust-idiom review to Claude Code's built-in code-review skill. Use whenever the user says "/review", asks to "review this PR", "review my changes", or wants a second pair of eyes on an RGB-related diff before merging. Supports --fix to apply findings to the working tree, same as code-review.
---

# RGB PR Review

For generic correctness bugs and Rust idioms, this delegates to the built-in `code-review` skill — no point re-deriving criteria Claude Code already maintains. This skill's own job is the part `code-review` has no way to know about: RGB/consensus-sensitive logic, and commit/doc hygiene.

## 1. What to diff & repo guidelines
See `../_shared/diff-and-guidelines.md`.

## 2. Delegate correctness & idioms
Invoke the built-in `code-review` skill (Skill tool, `skill: "code-review"`) on the same diff target, passing through any effort level or `--fix` flag the user gave. Let it run its own pass and report its own findings — don't re-derive correctness/idiom criteria here. If it's unavailable in this environment, say so and continue with step 3 anyway.

## 3. RGB-specific layer
Review the same diff for:

### RGB / consensus-sensitive logic
- **Validation ordering**: state mutated before the validation meant to gate it completes.
- **Trusting unvalidated input**: counterparty data (consignments, transfers, invoices) trusted without this node independently re-validating it.
- **Schema/contract logic**: new transitions or state updates that could desync global state (double-spends, state the schema wouldn't recompute).
- **Non-determinism & serialization**: floats, hash-map order, wall-clock time, wrong encoding, version mismatches — anything that could make honest parties disagree.

Name the specific state-consistency or validation-bypass scenario — not "this touches consensus, be careful."

### Commit messages & doc hygiene
Lowest priority — raise only when worth fixing. This is about wording, not organization — see `tidy-commits` for whether the commit *set* is atomic:
- Commit subjects over ~72 chars, or vague ones (`fix stuff`).
- Comments/docs bloated relative to what they explain — restating the obvious or padding with filler.
- The inverse: a non-obvious invariant or workaround with no comment explaining it.

Quote the specific message/comment — don't just assert "could be better."

### Maintainer conventions (rgb-lightning-node only)
Run this layer only when the repo has a remote pointing at `RGB-Tools/rgb-lightning-node`. That includes forks such as UTEXO's whose PRs go upstream. It catches the requests maintainers repeat in review, so a PR doesn't burn a review round on them.

1. Run the mechanical checks. Pass the PR number or branch you are reviewing; with no target it checks `HEAD`:
   ```
   python3 -I <this skill dir>/rln_checks.py <repo dir> [PR# | ref]
   ```
   It fetches upstream `master` and the PR head without checking anything out. Output lines are `<ID> FAIL|WARN|NOTE <message>`, and the IDs match `rln-conventions.md`. Report FAIL and WARN lines. Mention NOTEs only when they point at something real.
2. Read `rln-conventions.md` (next to this file) and apply the `[judge]` items to the diff. **T1** (extend an existing test instead of adding one), **D1/D3/D4** (duplication, minimal diff, single-use helpers) and **C5** (failing-test-then-fix for bugs) are the ones maintainers raise most. Quote the evidence PR number when it helps the author see the request is a pattern.
3. Lower the severity of a WARN when the PR description already justifies it, e.g. a C3 CI change that is actually needed.

## 4. Report & fix
Report via `ReportFindings`, slugs `rgb-consensus`, `hygiene` and `maintainer-conventions` (prefix each summary with its ID, e.g. `T1:`), most severe first. A maintainer-conventions finding's scenario is the review round it would cost, e.g. "maintainer will ask to fold this into `openchannel_fail`". Each finding needs a concrete scenario — for hygiene, the cost to a future reader, not a crash.

If `--fix` was passed, apply these findings to the working tree the same way `code-review --fix` applies its own — this is on top of whatever `code-review` already fixed in step 2, not a replacement for it.

Empty/short categories are a fine outcome — don't pad with nitpicks.
