# Discovery And Pack

## Contents
- Execution-target normalization
- FRS and flow parsing
- Flow-to-test mapping
- Repo discovery order
- Readiness assessment
- Source precedence
- Blocking-section rule
- FR Answer Pack model
- Unresolved FRS details

## Execution-target normalization
Use the internal execution-target model:
- `api`
- `db`
- `api+db`

Accept repo- or user-specific labels such as:
- `promotion_api`
- `transport_api`
- `client_db`
- `syx_db`

Normalization rules:
- API-like labels map to `api`
- DB-like labels map to `db`
- combined coverage maps to `api+db`

Show the original label in section 2 as `Channel coverage`, and show the normalized execution target when it adds clarity.

If the label cannot be mapped confidently, stop in section 2 and ask only for the missing coverage clarification.

## FRS and flow parsing
Use the selected FRS document as the primary business source when it is present and non-empty.

Read any supplied flow diagram first. Supported forms include:
- attached image or screenshot
- Mermaid or other text-based diagram
- arrow-based text flow embedded in the FRS

Extract the ordered flow from the diagram or FRS, including:
- trigger event
- qualification or decision points
- status transitions
- external lookups or calls
- persisted side effects and audit points
- terminal outcomes

If no usable diagram exists, derive the flow from:
- process descriptions
- `Given/When/Then` scenarios
- FR ordering and lifecycle states

State explicitly when no diagram support was provided.

Parse what the chosen FRS actually contains, for example:
- FR sections and acceptance criteria sections
- per-FR blocks such as `Requirement`, `Acceptance criteria`, `Applicability`, and `Outcome`
- `Given/When/Then` scenarios or other examples
- unresolved implementation details called out in the FRS

Map the FRS structure like this:
- `Requirement` -> user-story intent
- `Acceptance criteria` -> success and failure assertions
- `Applicability` -> scenario scope
- `Outcome` -> logging and final-state assertions
- `Given/When/Then` -> default AAA seed

If the diagram is incomplete, use the FRS text to fill gaps. If the diagram conflicts with the FRS text or repo contracts, record the mismatch and follow the FRS for business meaning and repo discovery for real contracts.

## Flow-to-test mapping
Convert the selected flow into ordered implementation and test steps:
1. identify the trigger, preconditions, and qualifying inputs
2. identify each decision point or state transition
3. identify each external dependency, lookup, or event handoff
4. identify the resulting persistence, audit, balance, or history effect
5. identify the terminal success, failure, expiry, or reversal outcome

Map each flow step into the default test shape:
- setup from trigger and preconditions
- action from the selected flow step
- assertions from the resulting state, output, audit, or side effect

## Repo discovery order
Use repo discovery before asking the user for API or DB contracts.

For API discovery:
- search controllers, routes, handlers, clients, DTOs, contracts, and tests
- prefer existing component structure over new wrappers
- run `python scripts/discover_api_contracts.py --root . --query "<fr keywords>"`

For DB discovery:
- search repositories, stored-procedure wrappers, SQL files, data access services, and tests
- prefer existing procedure wrappers and mappers over new raw access code
- run `python scripts/discover_db_contracts.py --root . --query "<fr keywords>"`

Also inspect the nearest existing test baseline for the selected target:
- folder structure and file naming
- helper, builder, and fixture patterns
- setup, teardown, and assertion style
- environment or config entry points already used by nearby tests

Capture provenance for every discovered contract:
- `contract_source`: `repo`, `pack`, or `user`
- `source_paths`: repo files or pack files used

## Readiness assessment
Assess readiness separately for each selected execution target.

Use this checklist:
- concrete target contract is known from repo code, pack, or user clarification
- nearest target-specific test or helper baseline exists
- required environment or auth configuration path is known
- required fixtures, builders, or wrappers exist or can be scaffolded
- logging and assertion points can be tied back to the contract and FRS outcome

Classify readiness like this:
- `ready`: concrete contract is known and a nearby automation baseline exists
- `bootstrap required`: concrete contract is known, but target-specific automation structure or baseline is missing
- `blocked`: concrete contract is still unknown after repo search, pack lookup, and user clarification

Treat `empty target contract discovery + absent nearby test baseline` as the repo-not-ready signal, then decide whether the result is bootstrapable or blocked by checking the pack and user clarification.

Record readiness inside section 4.

## Source precedence
Use these precedence rules and do not invert them:

For business meaning and expected behavior:
1. FRS text
2. flow diagram
3. FR Answer Pack
4. user clarification

For technical contracts and readiness:
1. repo code
2. FR Answer Pack
3. user clarification

If repo and pack disagree, surface the conflict and ask only for the unresolved choice. Do not use a flow diagram to override a concrete API or DB contract.

## Blocking-section rule
Map blockers to the earliest output section and stop there:

- section 1:
  - FRS missing
  - FR or AC missing
- section 2:
  - channel coverage unresolved
  - execution-target normalization unresolved
  - coverage model unresolved
  - environment unresolved
  - cleanup rule unresolved
  - baseline fixture or payload source unresolved when needed for deterministic planning
- section 3:
  - business rule, outcome, or FRS wording still too ambiguous for deterministic assertions after FRS and pack review
- section 4:
  - concrete API path still unknown
  - concrete DB procedure still unknown
  - required payload or output field still unknown
  - readiness is `blocked`
  - no nearby style baseline exists and no bootstrapable automation path can be defined yet
- section 8:
  - the plan is complete but approval has not yet been granted

When blocked:
- stop in that section
- ask only the targeted unresolved questions for that blocker
- do not emit later sections as placeholders
- do not fabricate partitions, boundaries, test cases, or implementation steps

## FR Answer Pack model
FR Answer Packs are optional approved metadata caches.

Use them to:
- preserve previously approved mappings
- fill gaps left by repo discovery
- store deterministic data-generation hints
- keep source provenance for contracts

Do not use them to:
- replace a clear repo contract
- bypass FRS validation
- force API or DB coverage that the user did not request

### Pack schema
```yaml
fr_id: FR-08
status: draft | proposed | approved | superseded
version: 2

clarifications:
  execution_targets: [api, db]
  environment: UAT
  cleanup_mode: disable

api:
  calls:
    create_bonus:
      method: POST
      path: /casino-bonus
      request:
        - { name: playerId, type: string, required: true }
      response_success:
        - { name: aggregationId, type: string }
      response_error:
        - { name: message, type: string }
      contract_source: repo
      source_paths:
        - src/promotions/controller.ts

db:
  procedures:
    create: dbo.CasinoBonus_Create
  io_contracts:
    create:
      input:
        - { name: PlayerId, type: bigint, required: true }
      output:
        - { name: AggregationId, type: uniqueidentifier }
      contract_source: repo
      source_paths:
        - src/data/CasinoBonusRepository.cs
```

### Legacy normalization
If a pack still uses `clarifications.channels`, normalize it to `clarifications.execution_targets`.

Only require selected-target fields:
- `api` selected -> `api.calls`
- `db` selected -> `db.procedures` and `db.io_contracts`

Missing pack files do not block planning if repo discovery is sufficient.

## Unresolved FRS details
If the FRS says implementation detail is unresolved, use this order:

1. Search the repo for the missing field or contract.
2. Check the FR Answer Pack for an approved answer.
3. Ask the user only if neither source resolves it.

If the automation repo is empty and the FRS only provides business wording, ask for the missing concrete API path, DB procedure, or payload or output details before writing wrappers or tests.

Examples of unresolved items that may need this process:
- funding-source exclusion field
- reversal contract shape
- expiry derivation field or model

Mark each one as:
- `resolved by repo`
- `resolved by pack`
- `still unresolved`

If an unresolved item blocks business meaning, stop in section 3. If it blocks a concrete contract or readiness, stop in section 4.
