# AuthTwin Master Architecture & Complete Codebase Presentation Reference Manual

> **Project Title**: AuthTwin — Autonomous Workflow-Aware API Identity & Security Twin Engine  
> **Repository Path**: `C:\Dev\Projects\AuthTwin2`  
> **Target Audience**: MCA Project Examiners, Technical Interviewers, System Architects, Cybersecurity Auditors, and Developers  
> **Documentation Version**: 2.0 (Authoritative Verification of Actual Repository Implementation)

---

## 1. Architectural Inventory & System Boundary

### 1.1 Backend Directory & File Structure (`backend/app/`)

```text
backend/app/
├── api/                        # REST API Router Endpoints
│   ├── dependencies.py         # /api/v1/dependencies endpoints
│   ├── health.py               # /api/v1/health status endpoint
│   ├── identities.py           # /api/v1/identities management endpoints
│   ├── imports.py              # /api/v1/imports/har upload endpoint
│   ├── interceptor.py          # /api/v1/interceptor reverse proxy & recording endpoints
│   ├── openapi.py              # /api/v1/openapi specification endpoints
│   ├── sessions.py             # /api/v1/sessions listing endpoints
│   ├── shadow.py               # /api/v1/shadow-workflows replay endpoints
│   ├── targets.py              # /api/v1/targets application configuration endpoints
│   ├── transactions.py         # /api/v1/transactions traffic listing endpoints
│   └── workflows.py            # /api/v1/workflows graph generation endpoints
├── core/                       # Infrastructure Core Settings & Database Setup
│   ├── config.py               # Application settings, port validation, control-plane isolation
│   ├── database.py             # SQLite engine, SessionLocal, seed data handlers
│   └── logging.py              # Credential redaction logger
├── dependencies/               # Dependency Analyzer Module
│   └── analyzer.py             # Producer-consumer value matching engine
├── identity/                   # Identity & Session Tracker Module
│   └── session_tracker.py      # Session grouping & token fingerprinting logic
├── ingestion/                  # Traffic Ingestion Module
│   └── har_parser.py           # HAR v1.2 JSON spec parser
├── models/                     # SQLAlchemy Database ORM Models
│   └── models.py               # 11 ORM Entities (Target, Identity, Session, Transaction, etc.)
├── openapi/                    # OpenAPI Loader Module
│   └── loader.py               # Path template matching engine
├── schemas/                    # Pydantic Data Contracts & Schemas
│   └── schemas.py              # CanonicalNodeSchema, CanonicalEdgeSchema, EdgeEvidenceSchema, etc.
├── services/                   # Business Logic Services Layer
│   ├── dependency_service.py   # Session parameter dependency analysis service
│   ├── identity_service.py     # Identity management service
│   ├── ingestion_service.py    # Traffic import service
│   ├── interceptor_service.py  # Reverse proxy & scope validation service
│   ├── openapi_service.py      # OpenAPI loader service
│   ├── session_service.py      # Session tracking service
│   ├── shadow_service.py       # Shadow workflow cloning service
│   ├── target_service.py       # Target configuration service
│   └── workflow_service.py     # Canonical graph & linear workflow generation service
├── shadow/                     # Shadow Workflow Module
│   └── cloner.py               # Model-only identity cloner
├── workflows/                  # Workflow State Graph Generator Module
│   └── wsg_generator.py        # High-level WSG generator
├── database.py                 # Core database export wrapper
├── logging.py                  # Core logging export wrapper
└── main.py                     # FastAPI Application Initialization & Router Aggregation
```

---

### 1.2 Frontend Directory & File Structure (`frontend/src/`)

```text
frontend/src/
├── api/                        # HTTP API Client Layer
│   └── client.ts               # Axios API client functions for all backend routes
├── components/                 # Shared UI & Graph Inspection Components
│   ├── Badge.tsx               # Method badge UI component
│   ├── GraphVisualizer.tsx     # Master Graph Visualizer container (2D/3D & Linear Drawer)
│   ├── Layout.tsx              # Shell layout navigation bar & workspace container
│   ├── NodeInspector.tsx       # Slide-out Canonical Node & Edge Evidence Inspector drawer
│   ├── StatCard.tsx            # Key-value statistical metric card component
│   └── TerminalConsole.tsx     # Live system execution terminal log console
├── graph/                      # Visual Graph Rendering Engine
│   ├── Renderer2D.tsx          # HTML5/SVG 2D Interactive Bezier Flowchart Renderer
│   ├── Renderer3D.tsx          # HTML5 Canvas 3D Spatial Visualizer Renderer
│   └── adapter.ts              # Data contract adapter converting API response to visual graph
├── pages/                      # Application Navigation Pages
│   ├── Dependencies.tsx        # Dynamic parameter dependencies table page
│   ├── Identities.tsx          # User identities registration page
│   ├── OpenAPI.tsx             # OpenAPI specification upload page
│   ├── Overview.tsx            # System metrics dashboard overview page
│   ├── Sessions.tsx            # Captured sessions listing page
│   ├── ShadowWorkflows.tsx     # Replay shadow workflows page
│   ├── TargetSandbox.tsx       # Live target probe, interceptor proxy, & sandbox workspace
│   ├── Traffic.tsx             # Recorded HTTP transactions traffic table page
│   └── Workflows.tsx           # Workflow state graphs list & viewer page
├── types/                      # TypeScript Interface Definitions
│   └── index.ts                # Data contracts matching backend Pydantic schemas
├── App.tsx                     # Main React Application Router & Navigation Shell
├── config.ts                   # AuthTwin frontend global API & proxy configuration
├── index.css                   # Tailwind CSS & glassmorphism theme styles
└── main.tsx                    # React DOM Application Root Renderer
```

---

## 2. Complete Function-by-Function Codebase Directory Reference

### 2.1 Backend Core Services & Modules (`backend/app/services/` & `backend/app/`)

| Directory Location | File Name | Function Name | Parameters | Return Type | Purpose & Internal Logic |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `backend/app/services/` | `workflow_service.py` | `build_canonical_graph` | `workflow_id: str`, `transactions: List[Transaction]`, `dependencies: List[Dependency]` | `Tuple[List[CanonicalNodeSchema], List[CanonicalEdgeSchema]]` | Aggregates repeated endpoint route templates (e.g. `/items/1` -> `/items/{id}`) into single canonical logical nodes, calculates in/out degrees, extracts parameter bindings (`DependencyBindingSchema`), evidence metrics (`EdgeEvidenceSchema`), cardinality (`1->1`, `1->N`, `N->1`, `N->N`), step distances, and validates structural graph integrity. |
| `backend/app/services/` | `workflow_service.py` | `build_linear_workflow` | `workflow_id: str`, `session: Session`, `transactions: List[Transaction]`, `dependencies: List[Dependency]` | `LinearWorkflowResponse` | Constructs the ground-truth Authoritative Linear Execution Workflow maintaining uncollapsed 1..N chronological step sequence for shadow replay. |
| `backend/app/services/` | `workflow_service.py` | `hash_deterministic_id` | `prefix: str`, `*parts: str` | `str` | Computes SHA-256 digests over prefix and string tokens to guarantee 100% reproducible Node and Edge IDs across runs. |
| `backend/app/services/` | `workflow_service.py` | `validate_canonical_graph` | `nodes: List[CanonicalNodeSchema]`, `edges: List[CanonicalEdgeSchema]` | `None` | Asserts non-empty graph rules and validates that edge source/target IDs exist in node set. |
| `backend/app/services/` | `workflow_service.py` | `normalize_path_template` | `path: str`, `resource_type: Optional[str]` | `str` | Normalizes path numbers and UUIDs into OpenAPI route parameters (e.g. `/projects/101` -> `/projects/{id}`). |
| `backend/app/services/` | `workflow_service.py` | `infer_resource_info` | `tx: Transaction` | `Tuple[Optional[str], Optional[str]]` | Infers resource type and identifier from URL path segments. |
| `backend/app/services/` | `workflow_service.py` | `generate_workflow_state_graph` | `db: DBSession`, `session_id: str` | `Workflow` | Database service generating Workflow, WorkflowNode, and WorkflowEdge records for a session. |
| `backend/app/services/` | `workflow_service.py` | `get_workflow_graph_details` | `db: DBSession`, `workflow_id: str` | `WorkflowGraphResponse` | Fetches graph nodes, edges, linear workflow, canonical graph, and dependencies for UI presentation. |
| `backend/app/services/` | `interceptor_service.py` | `validate_target_scope` | `target_url: str` | `str` | Validates target URL scheme, hostname, port, and blocks self-target loopbacks to AuthTwin ports (`5000`, `5173`) and cloud metadata endpoints (`169.254.169.254`). |
| `backend/app/services/` | `interceptor_service.py` | `validate_transaction_target` | `transaction_url: str`, `active_target_url: str` | `str` | Normalizes `localhost` vs `127.0.0.1`, strips `/api/v1/interceptor/proxy` prefixes, and converts relative paths to absolute target URLs cleanly. |
| `backend/app/services/` | `interceptor_service.py` | `rewrite_html_target_urls` | `html_str: str` | `str` | Scans HTML string and rewrites `src`, `href`, `action`, and `formaction` attributes to route through `/api/v1/interceptor/proxy/`. |
| `backend/app/dependencies/` | `analyzer.py` | `analyze_session_dependencies` | `db: DBSession`, `session_id: str` | `List[Dependency]` | Scans response body payloads for dynamic tokens/IDs, matches subsequent request headers, query parameters, or body values, and persists `Dependency` records. |
| `backend/app/identity/` | `session_tracker.py` | `process_and_group_session` | `db: DBSession`, `target_id: str`, `transactions_raw: List[Dict]`, `explicit_identity_id: Optional[str]` | `Tuple[Session, List[Transaction]]` | Groups transactions into a Session, extracts token fingerprints, and assigns target identity. |
| `backend/app/ingestion/` | `har_parser.py` | `parse_har_content` | `content_str: str` | `List[Dict[str, Any]]` | Parses HAR v1.2 JSON specification files and extracts HTTP request/response entries. |
| `backend/app/openapi/` | `loader.py` | `match_transactions_to_operations` | `db: DBSession`, `spec: OpenAPISpec` | `int` | Matches raw request URLs to OpenAPI operation IDs and path templates. |
| `backend/app/shadow/` | `cloner.py` | `clone_shadow_workflow` | `db: DBSession`, `source_workflow_id: str`, `shadow_identity_id: str` | `ShadowWorkflow` | Creates model-only shadow workflow clone for alternate identity replay testing. |
| `backend/app/core/` | `config.py` | `validate_infrastructure_ports` | `self` | `Settings` | Asserts API and Frontend ports are valid system ports between `1024` and `65535` and non-colliding. |
| `backend/app/core/` | `config.py` | `get_control_plane_endpoints` | `self` | `Set[Tuple[str, int]]` | Returns host/IP and port tuples representing AuthTwin control-plane listeners. |
| `backend/app/core/` | `database.py` | `get_active_target_model` | `db: DBSession` | `Optional[Target]` | Queries active Target model from SQLite database, deleting stale control plane entries. |
| `backend/app/core/` | `database.py` | `seed_demo_data` | `db: DBSession` | `None` | Seeds demo reference target (`http://127.0.0.1:8001`) and user identities (Alice, Bob). |
| `backend/app/core/` | `logging.py` | `redact_headers` | `headers: Dict[str, Any]` | `Dict[str, Any]` | Redacts sensitive authentication headers (`Authorization`, `Cookie`, `X-API-Key`, `Set-Cookie`). |

---

### 2.2 Backend API Handlers (`backend/app/api/`)

| Directory Location | File Name | Route Handler Function | HTTP Method & Path | Return Schema | Purpose & Execution Flow |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `backend/app/api/` | `interceptor.py` | `secret_proxy_middleware` | `ANY /api/v1/interceptor/proxy/{path:path}` | `Response / HTMLResponse` | Reverse proxy streaming middleware. Enforces scope rules, injects interceptor script into HTML, records live traffic to buffer, and forwards requests to active target. |
| `backend/app/api/` | `interceptor.py` | `verify_target_server` | `POST /api/v1/interceptor/verify` | `TargetVerifyResponse` | Probes target server URL via HTTP GET request, checking latency, status code, and server headers. |
| `backend/app/api/` | `interceptor.py` | `save_and_set_active_target` | `POST /api/v1/interceptor/target` | `TargetResponse` | Persists target URL as active target in SQLite database. |
| `backend/app/api/` | `interceptor.py` | `start_live_recording` | `POST /api/v1/interceptor/start-recording` | `Dict[str, Any]` | Starts live proxy recording session for selected identity ID. |
| `backend/app/api/` | `interceptor.py` | `stop_live_recording` | `POST /api/v1/interceptor/stop-recording` | `HARImportResult` | Stops live recording, ingests captured buffer transactions, runs session grouping, dependency analysis, and generates workflow state graph. |
| `backend/app/api/` | `interceptor.py` | `capture_live_session` | `POST /api/v1/interceptor/capture-session` | `HARImportResult` | Ingests live recorded transactions payload, running full WSG generation pipeline. |
| `backend/app/api/` | `targets.py` | `get_active_target` | `GET /api/v1/targets/active` | `TargetResponse` | Returns active project target configuration from DB. |
| `backend/app/api/` | `identities.py` | `create_identity` | `POST /api/v1/identities` | `IdentityResponse` | Registers a new user identity (`Primary` or `Alternate`) for target. |
| `backend/app/api/` | `imports.py` | `import_har_file` | `POST /api/v1/imports/har` | `HARImportResult` | Processes uploaded HAR v1.2 file, extracts transactions, and runs WSG generator. |
| `backend/app/api/` | `workflows.py` | `get_workflow_graph` | `GET /api/v1/workflows/{id}/graph` | `WorkflowGraphResponse` | Delivers complete workflow graph response including canonical graph, linear workflow, and edge evidence payloads. |
| `backend/app/api/` | `shadow.py` | `create_shadow_workflow` | `POST /api/v1/shadow-workflows` | `ShadowWorkflowResponse` | Generates a shadow workflow clone for alternate identity replay testing. |

---

### 2.3 Frontend Graph Visualizers & UI Components (`frontend/src/`)

| Directory Location | File Name | Function / Component | Props / Inputs | Render / Output | Purpose & User Interactions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `frontend/src/components/` | `GraphVisualizer.tsx` | `GraphVisualizer` | `nodes`, `edges`, `dependencies`, `rawGraphResponse` | `JSX.Element` | Master visualizer container. Renders 2D/3D visualizers, view mode toggles, Edge selection state, and the collapsible Authoritative Replay Workflow Drawer. |
| `frontend/src/components/` | `GraphVisualizer.tsx` | `handleSelectEdge` | `edge: CanonicalEdge` | `void` | Event handler setting `selectedEdge` and opening `NodeInspector` in Edge Evidence mode. |
| `frontend/src/components/` | `GraphVisualizer.tsx` | `handleJumpToLinearStep` | `stepIndex: number` | `void` | Expands Authoritative Replay Workflow Drawer and smoothly scrolls to step card. |
| `frontend/src/graph/` | `Renderer2D.tsx` | `Renderer2D` | `nodes`, `edges`, `selectedNode`, `selectedEdge`, `onSelectNode`, `onSelectEdge` | `JSX.Element (HTML5/SVG)` | Interactive 2D Flowchart visualizer. Renders node cards, Cubic Bezier connection lines, zoom/pan controls, and edge click listeners. |
| `frontend/src/graph/` | `Renderer3D.tsx` | `Renderer3D` | `nodes`, `edges`, `selectedNode`, `selectedEdge`, `onSelectNode`, `onSelectEdge` | `JSX.Element (Canvas 3D)` | 3D Spatial Visualizer. Maps 3D coordinates `(x, y, z)` to 2D canvas via perspective matrices, drawing light pulse animations and supporting 3D edge line segment picking. |
| `frontend/src/components/` | `NodeInspector.tsx` | `NodeInspector` | `node`, `edge`, `dependencies`, `onClose`, `onJumpToLinearStep` | `JSX.Element (Slide-out)` | Slide-out inspector drawer for Canonical Nodes and Edge Evidence payloads (bindings, cardinality, reason, step distance, and linear jump button). |
| `frontend/src/graph/` | `adapter.ts` | `adaptWorkflowResponseToCanonicalGraph` | `response: WorkflowGraphResponse` | `CanonicalGraph` | Adapter function converting backend graph payloads into visual graph data structures. |
| `frontend/src/pages/` | `TargetSandbox.tsx` | `TargetSandbox` | `onLogEvent`, `onNavigateToWorkflows` | `JSX.Element (Page)` | Target probe control, target URL configuration, live traffic interceptor recorder, embedded WSG graph preview, and iframe sandbox workspace. |

---

## 3. Database Deep Dive & Entity-Relationship Schema

```text
┌─────────────────┐        1:N        ┌─────────────────┐        1:N        ┌─────────────────┐
│     Target      │───────────────────┤    Identity     │───────────────────┤     Session     │
│ - id (PK)       │                   │ - id (PK)       │                   │ - id (PK)       │
│ - name          │                   │ - target_id(FK) │                   │ - target_id(FK) │
│ - base_url      │                   │ - name          │                   │ - identity_id(FK│
│ - created_at    │                   │ - role          │                   │ - started_at    │
└────────┬────────┘                   └─────────────────┘                   └────────┬────────┘
         │                                                                           │
         │ 1:N                                                                       │ 1:N
         ▼                                                                           ▼
┌─────────────────┐                   ┌─────────────────┐                   ┌─────────────────┐
│   OpenAPISpec   │                   │   Dependency    │                   │   Transaction   │
│ - id (PK)       │                   │ - id (PK)       │                   │ - id (PK)       │
│ - target_id(FK) │                   │ - producer_tx(FK│                   │ - session_id(FK)│
│ - title         │                   │ - consumer_tx(FK│                   │ - method        │
└────────┬────────┘                   │ - extracted_val │                   │ - path          │
         │ 1:N                        └────────┬────────┘                   │ - res_status    │
         ▼                                     │ 1:N                        └────────┬────────┘
┌─────────────────┐                            │                                     │ 1:N
│ OpenAPIOperation│                            │                                     │
└─────────────────┘                            ▼                                     ▼
                                      ┌─────────────────┐                   ┌─────────────────┐
                                      │  WorkflowEdge   │                   │  WorkflowNode   │
                                      │ - id (PK)       │                   │ - id (PK)       │
                                      │ - workflow_id(FK│                   │ - workflow_id(FK│
                                      └────────┬────────┘                   └────────┬────────┘
                                               │ 1:N                                 │ 1:N
                                               └──────────────────┬──────────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │    Workflow     │
                                                         │ - id (PK)       │
                                                         │ - session_id(FK)│
                                                         │ - identity_id(FK│
                                                         └─────────────────┘
```

---

## 4. End-to-End Data Pipeline & Graph Engine

```text
1. User Action in Target Sandbox / Iframe
   ↓ (HTTP Request)
2. Interceptor Proxy (`interceptor.py` secret_proxy_middleware)
   ↓ (Enforces scope rules, injects interceptor script, redacts secrets, forwards to target)
3. Target API Response (`http://127.0.0.1:8001`)
   ↓ (Captures transaction into live buffer memory)
4. Session Tracker (`session_tracker.py` process_and_group_session)
   ↓ (Assigns session ID, links target identity, fingerprints tokens)
5. Dependency Analyzer (`analyzer.py` analyze_session_dependencies)
   ↓ (Scans response bodies for dynamic values, matches consumer request parameters)
6. Canonical Workflow Builder (`workflow_service.py` build_canonical_graph & build_linear_workflow)
   ↓ (Constructs Linear Replay Workflow and Canonical Graph with SHA-256 IDs & Edge Payloads)
7. REST API Delivery (`/api/v1/workflows/{id}/graph`)
   ↓ (Pydantic serialization to WorkflowGraphResponse)
8. Frontend Adapter (`adapter.ts` adaptWorkflowResponseToCanonicalGraph)
   ↓ (Maps server response to visual graph contracts)
9. Dual Visualization (`Renderer2D.tsx` & `Renderer3D.tsx`)
   ↓ (Renders interactive 2D Bezier flowchart and 3D spatial orbit canvas)
10. Inspector & Replay (`NodeInspector.tsx` & `shadow_service.py`)
   ↓ (Analyst inspects edge evidence payload and executes shadow workflow replay)
```

---

## 5. Dual-Representation Architecture & Edge-Payload Evidence Model

### 5.1 Authoritative Linear Execution Workflow
- Strictly ordered 1..N chronological sequence of execution steps.
- Ground-truth target for shadow workflow replay engine.
- Retains individual HTTP request/response details, raw status codes, timestamps, and parameter bindings.

### 5.2 Canonical Hybrid Hierarchical Graph
- Route template path aggregation (collapses repeated endpoints like `/projects/101` and `/projects/102` into single `/projects/{id}` logical node).
- Preserves full execution trace by embedding every raw execution in a `CanonicalOccurrenceSummary` array.
- **Edge-Payload Model**: Edges encode exact parameter bindings, cardinality (`1->1`, `1->N`, `N->1`, `N->N`), step distance, and evidence metrics directly on directed edge structures.

---

## 6. Complete Test Suite Reference (`backend/tests/`)

| Test File | Total Tests | What It Validates |
| :--- | :--- | :--- |
| `test_canonical_graph.py` | 6 | 1->1, 1->N, N->1, N->N topologies, non-consecutive deps, repeated occurrences collapse, SHA-256 determinism |
| `test_workflow_graph_topologies.py` | 6 | Canonical state graph topological branching, merging, and route template aggregation |
| `test_interceptor_security.py` | 11 | SSRF protection, scope bounds, proxy loop prevention, credential redaction |
| `test_port_isolation.py` | 7 | Infrastructure port range validation (`1024-65535`) and port collision protection |
| `test_e2e_runtime_flow.py` | 1 | Complete 32-step end-to-end runtime flow (probe -> save -> identity -> proxy -> graph -> shadow clone) |
| `test_dependency_analyzer.py` | 2 | Producer-consumer parameter dependency extraction and false-positive filtering |
| `test_har_parser.py` | 2 | HAR v1.2 JSON specification parsing and empty HAR validation |
| `test_integration_workflow.py` | 1 | End-to-end Milestone 1 workflow integration |
| `test_session_tracker.py` | 2 | Session grouping and token fingerprinting |
| `test_shadow_cloner.py` | 1 | Shadow workflow clone generation |
| `test_wsg_generator.py` | 3 | WSG generation, dual representation, and graph determinism |
| `test_credential_isolation.py` | 1 | Redaction invariant policy enforcement |
| `test_openapi_loader.py` | 1 | OpenAPI path template matching |

**Total Suite**: 43 Unit & E2E Tests (**100% Pass Rate**).

---

## 7. Presentation Script & Viva Defense Guide

### 7.1 Presentation Script (10-15 Minutes)

#### Introduction (1 Minute)
> "Good morning, respected examiners. My project is AuthTwin — an Autonomous Workflow-Aware API Identity & Security Twin Engine. In modern web applications, authorization security flaws such as BOLA (Broken Object Level Authorization) are difficult to detect using traditional static scanners because web transactions are multi-step and contain dynamic parameter dependencies."

#### The Problem & Solution (2 Minutes)
> "Standard record-and-replay tools fail because when user Alice logs in and receives a token or project ID, user Bob cannot replay those exact same recorded requests — the IDs and tokens must be dynamically extracted and substituted. AuthTwin solves this by intercepting traffic, detecting dynamic parameter dependencies, and building a dual-representation model: an Authoritative Linear Execution Workflow for ground-truth replay, and a Canonical Hybrid Graph with Edge Evidence payloads for 2D/3D visual inspection."

#### Architecture & Pipeline (4 Minutes)
> "AuthTwin is built with Python FastAPI on the backend and React with TypeScript on the frontend. The data pipeline has five key stages:
> 1. Interception & Route Aggregation: Captures traffic via a secret proxy middleware, redacting credentials while mapping endpoints to OpenAPI templates like `/projects/{id}`.
> 2. Session Tracking & Identity Grouping: Groups transactions by identity and token fingerprint.
> 3. Dependency Analysis: Scans response payloads for values that appear in subsequent request headers, query parameters, or bodies.
> 4. Graph Construction: Computes SHA-256 deterministic IDs, edge parameter bindings, cardinality, and step distances.
> 5. Dual Visualization & Replay: Provides 2D SVG flowcharting, 3D HTML5 canvas rendering, and shadow workflow replay under alternate identities."

#### Conclusion & Key Results (2 Minutes)
> "All 43 unit and end-to-end automated tests pass cleanly. The system enforces strict credential isolation, SSRF protection, and deterministic reproducibility across all graph runs. Thank you, I am ready for your questions."

---

### 7.2 Top 20 Likely Examiner / Viva Questions & Answers

1. **Q: What is the main difference between AuthTwin's Linear Workflow and Canonical Graph?**  
   *A*: The Linear Workflow is an uncollapsed, strictly ordered 1..N chronological sequence of execution steps used as the ground-truth target for replay engines. The Canonical Graph is a state-aggregated 2D/3D topology that collapses repeated route templates (e.g. `/items/1` and `/items/2` into `/items/{id}`) while retaining exact occurrence indices and parameter edge evidence.

2. **Q: How does AuthTwin handle dynamic parameters like JWT tokens or resource IDs during replay?**  
   *A*: The Dependency Analyzer scans producer response payloads for dynamic values and links them to consumer request parameters. During replay, extracted bindings dynamically substitute fresh values produced by the replay session.

3. **Q: Why does AuthTwin use deterministic SHA-256 IDs for graph nodes and edges?**  
   *A*: Deterministic hashing via `hash_deterministic_id()` ensures that processing the exact same HTTP sequence produces identical Node and Edge IDs across multiple runs, guaranteeing 100% reproducibility.

4. **Q: How are sensitive credentials protected in AuthTwin?**  
   *A*: AuthTwin enforces a Credential Isolation Policy using `redact_headers()`, automatically sanitizing `Authorization`, `Cookie`, and secret keys before database storage or UI rendering.

5. **Q: What is the Edge-Payload Model in AuthTwin?**  
   *A*: Instead of storing relationship details inside nodes, directed edges directly encode parameter bindings (`DependencyBindingSchema`), cardinality (`1->1`, `1->N`, etc.), step distance, and evidence metrics.

6. **Q: How does the 3D visualizer work in AuthTwin?**  
   *A*: `Renderer3D.tsx` maps 3D spatial coordinates `(x, y, z)` onto an HTML5 Canvas using perspective depth transformation matrices, rendering animated glowing light pulse packets along directed edges.

7. **Q: How are 2D and 3D visualizers synchronized?**  
   *A*: Both visualizers consume the exact same `CanonicalGraph` data payload. Selecting a node or edge in either view updates the shared selection state and triggers the `NodeInspector`.

8. **Q: What is Cardinality in AuthTwin edges?**  
   *A*: Cardinality classifies structural transitions: `1->1` (single producer to single consumer), `1->N` (one producer value branching to multiple downstream calls), `N->1` (multiple upstream nodes converging), and `N->N` (multi-occurrence transitions).

9. **Q: How does AuthTwin prevent proxy loop recursion?**  
   *A*: `secret_proxy_middleware` checks for the `X-AuthTwin-Proxy` header. If present, it halts forwarding and raises an HTTP 400 Proxy Loop Error.

10. **Q: What database engine is used in AuthTwin?**  
    *A*: AuthTwin uses SQLite (`authtwin.db`) with SQLAlchemy declarative ORM models and `NullPool` connection management.

11. **Q: How does AuthTwin validate target scope?**  
    *A*: `validate_target_scope()` inspects URL scheme, hostname, port, and IP address, blocking self-target loopbacks to AuthTwin control plane ports and cloud metadata endpoints (`169.254.169.254`).

12. **Q: How does AuthTwin group requests into sessions?**  
    *A*: `process_and_group_session()` extracts token fingerprints (e.g. Bearer token hashes) and links incoming transactions to active target identities in the database.

13. **Q: How does OpenAPI integration improve path template matching?**  
    *A*: `match_transactions_to_operations()` matches raw URLs against OpenAPI path templates (e.g. `/api/v1/projects/{id}`), allowing AuthTwin to group requests by operation ID.

14. **Q: What is a Non-Consecutive Dependency?**  
    *A*: A transition where a step produces a parameter consumed by a later step that is not immediately adjacent (e.g. Step #1 producing a `cart_id` consumed by Step #4). The edge records `step_distance = 3`.

15. **Q: How are repeated API occurrences handled?**  
    *A*: Multiple calls to the same endpoint are collapsed into a single `CanonicalNode` while every raw call is preserved as an entry in the node's `occurrences` array.

16. **Q: What is the purpose of `adapter.ts` in the frontend?**  
    *A*: `adapter.ts` converts backend `WorkflowGraphResponse` payloads into visual graph data structures consumable by 2D and 3D renderers.

17. **Q: What happens when an edge is clicked in the UI?**  
    *A*: Clicking an edge sets `selectedEdge` state in `GraphVisualizer.tsx` and opens `NodeInspector.tsx` in Edge Evidence mode, displaying parameter bindings, cardinality, and evidence metrics.

18. **Q: How does the "View Step" button in NodeInspector work?**  
    *A*: Clicking "View Step #X" invokes `onJumpToLinearStep(stepIndex)`, expanding the Authoritative Replay Workflow Drawer and smoothly scrolling to the target step.

19. **Q: What unit testing framework is used in AuthTwin?**  
    *A*: Pytest (with 43 unit and end-to-end test cases covering topologies, security, dependency analysis, and graph determinism).

20. **Q: Is AuthTwin production-ready for MCA demonstration?**  
    *A*: Yes. The codebase features complete 2D/3D graph visualization, ground-truth linear replay, full edge-payload evidence modeling, 100% backend test suite pass rate, and presentation documentation.

---
*AuthTwin Architecture & Complete Codebase Presentation Manual — Version 2.0*
