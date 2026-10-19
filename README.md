# claude-rgb-skills

[Claude Code](https://claude.com/claude-code) skills for working on [RGB](https://rgb.tech/) protocol repos (rgb-lightning-node, rgb-lib, and similar). Each skill reads the target repo's actual CI config / toolchain pins / branch structure at runtime rather than assuming a fixed command set, so it isn't tied to one specific repo.

## Skills

- **`review`** — reviews a PR, branch, or diff against a fixed criteria set tailored to RGB work: correctness bugs, RGB/consensus-sensitive logic (validation ordering, trusting unvalidated consignment data, schema/state-transition correctness, non-determinism in consensus paths), and Rust idioms/safety (`unsafe`, `unwrap`/`panic!` on untrusted-input paths, swallowed errors). Reports findings via Claude Code's `ReportFindings` tool.
- **`ci-checks`** — discovers a repo's CI checks from its actual `.github/workflows/`, `justfile`/`Makefile`, etc. (not a hardcoded command list), matches the pinned Rust toolchain if one differs from the ambient `cargo`, runs format/lint/build/test checks locally in cheap-to-expensive order, and handles Docker-dependent integration tests (e.g. regtest harnesses) explicitly rather than failing silently when Docker isn't available.

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
```

## Develop locally

```bash
claude plugin validate .
claude --plugin-dir .
```

Edit a `SKILL.md` under `skills/`, then run `/reload-plugins` in an active session to pick up the change without restarting.

## Adding more skills

Add a new `skills/<name>/SKILL.md` following the existing two as a template — frontmatter needs `name` and a `description` that states when the skill should trigger. No changes to `plugin.json` or `marketplace.json` are needed; new skills under `skills/` are picked up automatically. Run `claude plugin validate .` before committing.

## License

MIT — see [LICENSE](LICENSE).
