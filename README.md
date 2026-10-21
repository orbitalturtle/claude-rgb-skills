# claude-rgb-skills

[Claude Code](https://claude.com/claude-code) skills for working on [RGB](https://rgb.tech/) protocol repos (rgb-lightning-node, rgb-lib, and similar). Each skill reads the target repo's actual CI config / toolchain pins / branch structure at runtime rather than assuming a fixed command set, so it isn't tied to one specific repo.

## Skills

- **`review`** — reviews a PR, branch, or diff in two layers: delegates generic correctness/Rust-idiom review to Claude Code's built-in `code-review` skill, then adds its own pass for what that skill can't know about — RGB/consensus-sensitive logic (validation ordering, trusting unvalidated consignment data, schema/state-transition correctness, non-determinism in consensus paths) and commit-message/doc hygiene. Also reads the target repo's own `CONTRIBUTING.md`/`CLAUDE.md`/PR template, if present, as additional criteria. Supports `--fix`, same as `code-review`. Reports findings via Claude Code's `ReportFindings` tool.
- **`ci-checks`** — discovers a repo's CI checks from its actual `.github/workflows/`, `justfile`/`Makefile`, etc. (not a hardcoded command list), matches the pinned Rust toolchain if one differs from the ambient `cargo`, runs format/lint/build/test checks locally in cheap-to-expensive order, and handles Docker-dependent integration tests (e.g. regtest harnesses) explicitly rather than failing silently when Docker isn't available.
- **`lint-and-fmt`** — the fast subset of `ci-checks`: just `cargo fmt --check` and `clippy`, no build or tests. For a quick pre-commit sanity check rather than full CI parity.
- **`tidy-commits`** — checks whether a PR's/branch's commits are atomic and cleanly separated (vs. a tangled mix of unrelated changes, WIP commits, or review-fixup noise), and suggests a concrete squash/split/reorder plan if not. Only suggests — never runs `rebase`/`reset`/force-push itself. Complements `review`'s commit-message-wording check without duplicating it.

## Install

```bash
claude plugin marketplace add orbitalturtle/claude-rgb-skills
claude plugin install rgb@claude-rgb-skills
```

Then, in any RGB repo:

```
/rgb:review          # review the current diff / branch vs. default branch
/rgb:review 180       # review PR #180
/rgb:ci-checks
/rgb:lint-and-fmt     # fast path: just fmt + clippy
/rgb:tidy-commits     # check commit organization, suggest a squash/split plan
```

## Develop locally

```bash
claude plugin validate .
claude --plugin-dir .
```

Edit a `SKILL.md` under `skills/`, then run `/reload-plugins` in an active session to pick up the change without restarting.

## Adding more skills

Add a new `skills/<name>/SKILL.md` following the existing ones as a template — frontmatter needs `name` and a `description` that states when the skill should trigger. No changes to `plugin.json` or `marketplace.json` are needed; new skills under `skills/` are picked up automatically. Run `claude plugin validate .` before committing.

If a new skill shares a chunk of instructions with an existing one, factor the shared part into `skills/_shared/<topic>.md` and have each `SKILL.md` point to it with a relative path rather than duplicating the text. Two examples already in this repo: `_shared/ci-detection.md` (used by `ci-checks` and `lint-and-fmt`) and `_shared/diff-and-guidelines.md` (used by `review`). `_shared/` has no `SKILL.md` of its own, so it isn't picked up as a skill — it's just a reference file read on demand.

For criteria that aren't RGB-specific at all, prefer delegating to a relevant built-in Claude Code skill (as `review` does for correctness/idioms via `code-review`) over re-implementing it — keep this repo's skills focused on what's actually RGB-specific.

## License

MIT — see [LICENSE](LICENSE).
