---
name: lint-and-fmt
description: Run just a repo's format and lint checks (cargo fmt --check, cargo clippy) locally — the fast subset of CI, with no build or tests. Use when the user says "/lint-and-fmt", asks to "check formatting", "run clippy", "lint this", or wants a quick pre-commit sanity check without the full test suite. For the full CI suite (build, tests, Docker-based integration checks), use ci-checks instead.
---

# Lint & Format

Fast subset of CI — format and lint only. For how to find CI config, match the toolchain, handle feature matrices, and report results, read `../_shared/ci-detection.md` first.

## Run
**fmt** (`cargo fmt -- --check`) → **clippy** (`cargo clippy --all-targets -- -D warnings`, default features unless asked for the full matrix). Report and stop — no build, tests, or Docker checks here; point the user at `ci-checks` for those.
