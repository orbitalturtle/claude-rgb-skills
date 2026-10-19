---
name: ci-checks
description: Discover and run a repo's CI checks locally (format, lint/clippy, build, tests) by reading its actual CI config rather than assuming a fixed command set, then report pass/fail with actionable failure details. Use this whenever the user says "/ci-checks", asks to "run CI locally", "make sure CI passes", "check if this will pass CI", or wants to verify a change is clean before pushing/opening a PR — especially in Rust repos like the RGB-Tools ecosystem (rgb-lightning-node, rgb-lib, utexo) where CI involves cargo fmt/clippy/test plus sometimes a Docker-based regtest harness. Trigger even if the user doesn't name specific commands, since figuring out the right commands from the repo is the whole point.
---

# CI Checks

Run what the repo's own CI would run, locally, so the user finds out about failures before pushing — without assuming any fixed command set. Every RGB repo (rgb-lightning-node, rgb-lib, utexo forks, others) wires its checks up slightly differently, so read the repo rather than pattern-matching on "it's Rust, so `cargo test`."

## 1. Find the repo root and its CI definition

Run from the repo the user means (current directory, or a path they gave). Confirm it's a git repo (`git rev-parse --show-toplevel`).

Look for CI config in this order, using whichever exist:
- `.github/workflows/*.yml` / `*.yaml` (GitHub Actions — the common case for RGB-Tools repos)
- `.gitlab-ci.yml`
- A `justfile` or `Makefile` with CI-shaped targets (`test`, `lint`, `ci`, `check`)
- `package.json` `scripts` block, if the repo has JS/TS tooling alongside Rust (e.g. docs/swagger builds)

Read the actual workflow files — don't guess from the file list. A workflow step often shells out to a script (`./coverage.sh --ci`, `./regtest.sh`) rather than calling `cargo test` directly; open those scripts too, since the real commands and flags live there, not in the YAML.

## 2. Match the toolchain CI uses — don't trust whatever `cargo` resolves to by default

Rust repos often pin a specific toolchain via `rust-version` in `Cargo.toml`, a `rust-toolchain.toml`, or the CI matrix itself (e.g. a `1.94.0` entry alongside `stable`/`beta`). The ambient `cargo`/`rustc` on the machine may be older or newer than that — and the failure mode is misleading: instead of a clean "wrong toolchain" error, you get a wall of "`<crate> requires rustc 1.94.0`" dependency errors that look like the *build* is broken.

Before running anything, check `rustc --version` against the repo's pinned version. If they differ, check `rustup toolchain list` for a matching one and use `cargo +<version> <subcommand>` for every check instead of bare `cargo`. If no matching toolchain is installed, say so explicitly (`rustup toolchain install <version>`) rather than pushing ahead on the wrong one and reporting unrelated-looking failures.

## 3. Build the list of checks to run, in cheap-to-expensive order

Typical shape for a Rust RGB repo, roughly in the order CI itself would fail fastest:
1. **Format** — e.g. `cargo fmt -- --check`
2. **Lint** — e.g. `cargo clippy --all-targets -- -D warnings`
3. **Build** — e.g. `cargo build --release`
4. **Tests** — unit tests, then anything needing a live regtest/docker environment

Run format and lint first and stop to report immediately if they fail — there's no point waiting on a 20-minute test suite when `cargo fmt --check` already failed in two seconds. Still run the remaining checks after reporting, unless the user only wanted a quick check.

**Feature/toolchain matrices**: CI often tests a matrix (multiple feature combinations, multiple Rust toolchains/OSes) to catch combination-specific bugs. Don't run the full matrix locally by default — it can mean 9+ clippy invocations or builds across stable/beta/MSRV, which takes far longer than useful for a local check. Default to the repo's default feature set on the stable toolchain, note in your summary that CI covers additional combinations, and only run the full matrix if the user asks for exhaustive parity with CI (e.g. "run the full lint matrix").

## 4. Handle Docker-dependent checks explicitly

Some RGB repos (e.g. rgb-lightning-node, UTEXO's rgb-lib regtest harness) run integration tests against a local regtest stack (bitcoind/electrum/esplora) brought up via `docker compose` or a setup script. Detect this from the repo itself — a `compose.yaml`/`docker-compose.yml`, a `Dockerfile`, or a script like `regtest.sh` that calls `docker`.

If such a check exists:
- Check whether Docker is actually available (`docker info`) before attempting it.
- If Docker isn't available or the daemon isn't running, don't fail silently — report that check as **skipped (Docker unavailable)** rather than passed or failed, and tell the user what would be needed to run it.
- If Docker is available, run the repo's own setup script/compose file rather than reinventing the stack bring-up — these scripts usually handle ordering, funding wallets, waiting for services to be ready, etc., which is fiddly to replicate ad hoc.

## 5. Report results clearly

For each check, report one of: **pass**, **fail**, or **skipped** (with why). For failures, don't just say "clippy failed" — include enough of the actual output (file:line, the warning/error text) that the user can act on it without re-running the command themselves. For compiler/clippy errors this usually means the last relevant chunk of output, not the whole log.

End with a short summary line, e.g.:
```
fmt: pass
clippy (default features): fail — 2 warnings in src/rgb_utils.rs
build: pass
tests: skipped (Docker unavailable — regtest harness needs it)
```

Don't modify any files (no auto-formatting, no `clippy --fix`) unless the user explicitly asks — this skill verifies, it doesn't fix.
