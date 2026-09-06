# AuthTwin Architecture Specification (Milestone 1)

## 1. System Overview

AuthTwin is built around the **Deterministic Workflow-Aware Shadow-Session Architecture (DWA-SSA)**.
In Milestone 1, the system focuses on **Workflow Reconstruction** and **Shadow Workflow Model Duplication**.

---

## 2. Core Modules (M1 Scope)

| Module # | Module Name | M1 Status | Primary Responsibility |
|---|---|---|---|
| 1 | Request Interceptor / Ingestion | **IMPLEMENTED** | Ingest HAR 1.2 files and normalize raw HTTP pairs into `Transaction` records. |
| 2 | Session Tracker | **IMPLEMENTED** | Associate transactions with `Identity` and `Session` entities based on token continuity & credentials fingerprints. Redacts secrets. |
| 3 | OpenAPI Specification Loader | **IMPLEMENTED** | Ingest OpenAPI 3.x specs, resolve operational templates (`/projects/{id}`), map HTTP transactions to operations. |
| 4 | Dependency Analyzer | **IMPLEMENTED** | Extract dynamic producer-consumer relationships (`RESPONSE_TO_PATH`, `RESPONSE_TO_BODY`, etc.) via exact value matching. |
| 5 | Workflow State Graph Generator | **IMPLEMENTED** | Construct directed Workflow State Graphs (WSG) connecting operation nodes and dependency edges using NetworkX. |
| 6 | Ownership Mapper | **PARTIAL (M1)** | Associate created resources (`project:101`) with creator identity metadata. |
| 7 | Authorization Comparator | **DEFERRED (M2+)** | Compare differential replay responses. |
| 8 | Differential Replay Engine | **DEFERRED (M2+)** | Execute controlled shadow identity HTTP replay against target APIs. |
| 9 | Violation Detection Engine | **DEFERRED (M2+)** | Classify BOLA / IDOR / BFLA / BAC authorization vulnerabilities. |
| 10 | Reporting Module | **DEFERRED (M2+)** | Export vulnerability findings & evidence packages. |
| 11 | Dashboard | **IMPLEMENTED** | Dark technical SOC-style interface for observing workflows, WSG graphs, and cloning shadow workflows. |
| 12 | Configuration Manager | **IMPLEMENTED** | Manage system settings, target registration, identity definitions. |
| 13 | Logger | **IMPLEMENTED** | Structured, credential-redacted logging across backend components. |
| 14 | Evidence Collector | **PARTIAL (M1)** | Immutable snapshot of workflow model state and dependency proofs. |

---

## 3. Data Pipeline & Schema Relationships

```text
[HAR File / OpenAPI Spec]
          │
          ▼
    [Transaction]  ──────►  [OpenAPIOperation]
          │
          ▼
      [Session]    ──────►  [Identity]
          │
          ▼
     [Dependency]  (Producer Transaction ──► Consumer Transaction)
          │
          ▼
     [Workflow]    ──────►  [WorkflowNode] & [WorkflowEdge]
          │
          ▼
 [ShadowWorkflow]  (Bound to Alternate Identity, Credentials Stripped, MODEL_ONLY)
```

---

## 4. Security & Credential Isolation Invariants

- **Credential Redaction**: Raw JWT tokens, Session Cookies, and API keys are hashed/fingerprinted for session tracking, but never stored or logged in plain text.
- **Shadow Credential Isolation**: Cloning a workflow creates a model bound to an alternate `Identity`. Under no circumstances are the source identity's tokens copied into the shadow workflow state.
- **Model-Only Flag**: All shadow workflows are instantiated with status `MODEL_ONLY` to explicitly signify that no automated request replay or vulnerability assertion has occurred.
