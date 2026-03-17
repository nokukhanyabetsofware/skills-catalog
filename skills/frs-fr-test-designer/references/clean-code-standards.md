# Clean Code Standards

## Reuse first
- Reuse existing builders, fixtures, harnesses, API clients, repositories, and DB wrappers before creating new ones.
- Extend the local component structure instead of inventing a parallel architecture.
- Add a new abstraction only when it clearly removes duplication across execution targets.

## Structural rules
- Keep one responsibility per file.
- Keep generated code and helper files under 200 lines where feasible.
- Keep methods under 10 executable lines where feasible by extracting helpers.
- Prefer small pure helpers over large branching methods.
- Keep naming explicit and business-driven.

## Automation architecture
- Centralize execution-target routing in one resolver or adapter.
- When `api+db` is selected, expose target-agnostic operations to test bodies.
- Do not scatter API-vs-DB branching through test bodies.
- Keep assertions target-agnostic when the logical business result is the same.
- Keep transport-specific setup in helpers, not in each test.

## DRY rules
- Do not duplicate request builders across tests.
- Do not duplicate DB parameter builders across tests.
- Do not duplicate assertion logic for success, failure, audit, or logging checks.
- Generate baseline data from discovered contracts, then mutate deterministically for partitions and boundaries.

## Practical quality rules
- Use dynamic dates that fit the test purpose.
- Keep tests deterministic and isolated.
- Skip only for missing config or unreachable dependency.
- Fail for all other unmet expectations.
- Use `UAT` and `disable` cleanup unless the user directs otherwise.

## Discovery discipline
- Derive business behavior from the FRS.
- Derive API and DB contracts from the repo first.
- Use FR Answer Packs only as optional approved metadata.
- Ask targeted questions only when FRS, repo, and pack still leave a real gap.
