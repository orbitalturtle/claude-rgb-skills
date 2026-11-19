# rgb-lightning-node maintainer conventions

Requests RGB-Tools maintainers (zoedberg, nicbus) made in **2+ PRs**, mined
from 403 inline comments + ~80 review summaries across PRs #7–#176
(last mined 2026-11-18). PR numbers are evidence; re-mine when this gets stale.

`[script]` = checked by `rln_checks.py`; `[judge]` = needs reading the diff.
For `[script]` items, check the script's output; don't re-check them by hand.

## Commits & process
- **C1** `[script]` Rebased on current upstream `master` tip, no merge commits. (15 PRs: 52,55,62,63,64,69,80,91,95,99,101,133,150,151,174)
- **C2** `[script]` One signed commit, short lowercase imperative subject naming the change: `add /getpayment API`, `add support for HODL invoices`, `add preimage to Payment`. No `feat:` prefixes. (11 PRs: 7,21,52,55,62,63,64,91,101,126,163)
- **C3** `[script]` Don't touch CI workflows, `.gitignore`, `Cargo.lock`, toolchain, dependency versions, `regtest.sh`, nix/compose files unless the change needs it. If it does, justify it in the PR. (7 PRs: 7,18,91,92,133,163,164)
- **C4** `[script]` `cargo fmt` and `cargo clippy --all-targets --all-features -- -D warnings` on latest stable Rust before asking for review. (7 PRs: 18,52,62,63,64,91,113)
- **C5** `[judge]` A **bug fix** is 2 commits: first the test reproducing the bug, then the fix. Push the test first so CI shows it failing. A **new feature** is 1 commit and doesn't need a failing test first. (5 PRs: 89,91,99,136,138; 101 inverse)
- **C6** `[judge]` Self-review the diff before (re-)requesting review. Every resolved thread must actually be addressed. (4 PRs: 18,91,104,126)
- **C7** `[script]` Don't commit a temporary `.gitmodules` URL or submodule pointer to a personal rust-lightning fork. Bump the pointer only after the RGB-Tools/rust-lightning PR has merged. (3 PRs: 69,113,138)
- **C8** `[script]` Subject ≤72 chars, blank line before the body. Update the message when the commit's content changes. (3 PRs: 7,89,163)

## Diff discipline
- **D1** `[judge]` Deduplicate code the PR introduces and look for more duplication. Typical fixes: share a branch, move common logic into a helper or `mod.rs`. (5 PRs: 18,91,126,133,164)
- **D2** `[script]`+`[judge]` Remove unused code, fields and derives (e.g. a `PartialEq` that is never compared). No `#[allow(dead_code)]`; feature-gate instead. (4 PRs: 18,126,151,163)
- **D3** `[judge]` Minimal diff. No cosmetic changes, reordering or sorting of existing fields, needless destructuring of request payloads, or renaming/refactoring of existing tests or helpers. These make blame and review harder. (3 PRs: 91 repeatedly, 92, 124)
- **D4** `[judge]` No helper function that is called only once and isn't needed elsewhere soon; inline it. In `src/utils.rs`, keep a method only if it is used more than once. (3 PRs: 91,124,152)
- **D5** `[judge]` Don't reimplement rgb-lib logic or re-test rgb-lib behaviour in RLN. Call the rgb-lib API and map its errors; missing checks belong in rgb-lib. (2 PRs: 94,151)
- **D6** `[judge]` Extend existing APIs and structs before adding new ones. Examples: an optional `payment_hash` on `/lninvoice` instead of `/hodlinvoice`, a preimage on `Payment` via `/getpayment` instead of `/getpaymentpreimage`, `EmptyResponse` when nothing new is returned. (2 PRs: 18,91)

## API surface
- **A1** `[script]` Alphabetical order of `main.rs` routes, `routes.rs` structs/enums and API fns, `openapi.yaml` paths and schemas, the README API list, and `src/test/mod.rs` modules. Request fields in openapi follow the order of the struct in `routes.rs`. (7 PRs: 18,62,69,91,94,126,151)
- **A2** `[script]`+`[judge]` OpenAPI style:
  - no per-field `description`
  - `required` written as a `- field` list
  - no `format`/`minimum`/`maximum`
  - no `nullable` (3.1 uses `type: [x, 'null']`)
  - enums defined as separate schemas and `$ref`'d
  - tagged enums use `discriminator` + `mapping` (see `Assignment`)
  - new endpoints get a tag that is also listed in the root `tags`
  - responses say `Successful operation`
  - examples are realistic

  Check rendering in swagger. (8 PRs: 62,63,91,104,107,126,151,152)
- **A3** `[script]`+`[judge]` Any new or changed API updates the route structs, `openapi.yaml` and the README API list together. (7 PRs: 52,55,62,63,99,101,126)
- **A4** `[judge]` Naming:
  - structs are `<ApiName>Request`/`<ApiName>Response` (`/claimhodlinvoice` → `ClaimHodlInvoiceRequest`)
  - reuse existing field names: `asset_id`, `asset_amount`, `amt_msat`, `*_sec`
  - one name per concept across the code
  - serde-tagged variants in PascalCase
  - route paths lowercase with no separators

  (4 PRs: 18,62,91,126)
- **A5** `[script]`+`[judge]` API docs live in `openapi.yaml`. No docstrings on route fns or private items, and no explanatory essays in the README. Keep only essential comments. (4 PRs: 91,95,126,138)

## Errors & invariants
- **E1** `[judge]` Every new failure mode gets a dedicated `APIError` variant with a precise message (e.g. `PaymentNotFound`, not `InvalidPaymentHash`) and the right HTTP status. Keep the underlying reason in the message. Map common rgb-lib errors in `From<RgbLibError>`. (4 PRs: 18,52,62,113)
- **E2** `[judge]` When an invariant guarantees success, use `unwrap`/`expect`. Don't add error branches that can never run and can't be covered by tests; if you believe a branch can run, add a test for it. Never `unwrap` something that can actually fail. (4 PRs: 18,52,91,133)

## Tests
- **T1** `[script]`+`[judge]` **Extend an existing test rather than adding a new one**, because each regtest setup is expensive. Merge many small tests into 1–3 with `// success` / `// fail: <case>` comments between subcases. (12 PRs: 69,80,89,91,92,94,99,101,128,152,163,164)
- **T2** `[script]` Imports, API-call wrappers and shared helpers go in `src/test/mod.rs`. Reuse existing helpers: `check_response_is_nok`, `open_channel*`, `issue_asset_*`, `wait_for_*`, `fund_and_create_utxos`. (8 PRs: 69,91,107,110,133,163,164,176)
- **T3** `[script]`+`[judge]` Use `assert_eq!` on exact values, not `assert!(x.is_some())` or `assert!(a == b)`. Assert that a failure happened for the *expected* reason, e.g. a specific error or log line. (5 PRs: 63,64,69,133,164)
- **T4** `[script]` Each test file sets `TEST_DIR_BASE = "tmp/<file_stem>/"`, unique per file. Name files after the API or behaviour, following existing names (`close_force_*`, `openchannel_*`). (6 PRs: 62,63,89,91,133,138)
- **T5** `[judge]` A regression test must fail on the unfixed code. It should also cover bypass variants such as relative and absolute paths, every affected endpoint, and good/bad pairs of inputs. (4 PRs: 91,163,164,176)
- **T6** `[script]`+`[judge]` Tests are deterministic:
  - no fixed sleeps; wait on a concrete signal
  - `free_port()` instead of hardcoded ports
  - `tempfile::tempdir()`
  - `Drop` guards for global test overrides

  (4 PRs: 91,133,163,176)
- **T7** `[judge]` Add a node restart when the change touches persistence. (2 PRs: 69,91)

## Behaviour
- **B1** `[judge]` New state must persist and survive a restart. Read it back from the same store it was written to. (2 PRs: 18,95)
