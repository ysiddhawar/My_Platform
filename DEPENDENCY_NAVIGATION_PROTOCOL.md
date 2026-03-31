# Dependency Navigation Protocol

This document defines the safe way to approach future feature work in `My_Platform` without getting lost in cross-folder dependencies or destabilizing existing behavior.

## 1. Core Principle

Always approach feature work in dependency order, not in UI order.

Safe order:

1. `models/`
2. `execution_tools/` and `discipline/`
3. `connectors/`
4. `persistence_layer/`
5. `ai/`
6. `api/`
7. `web_app/`

Do not reverse this order for features that affect behavior, storage, journaling, or AI.

## 2. Folder Ownership Map

Use this ownership map before changing any file.

### `models/`
Owns:
- canonical data contracts
- trade/event/report structures
- serialized state shape

Typical changes:
- new field on a trade
- new event payload
- new structured behavioral capture object

### `execution_tools/`
Owns:
- trade planning
- position sizing
- execution approval path
- price/risk/reward calculations

Typical changes:
- new execution calculation
- position sizing logic
- pre-trade validation

### `discipline/`
Owns:
- rule evaluation
- discipline scoring
- strict mode / governance controls
- rule violations vs warnings

Typical changes:
- checklist compliance logic
- rule-blocking behavior
- discipline thresholds

### `connectors/`
Owns:
- trade lifecycle event ingestion
- normalized broker/platform events
- filled/closed trade updates

Typical changes:
- capturing new data on fill/close
- event routing
- trade state transitions

### `persistence_layer/`
Owns:
- durable storage
- repositories
- retrieval for journal/history

Typical changes:
- storing new trade fields
- new repository
- retrieval endpoints support

### `ai/`
Owns:
- interpretation of stored signals
- diagnosis
- behavioral analysis

Typical changes:
- new behavioral signals
- new diagnosis inputs
- new explanatory outputs

### `api/`
Owns:
- external interface only
- request/response validation
- thin exposure of internal services

Typical changes:
- adding endpoints
- extending endpoint schemas

### `web_app/`
Owns:
- user interaction
- workflow sequencing
- visual state
- frontend presentation

Typical changes:
- new forms
- dashboards
- visual guidance
- UX alerts

## 3. Decision Tree Before Any Feature

Before coding, classify the feature.

Ask:

1. Does it create or change stored data?
2. Does it affect whether a trade is allowed?
3. Does it happen during event lifecycle?
4. Does it need persistence/history?
5. Does AI need to interpret it?
6. Does it need API exposure?
7. Does it need UI input or display?

Then route it:

- data contract -> `models/`
- trade gating -> `execution_tools/`, `discipline/`
- lifecycle capture -> `connectors/`
- storage -> `persistence_layer/`
- analysis -> `ai/`
- endpoint -> `api/`
- interface -> `web_app/`

## 4. Contract-First Rule

If a feature is not trivial, define its contract first.

Contract means:
- input shape
- internal state shape
- stored output shape
- AI-consumed shape

In this project, that usually starts in:
- `models/execution_event.py`
- `models/trade.py`
- or a new `models/*.py` file

Do not spread raw dicts across multiple folders first and formalize later.

## 5. Additive Change Rule

Prefer:

1. add helper/model/service
2. integrate into existing owner module
3. keep old methods and fields working
4. expose upstream only after backend is stable

Avoid:
- replacing public methods immediately
- renaming core fields without compatibility
- rewriting a whole module when extension is enough

## 6. The Core Hub Rule

`core/` is the shared dependency hub.

Rule:
- do not use `core/` as the default place for new feature logic
- touch `core/` only if the feature truly changes a platform-wide contract

For most product features, `core/` should remain untouched.

## 7. Analytical Side Protection Rule

These folders are primarily analytical consumers:

- `metrics/`
- `portfolio/`
- `robustness/`
- `capital/`
- `risk_control/`
- `stress/`
- `survival/`

Rule:
- do not route execution, journaling, or UI workflow features through them unless the feature genuinely creates a new metric

This prevents graph-level regressions.

## 8. Trade Lifecycle Path

For any execution/journal/discipline feature, follow this path:

1. `models/execution_event.py`
2. `execution_tools/execution_orchestrator.py`
3. `discipline/execution_gatekeeper.py` if rules are involved
4. `connectors/trade_listener.py`
5. `models/trade.py`
6. `persistence_layer/trade_repository.py`
7. `ai/behavioral_analyzer.py`
8. `api/...`
9. `web_app/...`

If a feature skips this path and jumps straight to API or UI, stop and reassess.

## 9. Hard Block vs Evidence Rule

For every behavior-related feature, explicitly separate:

- what blocks execution
- what is only recorded
- what AI interprets later

Placement:

- hard block -> `execution_tools/`, `discipline/`
- evidence capture -> `models/`, `connectors/`, `persistence_layer/`
- interpretation -> `ai/`

Do not mix these responsibilities.

## 10. Helper Engine Rule

If logic is:
- cross-market
- cost-based
- formula-driven
- reused across multiple call sites

create a helper/service file instead of embedding it inside:
- router
- repository
- page
- giant orchestrator method

Examples:
- cost engine
- market spec resolver
- minimum target engine

## 11. Thin API Rule

`api/` must remain thin.

Allowed in `api/`:
- request validation
- response formatting
- service delegation

Not allowed in `api/`:
- core business logic
- calculations that backend services should own
- duplicated rule engines

## 12. Backend Authority Rule

`web_app/` should not become the source of truth for:
- approval/rejection
- trade validity
- stored behavioral data
- AI logic

Frontend can own:
- guidance
- sequencing
- highlighting
- interaction flow

Backend must own:
- actual validation
- calculations
- storage
- analysis inputs

## 13. Single Owner Rule

Each concern should have one primary owner.

Examples:
- setup catalog -> persistence/model/service layer
- trade approval -> execution layer
- discipline evaluation -> discipline layer
- journal retrieval -> persistence/API
- diagnosis -> AI layer
- user workflow -> frontend

If two different folders both start owning the same logic, stop and refactor the plan.

## 14. Safe Implementation Order

Use this exact order when implementing future features:

1. inspect owner files
2. define contract
3. add helper/model files
4. extend owner module
5. extend persistence
6. extend AI if needed
7. add API exposure
8. add UI
9. run targeted verification
10. run broad compile/import verification

## 15. Verification Protocol

After each phase, run the verification that belongs to that phase.

Examples:

- model phase -> serialization/compile check
- execution phase -> approval/rejection tests
- connector phase -> event flow tests
- persistence phase -> repository round-trip tests
- AI phase -> signal extraction tests
- API phase -> endpoint smoke checks
- UI phase -> build/type checks and interaction review

Do not postpone all validation to the end.

## 16. Red-Flag Conditions

Stop and reassess if a feature plan requires:

- touching `core/` without a platform-wide reason
- editing `metrics/` for an execution-only feature
- duplicating logic in `api/` and `web_app/`
- storing important behavior only in frontend state
- spreading raw dict fields across many modules without a formal model
- changing several architectural layers at once without a contract-first step

## 17. Safe vs Usually Avoid

Usually safe for feature work:

- `models/`
- `execution_tools/`
- `discipline/`
- `connectors/`
- `persistence_layer/`
- `ai/`
- `api/`
- `web_app/`

Usually avoid unless clearly required:

- `core/`
- `metrics/`
- `portfolio/`
- `robustness/`
- `capital/`
- `risk_control/`
- `stress/`
- `survival/`
- `risk_modeling/`

## 18. Short Routing Checklist

Use this checklist before any new feature:

1. What data is new?
2. Where is the canonical model?
3. Who owns execution behavior?
4. Who captures lifecycle events?
5. Where is it stored?
6. Does AI need it?
7. Which API exposes it?
8. Which UI consumes it?
9. What blocks execution?
10. What is only recorded evidence?

If you cannot answer these before editing, the feature is not ready to implement safely.

