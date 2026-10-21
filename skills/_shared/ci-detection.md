# Finding and reporting a repo's CI checks

Shared by `ci-checks` and `lint-and-fmt`. Read this first, then follow the calling skill's own steps for which checks to actually run.

## Find the repo
Operate on the current directory by default, or on a path given in the skill's arguments (e.g. `/rgb:ci-checks ~/Code/rgb-lightning-node`) — don't assume the user has already `cd`'d there.

## Find the CI definition
Confirm it's a git repo (`git rev-parse --show-toplevel`), then check, in order: `.github/workflows/*.yml`, `.gitlab-ci.yml`, a `justfile`/`Makefile` with CI targets, or `package.json` scripts if JS tooling sits alongside Rust.

Read the workflow files themselves, not just their names — a step often shells out to a script (`./coverage.sh --ci`, `./regtest.sh`) where the real commands live.

## Match the toolchain
Repos often pin a Rust version (`Cargo.toml`'s `rust-version`, `rust-toolchain.toml`, or the CI matrix); a mismatch with ambient `cargo` produces misleading "crate requires rustc X" errors that look like a broken build. Compare `rustc --version` to the pin and use `cargo +<version>` (check `rustup toolchain list`) if they differ — or say a toolchain install is needed, rather than running on the wrong one.

## Feature/toolchain matrices
Skip the full feature/toolchain matrix by default (could mean 9+ builds) — use the default feature set on stable, note CI covers more, and run the full matrix only if asked.

## Report clearly
Per check: **pass**/**fail**/**skipped** (with why). On failure, include the actual file:line and error text, not just "clippy failed." End with a short summary, e.g.:
```
fmt: pass
clippy (default features): fail — 2 warnings in src/rgb_utils.rs
```
Don't modify files (no auto-fmt, no `--fix`) unless asked — these skills verify, they don't fix.
