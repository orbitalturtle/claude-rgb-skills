---
name: review
description: Review a PR, branch, or diff in an RGB protocol repo (rgb-lightning-node, rgb-lib, UTEXO forks, and similar) against a fixed criteria set — correctness bugs, RGB/consensus-sensitive logic, and Rust idioms/safety — and report findings via ReportFindings. Use whenever the user says "/review", asks to "review this PR", "review my changes", or wants a second pair of eyes on an RGB-related diff before merging. This is distinct from the general-purpose code-review skill: it bakes in RGB-specific scrutiny (contract state transitions, schema/consignment validation, client-side validation correctness) by default rather than requiring the user to specify criteria each time.
---

# RGB PR Review

Review RGB-related code changes against three fixed criteria, in priority order. This exists because generic review misses the ways RGB code specifically goes wrong — validation that runs in the wrong order, or untrusted consignment data trusted a step too early, reads fine to a reviewer who isn't thinking about client-side validation.

## 1. Determine what to diff

Accept an optional argument the same way the built-in `/code-review` skill does: a PR number, a branch name, or nothing (meaning the current working diff / branch vs. its upstream default branch).

- PR number → `gh pr diff <number>` (or `gh pr checkout` first if you need to run anything against the code, not just read the diff).
- Branch name → diff against the repo's default branch (`git merge-base` + `git diff`).
- Nothing → `git diff` against the default branch, falling back to the working tree diff if the branch has no separate upstream.

Work out the repo's default branch rather than assuming `main` or `master` — RGB-Tools repos use `master`.

## 2. Review criteria, in this order

Rank findings by how severe they are within each category, but weight category 2 above category 3 when triaging what to report first — a Rust style nit matters far less than a subtly wrong validation path.

### a. Correctness bugs
Standard review: logic errors, off-by-one/edge cases, incorrect error propagation, race conditions, resource leaks. A finding here needs a concrete failure scenario (specific input/state that produces a wrong result or crash) — not a stylistic preference.

### b. RGB / consensus-sensitive logic
This is the category generic review tools miss. Look specifically for:
- **Validation ordering**: state (UTXOs, allocations, contract state) mutated or acted on *before* the consignment/transfer/schema validation that's supposed to gate it completes.
- **Trusting untrusted input**: data arriving from a counterparty (consignments, transfers, invoices) used without being re-validated locally — client-side validation means *this node* must independently verify, not rely on the sender having done so.
- **Schema/contract logic**: changes to state transition rules, global/owned state schema, or Alluvium RGB contract logic — check that new transition types or state updates can't produce globally-inconsistent state (e.g. double-spend of the same allocation, state that doesn't match what the schema would recompute).
- **Non-determinism in consensus paths**: floating point, hash map iteration order, wall-clock time, or other non-deterministic operations in any code path that affects validation or that different parties must agree on.
- **Serialization**: wrong encoding/strict-encoding usage, version mismatches, or anything that could make two honest parties compute different results from the same data.

A finding here should name the specific state-consistency or validation-bypass scenario it enables, not just "this touches consensus code, be careful."

### c. Rust idioms & safety
- `unsafe` blocks without a safety comment justifying the invariant being relied on.
- `.unwrap()` / `.expect()` / `panic!()` on a path reachable from untrusted input (network data, user input, file parsing) — as opposed to a genuinely-unreachable invariant, which is fine.
- Silently dropped errors: `.ok()` discarding an `Err`, overly broad `map_err` that loses information needed to debug, `let _ = fallible_call()`.
- Clippy-style concerns worth flagging even if clippy would eventually catch them: needless clones, wrong error types, non-idiomatic `Option`/`Result` handling.

## 3. Report findings

Use the `ReportFindings` tool, most severe first (and category (b) findings outranking equally-severe (a)/(c) findings, since they're easier to miss and more consequential). Use category slugs `correctness`, `rgb-consensus`, `rust-safety`. Each finding needs a concrete failure scenario — what input or sequence of events triggers the problem — not just a description of what the code does.

If nothing survives scrutiny in a category, that's a fine outcome — report an empty or shorter list rather than padding it with nitpicks to seem thorough.
