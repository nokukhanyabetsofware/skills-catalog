---
name: frs-fr-test-designer
description: "Plan-first FRS-driven API and DB automation for a specific FR or AC by reading a supplied flow diagram or deriving the flow from FRS text, discovering real repo contracts and readiness before asking questions, using FR Answer Packs as optional approved metadata, and producing an exact 8-section approval-gated plan before any code changes. After explicit approval, implement or bootstrap missing automation structure. Use when Dev or QA asks to formulate detail tests, derive test cases from an FRS, write api/db automation, scaffold missing automation components, or generate an approval-gated plan."
---

# FRS FR Test Designer

Use for Dev and QA automation work driven by an FRS, FR, AC, or flow diagram.

## Core rules
- Use `execution target` as the canonical internal term.
- Supported execution targets: `api`, `db`, `api+db`.
- Render `Channel coverage` in the user-facing plan output. Normalize repo- or user-specific labels such as `promotion_api`, `transport_api`, `client_db`, or `syx_db` to the internal execution target model while preserving the original label in the plan.
- Use the selected FRS document from the repo or conversation. If it is missing or unclear, run `scripts/find_frs.py`.
- Read any supplied flow diagram first to understand sequence and state transitions. If no usable diagram exists, derive the flow from FRS process text, scenarios, and FR sequencing, then state that no diagram support was provided.
- Use source precedence:
  - business meaning: `FRS text -> flow diagram -> FR Answer Pack -> user clarification`
  - technical contracts and readiness: `repo discovery -> FR Answer Pack -> user clarification`
- Treat FR Answer Packs as optional approved caches, not first lookup.
- Treat any attached FRS or flow diagram as task input for the current run only, not as a hardcoded repository dependency.
- Bootstrap only the automation layer. Do not invent unknown production API paths, DB procedures, or payload fields.
- Always plan first. Do not write or edit tests before the final approval gate in section 8 is satisfied.

## Workflow
### 1. Resolve context, execution target, and flow
- Validate the exact FR or AC exists in the FRS.
- Read the supplied flow diagram first. Support image, Mermaid, or arrow-based text flow.
- If no usable diagram exists, derive the flow from:
  - process descriptions
  - `Given/When/Then` scenarios
  - FR ordering and lifecycle states
- Parse the matching `Requirement`, `Acceptance criteria`, `Applicability`, and `Outcome`.
- Convert the selected flow into ordered test steps: trigger, qualification, state change, side effect, audit point, and terminal outcome.
- Collect matching `Given/When/Then` scenarios and use them as the default AAA seed.
- Record known unresolved FRS items that may block deterministic assertions.
- Confirm the execution target as `api`, `db`, or `api+db`, even if the request expresses it as a channel label.

### 2. Discover repo contracts and readiness before asking questions
- For `api` or `api+db`, inspect the existing component structure first:
  - routes, controllers, handlers, clients, DTOs, contracts, tests
  - run `scripts/discover_api_contracts.py` when search needs to be repeatable
- For `db` or `api+db`, inspect the existing component structure first:
  - repositories, stored-procedure wrappers, SQL files, data access services, tests
  - run `scripts/discover_db_contracts.py` when search needs to be repeatable
- Inspect the nearest existing test area before proposing file structure:
  - folder structure and naming
  - fixtures, builders, and helpers
  - setup, teardown, and assertion style
- Capture method or procedure names, request or input fields, response or output fields, source paths, and nearby test baseline.
- Treat `empty target contract discovery + absent nearby test baseline` as the repo-not-ready signal for that target.
- Distinguish:
  - missing automation structure that can be bootstrapped
  - missing system-under-test contract details that must be clarified before coding
- Reuse the current component structure. Do not invent a parallel API or DB abstraction when an existing one can be extended.

### 3. Hydrate the optional FR Answer Pack
- Load a matching FR Answer Pack only after repo discovery.
- Use the pack to confirm or fill missing details, not to replace repo truth.
- Normalize legacy `clarifications.channels` to `clarifications.execution_targets`.
- If the user overrides the pack in the current conversation, user input wins for that run.

### 4. Ask only targeted unresolved questions
- Do not ask DB questions for `api`.
- Do not ask API questions for `db`.
- Do not ask for AAA samples if the flow plus repo discovery already make the test path concrete.
- Ask only for unresolved target-specific contract gaps or conflicts that remain after FRS, repo discovery, and pack lookup.
- Stop at the earliest blocking output section. Do not continue into fabricated partitions, boundaries, test cases, or implementation planning.
- If a concrete API path, DB procedure, required payload field, required output field, environment detail, or baseline fixture is still unknown, list the missing item in the current blocking section and stop.

### 5. Build the plan-first response
- For complete planning responses, output exactly the 8 numbered sections defined in `references/output-and-naming.md`.
- Fold flow summary into section 3, repo discovery and run commands into section 4, lean and extended suites plus the channel matrix and FR mapping into section 7, and logging, bootstrap, audit, cleanup, and execution details into section 8.
- When the repo is not ready, describe bootstrap work inside section 8. Do not create a separate bootstrap section and do not ask `Approve bootstrap? (yes/no)`.
- Include discovery provenance inside section 4 as a compact subsection.
- End section 8 with `Approve implementation? (yes/no)` and stop.

### 6. Implement after approval
- Do not edit code before the section 8 approval gate is satisfied.
- If the repo is not ready, implement the approved bootstrap structure first, then the tests covered by the same approved plan.
- Use the repo's existing framework, builders, fixtures, clients, wrappers, and assertion style when they exist.
- If no baseline exists, use the approved bootstrap structure as the new local baseline.
- Apply the clean-code rules in `references/clean-code-standards.md`.
- When tests are executed, default to `UAT` and `disable` cleanup unless the user explicitly instructs otherwise.

## Stop conditions
Stop and report before later sections if any of these are true:

1. The requested FR or AC does not exist in the FRS.
2. No non-empty FRS can be found in the repo or conversation.
3. Execution-target or channel-coverage mapping is still unresolved.
4. Scope clarification items still unresolved: coverage model, environment, cleanup rule, or baseline fixture or payload source when needed for deterministic planning.
5. A selected target contract cannot be discovered from repo code and cannot be completed from a pack or user clarification.
6. A known unresolved FRS item still blocks deterministic assertions after repo search, pack lookup, and targeted clarification.
7. Neither an existing nearest test/style baseline nor a bootstrapable automation plan has been established before section 8.
8. The plan violates skip policy: skip only for missing config or unreachable dependency; otherwise fail.
9. The user has not approved implementation yet.

For blocked runs, emit sections in order and stop at the first blocking section. Do not add later sections as placeholders.

## Output contract
For complete planning responses, produce exactly these 8 numbered sections in order:

1. `FR Existence Check`
2. `Scope Clarification Check`
3. `Step 1 - Understand the Requirement`
4. `Step 2 - Explore the Implementation`
5. `Step 3 - Identify Partitions`
6. `Step 4 - Analyse the Boundaries`
7. `Step 5 - Devise Test Cases`
8. `Plan + Approval Gate`

- Use the detailed content rules in `references/output-and-naming.md`.
- For blocked runs, start at section 1 and stop after the first section that contains an unresolved blocker.
- Do not produce standalone sections named `FRS and Flow Summary`, `Execution Target Check`, `Repo Discovery and Readiness Summary`, `Logging and Assertions`, or `Bootstrap Plan`.

## Implementation rules
- Generated test function names must follow `test_<test_case_name>`.
- Generated test folders and files must not include `fr` as a token.
- FR identifiers may appear in prose, traceability tables, and approval planning, but not in generated artifact names.
- Lean suite is mandatory. Extended suite is conditional.
- Category buckets are required for implemented suites, not for analysis-only plans.
- Prefer existing repo components over new abstractions.
- Bootstrap only missing automation structure; do not create speculative production contracts.
- Keep generated code and helper code under 200 lines per file where feasible.
- Keep methods under 10 executable lines where feasible by extracting helpers.
- Centralize execution-target routing in one resolver or adapter.
- Expose target-agnostic operations when `api+db` is selected.
- Avoid duplicating setup, assertions, or logging logic across API and DB paths.
- Log DB and API responses and validate both structure and values required by the FRS.
- Inform the user of missing requirements and required approvals before any implementation step.
- Document which existing style baseline is being followed and any deliberate deviations before asking for implementation approval.

## Resource map
Load these files only when needed:

- `references/discovery-and-pack.md`
  - Parse the selected FRS layout, run repo discovery, interpret unresolved details, normalize channel labels to execution targets, and normalize FR Answer Packs.
- `references/output-and-naming.md`
  - Build the exact 8-section response, naming, suite grouping, approval gating, and logging expectations.
- `references/clean-code-standards.md`
  - Apply DRY, clean architecture, file-size and method-size guidance, and transport-agnostic automation patterns.
- `scripts/find_frs.py`
  - Locate and rank likely FRS files when the FRS source is missing or ambiguous.
- `scripts/discover_api_contracts.py`
  - Discover likely API routes, request fields, response fields, and source paths from repo code.
- `scripts/discover_db_contracts.py`
  - Discover likely stored procedures, operation maps, input parameters, output columns, and source paths from repo code.

## FRS handling
- Use the FRS selected for the current task, not a hardcoded repository example.
- Parse the actual structure present in that FRS before asking clarifying questions.
- Read supplied flow diagrams first to understand sequence and state transitions.
- If no diagram exists, derive the flow from FRS text and state that no diagram support was provided.
- If the FRS includes FR sections, AC sections, scenarios, unresolved items, or data definitions, use them directly instead of asking generic context questions.

## Good interactions
- "use the flow diagram and FRS to formulate detail tests for FR-08 using promotion_api and show the plan first"
- "no diagram is attached; derive the flow from the FRS and plan db automation for AC-G5"
- "the repo has no deposit api automation yet; show the bootstrap work inside the approval plan for FR-12"

## Bad interactions
- Asking for DB procedure mappings before checking repo code.
- Asking for AAA examples when the FRS flow and scenarios already provide them.
- Treating the FR Answer Pack as the primary source of truth.
- Forcing both API and DB when the request explicitly targets only one.
- Inventing endpoints, procedures, or payload fields that are not confirmed by repo code, a pack, or the user.
- Emitting sections 5 to 8 when section 2, 3, or 4 is still blocked.
