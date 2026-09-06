# Architectural Decision Records (ADR)

## ADR-001: Modular Monolith vs. Microservices Architecture
- **Date**: 2026-09-04
- **Status**: Accepted
- **Context**: AuthTwin is a research framework for workflow-aware authorization analysis.
- **Decision**: Use a clean, modular python monolith (FastAPI + SQLAlchemy + SQLite) rather than microservices to guarantee determinism, simplicity of installation, low latency data processing, and seamless testability.

## ADR-002: Deterministic Baseline Dependency Analysis
- **Date**: 2026-09-04
- **Status**: Accepted
- **Context**: Dynamic parameter values (like project IDs) produced in early responses are consumed in later request parameters.
- **Decision**: Implement exact-value matching across normalized JSON response payloads and request parameter locations (path, query, header, body). This provides 100% explainable, deterministic baseline dependencies without relying on non-deterministic black-box heuristics in Milestone 1.

## ADR-003: Model-Only Shadow Workflow Boundary
- **Date**: 2026-09-04
- **Status**: Accepted
- **Context**: In Milestone 1, workflow models are cloned to alternate identities.
- **Decision**: Shadow workflows are strictly instantiated as structural models (`MODEL_ONLY`). No active HTTP request replay is executed against target servers in Milestone 1 to maintain a clear security boundary.
