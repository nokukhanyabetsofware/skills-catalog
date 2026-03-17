# Output And Naming

## Response format
For complete plans, produce exactly these 8 numbered sections in order:

1. `FR Existence Check`
2. `Scope Clarification Check`
3. `Step 1 - Understand the Requirement`
4. `Step 2 - Explore the Implementation`
5. `Step 3 - Identify Partitions`
6. `Step 4 - Analyse the Boundaries`
7. `Step 5 - Devise Test Cases`
8. `Plan + Approval Gate`

Render the headings with the numeric prefixes shown above.

For blocked runs:
- start at section 1
- stop after the first section that contains an unresolved blocker
- ask only the targeted unresolved questions for that blocking section
- do not emit later sections as empty placeholders

Do not produce standalone sections named `FRS and Flow Summary`, `Execution Target Check`, `Repo Discovery and Readiness Summary`, `Logging and Assertions`, or `Bootstrap Plan`.

## Section 1 - FR Existence Check
- Confirm the requested FR or AC exists by exact identifier.
- Cite the FRS file, section, or line when available.
- Summarize the requirement text used without long verbatim quotes.
- If the FR or AC does not exist, or if no FRS source can be found, stop here.

## Section 2 - Scope Clarification Check
- Render `Channel coverage` even though the internal model uses execution targets.
- If labels were normalized, show both forms, for example `Channel coverage: promotion_api (execution target: api)`.
- Confirm these items when available:
  - channel coverage
  - coverage model
  - procedure or operation mapping
  - environment
  - cleanup rule
  - baseline fixture or payload source
  - why the fixture or payload is suitable
- If a scope-confirmation item is still required and unresolved, list only the missing item or items and stop here.
- If the unresolved item depends on repo-contract discovery rather than user scope, carry it into section 4 instead of guessing here.

## Section 3 - Step 1 - Understand the Requirement
- Integrate the flow summary into this section.
- State whether the flow came from a supplied diagram, a derived FRS flow, or both.
- If no diagram exists, say that no diagram support was provided.
- Include:
  - intent or user story
  - ordered business flow
  - inputs
  - outputs
  - expected behaviors
  - failure behaviors and reason codes or messages from the FRS
- If an unresolved business rule or outcome expectation still blocks deterministic assertions after FRS and pack review, stop here.

## Section 4 - Step 2 - Explore the Implementation
- Include:
  - likely implementation points in the repo
  - current tests found, or none
  - readiness result per selected execution target: `ready`, `bootstrap required`, or `blocked`
  - existing style baseline in the closest test area
  - how the tests would be run in this repo
  - current execution blockers or observed environment issues when known
- Add a compact `Discovery Provenance` subsection covering:
  - FRS section used
  - flow source used
  - repo path or paths used
  - FR Answer Pack details used, if any
  - user clarification used, if any
- If a concrete API path, DB procedure, required payload field, required output field, or readiness dependency is still unknown, ask only the missing target-specific questions and stop here.

## Section 5 - Step 3 - Identify Partitions
- Present a partition table with these columns:
  - `Partition`
  - `Input Class`
  - `Example Mutation or Setup`
  - `Expected Outcome`
  - `FR Mapping`
- Cover:
  - valid
  - invalid
  - exceptional (`null`, empty, wrong type)
  - combinations and precedence

## Section 6 - Step 4 - Analyse the Boundaries
- Present a boundary table with these columns:
  - `Boundary`
  - `In-Point (Expected)`
  - `Out-Point (Expected)`
  - `Rule`
- Include numeric, time, date, and requiredness or type boundaries when applicable.
- If the FRS does not define explicit numeric ranges, say so briefly and focus on explicit business boundaries instead of inventing ranges.

## Section 7 - Step 5 - Devise Test Cases
- Use these subheadings in this section:
  - `Lean suite (minimal complete)`
  - `Extended suite (full coverage)`
  - `Channel matrix`
  - `FR/AC mapping`
- Lean suite is mandatory.
- Extended suite is conditional. If it is not needed, say `Extended suite: not required for current risk profile`.
- Include the execution-target matrix per test case, or a shared matrix when every case uses the same coverage.
- Map each test to the relevant FR or AC lines.
- Keep bootstrap work, execution commands, and approval gating out of this section. Those belong in section 8.

## Section 8 - Plan + Approval Gate
- Make it explicit that this is the implementation plan and that no code changes have been made yet.
- Include:
  - files to add or modify
  - test names
  - style adoption map
  - deliberate deviations from existing style with rationale
  - per-test execution-target coverage and DB procedure mapping where needed
  - SP or API I/O structure usage for assertions and logging
  - category grouping allocation for lean and extended suites
  - test data approach from discovered I/O contracts
  - mocks or fakes needed
  - cleanup strategy using `disable` in `UAT`
  - audit and logging validation approach
  - execution commands
  - expected diagnostics or reporting
  - explicit skip criteria versus fail criteria
- When readiness is `bootstrap required`, describe bootstrap work inline in this section. Do not create a separate bootstrap section.
- Never ask `Approve bootstrap? (yes/no)`.
- Always end with `Approve implementation? (yes/no)`.
- Stop after the plan.

## Required step-by-step method
Follow this sequence exactly:

1. Confirm the FR or AC exists and capture the FRS text being used.
2. Confirm scope items that are already known or discoverable without inventing them.
3. Understand the requirement and flow.
4. Explore the repo and assess readiness.
5. Identify partitions.
6. Analyse boundaries.
7. Devise test cases.
8. Build the implementation plan and approval gate.

## Lean and extended suites
- Lean suite is mandatory.
- Extended suite is optional.
- Add the extended suite only when:
  - the user asks for it
  - the FR risk is high
  - multiple failure-precedence paths matter
  - significant date, money, or lifecycle boundaries exist

## Naming rules
- Test names must follow `test_<test_case_name>`.
- Use readable business action + condition + expected outcome wording.
- Generated folders and files must not include `fr` as a token.
- FR identifiers may appear in prose, traceability tables, and approval planning, but not in generated artifact names.
- Keep names stable across `api`, `db`, and `api+db`.

Good examples:
- `test_create_bonus_persists_when_deposit_qualifies`
- `test_turnover_reversal_reduces_total_when_refund_event_arrives`
- `test_completion_blocks_after_expiry_timestamp`

Bad examples:
- `test_case_01`
- `bonus_valid_case`
- `create_bonus_plan_case_08`

## Category buckets
Use category buckets only when implementing suites or allocating the implementation plan, not for analysis-only replies.

Required suite bucket patterns:
- `test_audit_and_defaults_<test_case_name>_plan`
- `test_create_update_and_retrieve_<test_case_name>_plan`
- `test_validation_boundaries_<test_case_name>_plan`
- `test_validation_required_<test_case_name>_plan`
- `test_validation_uniqueness_<test_case_name>_plan`
- `test_exception_<test_case_name>_plan`

## Logging expectations
- Log every DB procedure call used by tests.
- Log every API call used by tests.
- Log the fields required for assertions, audit checks, and diagnosis.
- Tie logged fields back to discovered input and output contracts.
- Validate both structure and expected values when the FRS requires them.

## Approval rule
Do not edit code before the section 8 approval gate is satisfied.
