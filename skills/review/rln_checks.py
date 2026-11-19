#!/usr/bin/env python3
"""Mechanical checks for rgb-lightning-node maintainer conventions.

Usage: rln_checks.py [REPO_DIR] [PR_NUMBER | REF]

Diffs REF (default HEAD) or the upstream PR head against the merge-base with
the RGB-Tools upstream `master`. Only reads git objects, so a PR does not need
to be checked out. IDs match rln-conventions.md. Output lines:
    <ID> <FAIL|WARN|NOTE> <message>
"""

import re
import subprocess
import sys
from pathlib import PurePosixPath

UPSTREAM_RE = re.compile(r"RGB-Tools/rgb-lightning-node(\.git)?\s")
results = []


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def report(cid, level, msg):
    results.append((cid, level, msg))


def show(ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def added_lines(base, head, path):
    """Yield (new_line_no, text) for lines added in path."""
    out = git("diff", "-U0", base, head, "--", path)
    ln = 0
    for line in out.splitlines():
        m = re.match(r"@@ -\S+ \+(\d+)", line)
        if m:
            ln = int(m.group(1))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            yield ln, line[1:]
            ln += 1


def sort_key(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def disorder(items):
    return {(a, b) for a, b in zip(items, items[1:]) if sort_key(a) > sort_key(b)}


# --- list extractors for alphabetical-order checks (A1) ---
def main_routes(txt):
    return re.findall(r'\.route\(\s*"(/[^"]+)"', txt)


def openapi_paths(txt):
    return re.findall(r"^  (/\S+):\s*$", txt, re.M)


def openapi_schemas(txt):
    m = re.search(r"^  schemas:\s*$(.*?)(?=^  \S|\Z)", txt, re.M | re.S)
    return re.findall(r"^    ([A-Za-z0-9_]+):\s*$", m.group(1), re.M) if m else []


def routes_types(txt):
    return re.findall(r"^pub\(crate\) (?:struct|enum) (\w+)", txt, re.M)


def routes_fns(txt):
    return re.findall(r"^pub\(crate\) async fn (\w+)", txt, re.M)


def test_mods(txt):
    return re.findall(r"^mod (\w+);", txt, re.M)


def readme_apis(txt):
    return re.findall(r"^- `(/[^`]+)`", txt, re.M)


ORDER_LISTS = [
    ("src/main.rs", main_routes, "routes in main.rs"),
    ("openapi.yaml", openapi_paths, "openapi paths"),
    ("openapi.yaml", openapi_schemas, "openapi schemas"),
    ("src/routes.rs", routes_types, "structs/enums in routes.rs"),
    ("src/routes.rs", routes_fns, "API fns in routes.rs"),
    ("src/test/mod.rs", test_mods, "test modules in src/test/mod.rs"),
    ("README.md", readme_apis, "API list in README"),
]


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    target = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    import os

    os.chdir(repo)

    upstream = next(
        (l.split()[0] for l in git("remote", "-v").splitlines() if UPSTREAM_RE.search(l + " ")),
        None,
    )
    if not upstream:
        raise SystemExit("no remote pointing at RGB-Tools/rgb-lightning-node")
    git("fetch", "-q", upstream, "master")
    tip = git("rev-parse", "FETCH_HEAD").strip()
    if target.isdigit():
        git("fetch", "-q", upstream, f"pull/{target}/head")
        head = git("rev-parse", "FETCH_HEAD").strip()
    else:
        head = git("rev-parse", target).strip()
    base = git("merge-base", tip, head).strip()
    if base == head and target.isdigit():
        # already merged: take the PR's own first commit parent as the base
        first = subprocess.run(
            ["gh", "pr", "view", target, "-R", "RGB-Tools/rgb-lightning-node",
             "--json", "commits", "--jq", ".commits[0].oid"],
            capture_output=True, text=True,
        ).stdout.strip()
        if first:
            base = git("rev-parse", f"{first}^").strip()
    if base == head:
        raise SystemExit("nothing to check: head is already in upstream master")
    commits = git("rev-list", "--reverse", f"{base}..{head}").split()
    files = {}
    for l in git("diff", "--name-status", base, head).splitlines():
        st, *paths = l.split("\t")
        files[paths[-1]] = st[0]

    print(f"# head {head[:12]}  base {base[:12]}  upstream master {tip[:12]}")
    print(f"# {len(commits)} commit(s), {len(files)} file(s) changed")

    # C1 rebase / merges
    if base != tip:
        behind = len(git("rev-list", f"{base}..{tip}").split())
        report("C1", "WARN", f"not rebased on upstream master tip ({behind} commit(s) behind)")
    for c in sorted(set(git("rev-list", "--merges", f"{base}..{head}").split())):
        report("C1", "FAIL", f"merge commit {c[:12]} — rebase instead")

    # C2/C8 commits
    if len(commits) > 2:
        report("C2", "WARN", f"{len(commits)} commits — maintainers usually want 1 (or test+fix for a bug)")
    merges = set(git("rev-list", "--merges", f"{base}..{head}").split())
    for c in commits:
        if c in merges:
            continue
        sig, subject, body = git("log", "-1", "--format=%G?%x00%s%x00%B", c).split("\x00", 2)
        short = f"{c[:12]} '{subject}'"
        if sig == "N":
            report("C2", "FAIL", f"{short} is not signed (GPG/SSH signature required)")
        if len(subject) > 72:
            report("C8", "FAIL", f"{short} subject is {len(subject)} chars (>72)")
        if re.match(r"(fixup|squash|amend)!|wip\b", subject, re.I):
            report("C2", "FAIL", f"{short} is a fixup/WIP commit — squash it")
        if re.match(r"[a-z]+(\([^)]*\))?!?: ", subject):
            report("C2", "WARN", f"{short} uses a conventional-commit prefix; repo style is plain e.g. 'add /getpayment API'")
        elif subject[:1].isupper() and not re.match(r"[A-Z]{2,}", subject):
            report("C2", "WARN", f"{short} starts uppercase; repo style is lowercase imperative")
        if subject.endswith("."):
            report("C2", "WARN", f"{short} subject ends with a period")
        lines = body.splitlines()
        if len(lines) > 1 and lines[1].strip():
            report("C8", "FAIL", f"{short} has no blank line between subject and body")

    # C3/C7 out-of-scope files
    risky = [
        (r"^\.github/", "CI workflow"),
        (r"^\.gitignore$", ".gitignore"),
        (r"(^|/)Cargo\.lock$", "Cargo.lock"),
        (r"^rust-toolchain", "toolchain file"),
        (r"(^|/)(flake\.(nix|lock)|shell\.nix|default\.nix)$", "nix file"),
        (r"^regtest\.sh$", "regtest.sh"),
        (r"docker-compose|compose\.ya?ml$", "compose file"),
    ]
    for f in files:
        for pat, what in risky:
            if re.search(pat, f):
                report("C3", "WARN", f"{what} changed ({f}) — revert unless essential, and justify in the PR")
    if "Cargo.toml" in files:
        dep_changes = [t for _, t in added_lines(base, head, "Cargo.toml") if re.match(r'\s*[\w-]+\s*=\s*(\{|")', t)]
        if dep_changes:
            report("C3", "WARN", f"Cargo.toml dependency lines changed ({len(dep_changes)}) — deps are bumped by maintainers at release time")
    if ".gitmodules" in files:
        gm = show(head, ".gitmodules")
        bad = [u for u in re.findall(r"url\s*=\s*(\S+)", gm) if "RGB-Tools" not in u]
        level = "FAIL" if bad else "WARN"
        report("C7", level, f".gitmodules changed{' (non-RGB-Tools url: ' + ', '.join(bad) + ')' if bad else ''} — don't commit a temp fork pointer; wait for the upstream rust-lightning merge")
    sub_paths = set(re.findall(r"path\s*=\s*(\S+)", show(head, ".gitmodules")))
    for f in sorted(sub_paths & set(files)):
        report("C7", "NOTE", f"submodule pointer {f} moved — make sure it points at an RGB-Tools/rust-lightning commit (C5: bump goes in the commit after the failing test)")

    # A1 alphabetical order (only newly introduced disorder)
    for path, fn, what in ORDER_LISTS:
        if path not in files:
            continue
        new = disorder(fn(show(head, path))) - disorder(fn(show(base, path)))
        for a, b in sorted(new):
            report("A1", "FAIL", f"{what}: '{a}' placed before '{b}' (not alphabetical)")

    # A3 API change propagated to openapi + README
    new_routes = set(main_routes(show(head, "src/main.rs"))) - set(main_routes(show(base, "src/main.rs")))
    head_openapi, head_readme = show(head, "openapi.yaml"), show(head, "README.md")
    for r in sorted(new_routes):
        if r not in openapi_paths(head_openapi):
            report("A3", "FAIL", f"new route {r} missing from openapi.yaml")
        if r not in readme_apis(head_readme):
            report("A3", "FAIL", f"new route {r} missing from README API list")
    api_struct_touched = any(
        re.search(r"\b(struct|enum) \w+|^\s+pub\(crate\) \w+:", t) for _, t in added_lines(base, head, "src/routes.rs")
    ) if "src/routes.rs" in files else False
    if api_struct_touched and "openapi.yaml" not in files:
        report("A3", "WARN", "routes.rs structs/fields changed but openapi.yaml untouched — update the spec if the API shape changed")

    # A2 openapi style
    if "openapi.yaml" in files:
        comp = next((i + 1 for i, l in enumerate(head_openapi.splitlines()) if l.startswith("components:")), 10**9)
        for ln, t in added_lines(base, head, "openapi.yaml"):
            indent = len(t) - len(t.lstrip())
            s = t.strip()
            if s.startswith("description:") and ln > comp and indent >= 8:
                report("A2", "WARN", f"openapi.yaml:{ln} field-level description — repo style has none")
            if re.match(r"(format|minimum|maximum|nullable):", s):
                report("A2", "WARN", f"openapi.yaml:{ln} '{s}' — repo avoids format/min/max/nullable (3.1 uses type: [x, 'null'])")
            if re.match(r"required:\s*\[", s):
                report("A2", "WARN", f"openapi.yaml:{ln} inline required list — use one '- field' per line")

    # D2 dead code, A5 docstrings
    for f in files:
        if not f.endswith(".rs") or files[f] == "D":
            continue
        for ln, t in added_lines(base, head, f):
            if re.search(r"#\[allow\(dead_code\)\]", t):
                report("D2", "FAIL", f"{f}:{ln} #[allow(dead_code)] — remove the code or feature-gate it")
            if f == "src/routes.rs" and re.match(r"\s*//[/!]", t):
                report("A5", "WARN", f"{f}:{ln} doc comment in routes.rs — API docs live in openapi.yaml")

    # Tests: T1/T2/T3/T4/T6
    test_mod = show(head, "src/test/mod.rs")
    for f, st in files.items():
        if not (f.startswith("src/test/") and f.endswith(".rs")) or st == "D":
            continue
        stem = PurePosixPath(f).stem
        if st == "A" and f != "src/test/mod.rs":
            report("T1", "WARN", f"new test file {f} — maintainers prefer extending an existing test (regtest setup is costly); justify if kept")
            m = re.search(r'TEST_DIR_BASE: &str = "([^"]+)"', show(head, f))
            if m and m.group(1) != f"tmp/{stem}/":
                report("T4", "FAIL", f"{f}: TEST_DIR_BASE is '{m.group(1)}', expected 'tmp/{stem}/'")
            if not re.search(rf"^mod {re.escape(stem)};", test_mod, re.M):
                report("T4", "WARN", f"{f} not declared as 'mod {stem};' in src/test/mod.rs")
        if f == "src/test/mod.rs":
            continue
        helpers, sleeps, prev = [], [], ""
        for ln, t in added_lines(base, head, f):
            s = t.strip()
            if s.startswith("use ") and s != "use super::*;":
                report("T2", "WARN", f"{f}:{ln} '{s}' — test imports go in src/test/mod.rs")
            m = re.match(r"(?:pub(?:\(crate\))? )?(?:async )?fn (\w+)", s)
            if m and not prev.startswith("#[") and m.group(1) not in ("drop", "fmt", "from", "default", "deref", "eq"):
                helpers.append(m.group(1))
            if re.search(r"\bassert!\(.*(==|!=|\.is_some\(\)|\.is_ok\(\)|\.is_none\(\))", s):
                report("T3", "WARN", f"{f}:{ln} use assert_eq!/exact values instead of '{s[:70]}'")
            if re.search(r"\bsleep\(", s):
                sleeps.append(str(ln))
            if s:
                prev = s
        if helpers:
            report("T2", "WARN", f"{f}: helper fns {', '.join(helpers)} — API wrappers/shared helpers belong in src/test/mod.rs; inline single-use ones")
        if sleeps:
            report("T6", "NOTE", f"{f}: fixed sleep at line(s) {', '.join(sleeps)} — prefer waiting on a concrete signal")

    # C4 fmt (only when head is the checked-out tree)
    if git("rev-parse", "HEAD").strip() == head and not git("status", "--porcelain", "--untracked-files=no").strip():
        r = subprocess.run(["cargo", "fmt", "--all", "--", "--check"], capture_output=True, text=True)
        if r.returncode != 0:
            report("C4", "FAIL", "cargo fmt --check fails")
    else:
        report("C4", "NOTE", "head not checked out cleanly — fmt/clippy not run (use rgb:lint-and-fmt)")

    order = {"FAIL": 0, "WARN": 1, "NOTE": 2}
    for cid, level, msg in sorted(results, key=lambda x: (order[x[1]], x[0])):
        print(f"{cid} {level} {msg}")
    if not results:
        print("all mechanical checks passed")


if __name__ == "__main__":
    main()
