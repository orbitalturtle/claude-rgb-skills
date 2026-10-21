---
name: ci-checks
description: Discover and run a repo's CI checks locally (format, lint/clippy, build, tests) by reading its actual CI config rather than assuming a fixed command set, then report pass/fail with actionable failure details. Use this whenever the user says "/ci-checks", asks to "run CI locally", "make sure CI passes", "check if this will pass CI", or wants to verify a change is clean before pushing/opening a PR — especially in Rust repos like the RGB-Tools ecosystem (rgb-lightning-node, rgb-lib, utexo) where CI involves cargo fmt/clippy/test plus sometimes a Docker-based regtest harness. Trigger even if the user doesn't name specific commands, since figuring out the right commands from the repo is the whole point. For just fmt/clippy with no build or tests, use lint-and-fmt instead.
---

# CI Checks

Run the repo's own CI locally before pushing — every RGB repo wires CI differently. For how to find CI config, match the toolchain, handle feature matrices, and report results, read `../_shared/ci-detection.md` first.

## 1. Order checks cheap-to-expensive
Order: **fmt** → **clippy** → **build** → **tests**. Report fmt/clippy failures immediately rather than waiting on a long test run; still run the rest unless the user wants just a quick check (point them at `lint-and-fmt` for that).

## 2. Handle Docker-dependent checks
Detect regtest/integration setups from the repo itself (`compose.yaml`, `Dockerfile`, a script calling `docker`). If found, check `docker info` first; report **skipped (Docker unavailable)** rather than pass/fail if missing, otherwise run the repo's own setup script instead of reinventing stack bring-up.

Report all four checks using the format in the shared doc.
