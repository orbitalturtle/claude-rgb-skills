# Determining the diff & repo guidelines

Shared by review-style skills that need a diff target.

## Find the repo
Operate on the current directory by default, or on a repo path given in the skill's arguments (e.g. `/rgb:review ~/Code/rgb-lightning-node 180`) — don't assume the user has already `cd`'d there. If a path is given, run `gh`/`git` commands with that as the working directory (or `gh`'s `-R <owner>/<repo>` flag) rather than the shell's actual cwd.

## What to diff
- PR number → `gh pr diff <number>` (checkout first if you need to run code, not just read it).
- Branch → diff against the default branch (`git merge-base` + `git diff`).
- Nothing → `git diff` against the default branch, falling back to the working-tree diff.

Check the actual default branch — RGB-Tools repos use `master`, not `main`.

## Repo-specific guidelines
Check for `CONTRIBUTING.md`, `CLAUDE.md`, `.github/PULL_REQUEST_TEMPLATE.md`; apply any that exist as additions to whatever criteria the calling skill applies, not replacements.
