# AUTHTWIN — COMPLETE 50% MILESTONE CODE AUDIT, ARCHITECTURE ANALYSIS & DEVELOPER TEACHING GUIDE

> **System Baseline**: AuthTwin (Milestone 1 — Workflow Reconstruction & Shadow Workflow Model Duplication Foundation)  
> **Repository Path**: `c:\Dev\Projects\AuthTwin2`  
> **Primary Stack**: Python 3.11+ / FastAPI / SQLAlchemy / SQLite / NetworkX / React 18 / TypeScript / Vite / Tailwind-styled CSS  

---

# PART A — Executive Summary

AuthTwin is a research-driven, workflow-aware authorization testing framework designed to discover complex security vulnerabilities such as **Broken Object Level Authorization (BOLA)**, **Insecure Direct Object References (IDOR)**, **Broken Function Level Authorization (BFLA)**, and **Broken Account Authorization (BAC)** in REST APIs and multi-tenant web applications.

Existing API security scanners (e.g., OWASP ZAP, Burp Suite active scanner) evaluate HTTP requests in isolation. They replay static API calls out of context, failing to understand multi-step state dependencies (e.g., *User A creates Project 101, acquires a dynamic session resource token, and subsequently accesses Document 202 inside Project 101*).

AuthTwin bridges this gap by constructing a **Workflow State Graph (WSG)** from real authenticated user interactions. At the **50% Milestone (Milestone 1)**, AuthTwin implements:
1. **Live & HAR Traffic Ingestion**: Reverse-proxy middleware interception and HAR 1.2 file parsing into normalized `Transaction` entities.
2. **Identity & Session Tracking**: Cryptographic token fingerprinting (SHA-256) and credential redaction.
3. **OpenAPI 3.x Specification Loading**: Dynamic route template matching (`/projects/{id}`) and operation mapping.
4. **Exact Value Dependency Analysis**: Automated detection of dynamic producer-consumer relationships across JSON bodies, path parameters, query strings, and headers.
5. **Workflow State Graph (WSG) Generation**: Directed graph construction using NetworkX, persisted as `WorkflowNode` and `WorkflowEdge` tables in SQLite.
6. **Shadow Workflow Duplication under Credential Isolation**: Cloning structural workflow models to alternate identities with status strictly set to `MODEL_ONLY`.

---

# PART B — Current 50% Milestone

## 1. Scope Accomplished (Milestone 1)
- **Reconstruction Engine**: Transforms raw HTTP traffic into an explainable, deterministic directed graph.
- **Data Dependency Engine**: Identifies exactly which HTTP response fields produce values consumed by subsequent request paths/queries/bodies.
- **Shadow Model Engine**: Clones the structural sequence and dependencies of a primary user's workflow into an alternate user's identity model without copying authentication tokens.
- **Control & Target Plane Isolation**: Strictly isolates AuthTwin's management workstation (Ports 5000-5999) from target applications.

## 2. Intentionally Deferred (Milestone 2 - Remaining 50%)
- **Controlled Differential Request Replay Engine**: Executing real replayed HTTP transactions under alternate shadow identity tokens.
- **Response Authorization Comparator**: Comparing response status codes, body lengths, and structural JSON deltas between primary and shadow executions.
- **Violation Classification Engine**: Automated assertion of BOLA / IDOR / BFLA vulnerabilities.
- **Evidence Collector & Report Exporter**: Generating PDF/HTML reports with cryptographic proof chains.

---

# PART C — Actual Repository Architecture

## 1. Repository Inventory Map

```text
AuthTwin2/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI REST endpoints & Reverse Proxy Interceptor
│   │   │   ├── dependencies.py   # GET /api/v1/dependencies
│   │   │   ├── health.py         # GET /api/v1/health
│   │   │   ├── identities.py     # CRUD /api/v1/identities
│   │   │   ├── imports.py        # POST /api/v1/import/har, /import/openapi
│   │   │   ├── interceptor.py    # Live proxy middleware, scope validation, recording controls
│   │   │   ├── openapi.py        # GET /api/v1/openapi/specs
│   │   │   ├── sessions.py       # GET/DELETE /api/v1/sessions
│   │   │   ├── shadow.py         # GET /api/v1/shadow-workflows
│   │   │   ├── targets.py        # CRUD & probe /api/v1/targets
│   │   │   ├── transactions.py   # GET /api/v1/transactions
│   │   │   └── workflows.py      # GET/DELETE /api/v1/workflows, graph, clone
│   │   ├── dependencies/
│   │   │   └── analyzer.py       # Producer-consumer parameter matching logic
│   │   ├── identity/
│   │   │   └── session_tracker.py# Token fingerprinting & transaction session grouping
│   │   ├── ingestion/
│   │   │   └── har_parser.py     # HAR v1.2 file parsing & normalization
│   │   ├── models/
│   │   │   └── models.py         # SQLAlchemy ORM models (11 tables)
│   │   ├── openapi/
│   │   │   └── loader.py         # OpenAPI JSON/YAML parser & route template matcher
│   │   ├── schemas/
│   │   │   └── schemas.py        # Pydantic v2 validation & response DTOs
│   │   ├── shadow/
│   │   │   └── cloner.py         # Credential-isolated ShadowWorkflow cloner
│   │   ├── workflows/
│   │   │   └── wsg_generator.py  # NetworkX Workflow State Graph builder
│   │   ├── config.py             # System settings & port validation
│   │   ├── database.py           # SQLAlchemy engine, session maker, target validation
│   │   ├── logging.py            # Credential-redacting logger
│   │   └── main.py               # FastAPI application entry point
│   ├── tests/                    # 11 Pytest unit & integration test files
│   ├── authtwin.db               # SQLite persistent database
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts         # Axios API client connecting to FastAPI
│   │   ├── components/
│   │   │   ├── Badge.tsx         # Technical UI status pill badge
│   │   │   ├── GraphVisualizer.tsx # Interactive Canvas/SVG WSG Graph Explorer
│   │   │   ├── Layout.tsx        # Command rail & workstation frame
│   │   │   ├── StatCard.tsx      # System stat card
│   │   │   └── TerminalConsole.tsx# Live SOC-style event console
│   │   ├── pages/
│   │   │   ├── Dependencies.tsx  # Extracted producer-consumer links view
│   │   │   ├── Identities.tsx    # Primary & Alternate identity management
│   │   │   ├── OpenAPI.tsx       # OpenAPI specification inspector
│   │   │   ├── Overview.tsx      # System architecture & status dashboard
│   │   │   ├── Sessions.tsx      # Tracked user session explorer
│   │   │   ├── ShadowWorkflows.tsx # Cloned shadow model manager
│   │   │   ├── TargetSandbox.tsx # Live target proxy workspace & iframe runner
│   │   │   ├── Traffic.tsx       # Raw transaction inspector with headers/body
│   │   │   └── Workflows.tsx     # WSG graph visualizer & clone trigger page
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript interfaces matching backend DTOs
│   │   ├── App.tsx               # Root tab router & state container
│   │   ├── config.ts             # Frontend environment constants
│   │   └── main.tsx              # React DOM entry point
│   └── package.json              # Vite + React npm manifest
├── fixtures/                     # Test HAR files & OpenAPI specifications
├── scripts/                      # Startup, dev environment, and cleanup scripts
├── target/
│   └── reference-api/
│       └── app.py                # Reference mock Target API (Port 8090)
├── ARCHITECTURE.md               # Architectural specification
├── DECISIONS.md                  # Architectural Decision Records (ADRs)
├── DO_NOT_INVENT.md              # Non-negotiable scope invariants
├── IMPLEMENTATION_STATUS.md      # Detailed 14-module milestone tracking
├── README.md                     # Framework setup guide
├── start-dev.bat                 # Windows startup script
└── start-dev.ps1                 # PowerShell startup script
```

---

# PART D — Complete Runtime Flow

## Live Interception & Workflow Reconstruction Flow

```text
[User Browser / TargetSandbox]
              │
   1. HTTP Request to Target
              ▼
[Reverse Proxy Middleware] ───► `validate_target_scope()` (Prevents SSRF & Self-Target Loops)
 (`/api/v1/interceptor/proxy`)
              │
   2. Forwards to Target Application (e.g., http://127.0.0.1:8090)
              │
   3. Receives Response & Injects JS Interceptor Script + Base Tag
              │
   4. Buffers Redacted Transaction into `active_recording_sessions`
              │
              ▼ (User Clicks "Stop Recording" or "Capture Session")
[`stop_live_recording()` / `capture_live_session()`]
              │
   5. `process_and_group_session()` ──► Generates SHA-256 Token Fingerprint
              │                         Saves `Session` & `Transaction` records
              │
   6. `match_transactions_to_operations()` ──► Resolves paths against OpenAPI spec (`/projects/{id}`)
              │
   7. `analyze_session_dependencies()` ──► Extracts values (`response.body.id` -> `PATH segment_1`)
              │                            Saves `Dependency` records
              │
   8. `generate_workflow_state_graph()` ──► Builds NetworkX DiGraph
              │                             Saves `WorkflowNode` & `WorkflowEdge` records
              │
              ▼
[React UI Dashboard / Workflows Page]
   9. Fetches GET `/api/v1/workflows/{id}/graph`
  10. `GraphVisualizer.tsx` Renders Interactive Directed Node-Edge Hologram Graph
```

---

# PART E — Backend File-by-File Analysis

### 1. `backend/app/main.py`
- **Responsibility**: Application entrypoint. Instantiates FastAPI, configures CORS middleware, mounts 11 API routers, and initializes database schema via `init_db()`.
- **Key Functions**: `root()` returns system status JSON. Listens on `127.0.0.1:5000`.

### 2. `backend/app/config.py`
- **Responsibility**: System settings and security port invariants powered by `pydantic_settings`.
- **Key Functions**:
  - `validate_infrastructure_ports()`: Enforces AuthTwin API (`5000`) and Frontend (`5173`) ports stay within range `5000-5999`.
  - `get_control_plane_endpoints()`: Returns set of `(host, port)` tuples representing AuthTwin's control plane to prevent proxy loops and self-targeting.

### 3. `backend/app/database.py`
- **Responsibility**: SQLAlchemy engine setup, session management (`get_db`), and database initialization (`init_db`).
- **Key Functions**:
  - `get_active_target_model(db)`: **Single Source of Truth** for the currently configured target. Purges stale control-plane targets.
  - `seed_demo_data(db)`: Conditionally populates demo targets/identities ONLY if `AUTHTWIN_DEMO_MODE=true`.

### 4. `backend/app/ingestion/har_parser.py`
- **Responsibility**: Parses HAR 1.2 JSON files into normalized transaction dictionaries.
- **Key Functions**:
  - `parse_har_content(har_content)`: Iterates over `log.entries`, extracts method, URL, headers, postData body, response status, and response content. Redacts secret headers (`Authorization`, `Cookie`, `X-API-Key`) using `redact_headers()`.

### 5. `backend/app/identity/session_tracker.py`
- **Responsibility**: Groups transactions into a logical `Session` bound to an `Identity`.
- **Key Functions**:
  - `get_token_fingerprint(headers)`: Extracts `Authorization`, `Cookie`, or `X-API-Key` headers and generates a 16-character SHA-256 hex fingerprint (`hashlib.sha256(v).hexdigest()[:16]`). Plaintext tokens are NEVER stored.
  - `process_and_group_session(db, target_id, transactions_raw, explicit_identity_id)`: Creates a `Session` row and inserts `Transaction` rows with redacted headers.

### 6. `backend/app/openapi/loader.py`
- **Responsibility**: Ingests OpenAPI 3.x specifications (JSON/YAML) and matches raw URL paths to parameterized route templates.
- **Key Functions**:
  - `path_template_to_regex(template)`: Converts `/projects/{project_id}` into regex `^/projects/([^/]+)$`.
  - `match_path_template(actual_path, path_templates)`: Finds exact or regex template matches for an observed path.
  - `load_and_save_openapi(db, target_id, spec_content_str)`: Saves `OpenAPISpec` and `OpenAPIOperation` records, then calls `match_transactions_to_operations()`.

### 7. `backend/app/dependencies/analyzer.py`
- **Responsibility**: Discovers exact value producer-consumer parameter links between HTTP transactions.
- **Key Functions**:
  - `extract_primitive_values_from_json(data, prefix)`: Recursively extracts scalar strings/ints from JSON response payloads.
  - `find_value_in_consumer(consumer_tx, target_val)`: Checks if a produced value appears in a subsequent request's path, query string, JSON body, or header.
  - `analyze_session_dependencies(db, session_id)`: Chronologically scans session transactions, matches produced vs consumed values, applies confidence scoring (e.g. demotes coincidental pagination matches like `total=101` vs `page=101` to `0.2`), and persists `Dependency` records (for confidence >= 0.5).

### 8. `backend/app/workflows/wsg_generator.py`
- **Responsibility**: Builds Workflow State Graphs using NetworkX and persists nodes/edges to SQLite.
- **Key Functions**:
  - `infer_resource_info(tx)`: Derives resource types (`project`, `document`) and IDs from transaction paths.
  - `generate_workflow_state_graph(db, session_id)`: Instantiates a `nx.DiGraph()`, adds nodes for each transaction sequence index, inserts sequential transition edges (`SEQUENCE`), and adds multi-degree parameter dependency edges (`DEPENDENCY_TRANSITION`).

### 9. `backend/app/shadow/cloner.py`
- **Responsibility**: Duplicates a source workflow into a shadow workflow for an alternate identity under credential isolation.
- **Key Functions**:
  - `clone_shadow_workflow(db, source_workflow_id, shadow_identity_id)`: Creates a `ShadowWorkflow` record with `clone_policy="CREDENTIAL_ISOLATED"` and `status="MODEL_ONLY"`.

### 10. `backend/app/api/interceptor.py`
- **Responsibility**: Secret reverse proxy middleware, target scope validation, live buffer recording, iframe URL rewriting, and script injection.
- **Key Functions**:
  - `validate_target_scope(target_url)`: Rejects targets resolving to AuthTwin control plane IPs/ports, cloud metadata (`169.254.169.254`), or invalid schemes.
  - `secret_proxy_middleware(request, path, db)`: Reverse proxy handler. Enforces 10MB body limits, prevents proxy loops via `X-AuthTwin-Proxy: 1` header, rewrites HTML attributes, injects JS client-side fetch/XHR interceptor script, and records transactions to in-memory buffer when recording is active.

---

# PART F — Frontend File-by-File Analysis

### 1. `frontend/src/App.tsx`
- Root component with tab navigation (`overview`, `sandbox`, `traffic`, `identities`, `sessions`, `openapi`, `dependencies`, `workflows`, `shadow`) and live SOC terminal console logging state.

### 2. `frontend/src/components/GraphVisualizer.tsx`
- **Responsibility**: Interactive directed graph explorer. Uses Canvas 2D and SVG rendering to display `WorkflowNode` nodes and `WorkflowEdge` transitions. Color-codes nodes by HTTP method (GET=Blue, POST=Green, PUT=Amber, DELETE=Red) and edges by transition type (Solid Gray=Sequence, Curved Purple=Dependency). Provides interactive node selection with request/response detail drawers.

### 3. `frontend/src/pages/TargetSandbox.tsx`
- **Responsibility**: Live reverse-proxy testing sandbox. Allows operators to probe target URLs, toggle live recording (Start / Pause / Resume / Stop), render target web applications inside an isolated iframe routed through `/api/v1/interceptor/proxy/`, and view real-time live buffer capture counters.

### 4. `frontend/src/pages/Workflows.tsx`
- **Responsibility**: WSG explorer page. Displays persisted workflows, renders `GraphVisualizer`, and provides a one-click "Clone Shadow Workflow" trigger targeting registered alternate identities.

---

# PART G — Database and Data Models

AuthTwin uses SQLite (`authtwin.db`) via SQLAlchemy ORM defined in `backend/app/models/models.py`.

## Table Specifications (11 Tables)

| Table Name | Primary Key | Key Foreign Keys | Purpose |
|---|---|---|---|
| `targets` | `id` (String) | None | Registered target application URLs and scope rules |
| `identities` | `id` (String) | `target_id` | User identity profiles (`Primary` vs `Alternate`) |
| `sessions` | `id` (String) | `target_id`, `identity_id` | Logical transaction groups with SHA-256 token fingerprints |
| `transactions` | `id` (String) | `session_id` | Recorded HTTP request/response pairs (redacted headers) |
| `openapi_specs` | `id` (String) | `target_id` | Ingested OpenAPI 3.x spec metadata and JSON payload |
| `openapi_operations` | `id` (String) | `spec_id` | Parameterized endpoint route templates (`/projects/{id}`) |
| `dependencies` | `id` (String) | `producer_transaction_id`, `consumer_transaction_id` | Producer-consumer value links and confidence scores |
| `workflows` | `id` (String) | `session_id`, `identity_id` | Top-level Workflow State Graph metadata |
| `workflow_nodes` | `id` (String) | `workflow_id`, `transaction_id` | Graph nodes representing individual HTTP operations |
| `workflow_edges` | `id` (String) | `workflow_id`, `source_node_id`, `target_node_id`, `dependency_id` | Graph transitions (`SEQUENCE` vs `DEPENDENCY_TRANSITION`) |
| `shadow_workflows` | `id` (String) | `source_workflow_id`, `source_identity_id`, `shadow_identity_id` | Duplicated structural workflow model (`MODEL_ONLY`) |

---

# PART H — Traffic Interception

AuthTwin provides two ingestion pathways:

1. **HAR 1.2 File Upload (`/api/v1/import/har`)**: Parses browser-exported network logs, redacts credentials, creates sessions, runs dependency analysis, and generates WSG graphs.
2. **Live Reverse Proxy Middleware (`/api/v1/interceptor/proxy/{path}`)**:
   - Actively proxies target HTTP traffic.
   - Prevents self-targeting loops via host/port validation and `X-AuthTwin-Proxy: 1` header checks.
   - Automatically rewrites HTML element attributes (`src`, `href`, `action`) so iframe navigation stays inside the proxy.
   - Injects a client-side JavaScript patch script overriding `fetch`, `XMLHttpRequest`, and `history.pushState`.
   - Captures transactions into a live memory buffer, automatically redacting secret headers.

---

# PART I — Session and Identity Tracking

- **Identity Classification**: Identities are registered per target as `Primary` (source workflow creator) or `Alternate` (shadow workflow target).
- **Token Fingerprinting**: Plaintext tokens are NEVER persisted or logged. `get_token_fingerprint()` computes:
  $$\text{fingerprint} = \text{SHA256}(\text{header\_value})[0:16]$$
- **Header Redaction**: `redact_headers()` strips values for `Authorization`, `Cookie`, `Set-Cookie`, and `X-API-Key`, replacing them with `[REDACTED_BY_AUTHTWIN]`.

---

# PART J — OpenAPI Processing

1. Ingests OpenAPI specs via JSON or YAML strings at `/api/v1/import/openapi`.
2. Extracts path templates (e.g. `/api/v1/projects/{project_id}/documents/{doc_id}`).
3. Converts curly-brace templates into regular expressions:
   $$\text{Template: } \texttt{/projects/\{id\}} \longrightarrow \text{Regex: } \texttt{\^{}/projects/([\^{}/]+)\$}$$
4. Correlates observed transactions (`GET /projects/101`) to operation IDs (`get_projects_id`).

---

# PART K — Dependency Analysis

AuthTwin detects dynamic data propagation across HTTP steps using exact-value matching:

```text
Step 1: POST /projects  ───► Response Body JSON: {"id": "proj-9876", "status": "created"}
                                                   │
                                     Exact Match   │ Produced Value: "proj-9876"
                                                   ▼
Step 2: GET /projects/proj-9876 ──► Request Path: /projects/proj-9876
```

## Supported Dependency Types
1. `RESPONSE_TO_PATH`: Response field value consumed in request path segment.
2. `RESPONSE_TO_QUERY`: Response field value consumed in query parameter.
3. `RESPONSE_TO_BODY`: Response field value consumed in request JSON body field.
4. `RESPONSE_TO_HEADER`: Response field value consumed in request header.

## Noise Reduction Heuristics
- Ignores single-character values (`len < 2`).
- Filters out boolean keywords (`true`, `false`, `null`).
- Reduces confidence score to `0.2` for coincidental pagination field matches (e.g. response `total=10` matching query `limit=10`). Only dependencies with confidence >= 0.5 are saved.

---

# PART L — Workflow State Graph Generation

- Built using **NetworkX** (`nx.DiGraph`).
- **Nodes**: Represent individual HTTP operations in execution sequence order.
- **Edges**:
  - `SEQUENCE`: Connects step N to step N+1.
  - `DEPENDENCY_TRANSITION`: Connects step M to step N (where M < N) based on proven parameter dependencies.
- Persisted to database as `WorkflowNode` and `WorkflowEdge` rows, then served via JSON API to the React frontend.

---

# PART M — Current Dashboard Integration

The React dashboard (`frontend/src`) provides full visibility:
- **Target Sandbox**: Control live proxy recording, view active target reachability probes, and interact with the target inside an embedded iframe.
- **Workflows Screen**: Visualizes the WSG using `GraphVisualizer.tsx`. Operators can click nodes to view full request/response bodies, inspect dependency links, and trigger shadow workflow cloning.
- **Dependencies Screen**: Tabular breakdown of all discovered producer-consumer links.
- **Shadow Workflows Screen**: Lists cloned alternate identity workflow models and confirms their `MODEL_ONLY` credential-isolated status.

---

# PART N — Security Architecture

1. **Control vs. Target Plane Isolation**: AuthTwin runs on ports 5000 (API) and 5173 (UI). `validate_target_scope()` prevents AuthTwin from targeting its own ports or IP addresses.
2. **Proxy Recursion Guard**: Proxy requests carry `X-AuthTwin-Proxy: 1`. Re-entrant requests are immediately aborted.
3. **SSRF Prevention**: Cloud metadata addresses (`169.254.169.254`) and internal loopback addresses targeting control plane services are blocked.
4. **Credential Isolation Invariant**: Cloning a workflow to a shadow identity creates a model bound to the shadow identity. Source identity tokens are NEVER copied into the shadow workflow state.

---

# PART O — Testing

AuthTwin contains an automated Pytest suite in `backend/tests/`:
- `test_har_parser.py`: Verifies HAR ingestion and header redaction.
- `test_session_tracker.py`: Tests SHA-256 fingerprinting and session grouping.
- `test_openapi_loader.py`: Verifies path template matching.
- `test_dependency_analyzer.py`: Tests exact value matching across path, query, and body.
- `test_wsg_generator.py`: Verifies NetworkX graph construction and edge creation.
- `test_shadow_cloner.py`: Verifies credential isolation and `MODEL_ONLY` flag.
- `test_credential_isolation.py`: Confirms source secrets never leak to shadow models.
- `test_interceptor_security.py`: Tests SSRF protection and proxy loop prevention.
- `test_port_isolation.py`: Enforces port validation rules (5000-5999).
- `test_e2e_runtime_flow.py`: End-to-end integration test from HAR ingestion to WSG and shadow cloning.

---

# PART P — Configuration / Hardcoding / Mock Audit

| File | Item | Type | Purpose / Impact |
|---|---|---|---|
| `config.py` | `AUTHTWIN_API_PORT = 5000` | Configuration Default | Default backend API port |
| `config.py` | `AUTHTWIN_FRONTEND_PORT = 5173` | Configuration Default | Default frontend UI port |
| `config.py` | `MAX_BODY_BYTES = 10MB` | Security Constant | Prevents RAM exhaustion during proxying |
| `database.py` | `seed_demo_data()` | Demo Helper | Populates demo data ONLY if `AUTHTWIN_DEMO_MODE=true` |
| `cloner.py` | `status = "MODEL_ONLY"` | Invariant | Explicitly marks Milestone 1 shadow workflows as non-executing |

---

# PART Q — Source-of-Truth Audit

- **Active Target Configuration**: Database `Target` model (`get_active_target_model()`) is the sole canonical source of truth. In-memory components read from the database.
- **Workflow State**: SQLite database (`workflows`, `workflow_nodes`, `workflow_edges`) is canonical. NetworkX graphs are generated transiently in memory to populate database rows.
- **Frontend State**: Frontend queries backend endpoints via Axios (`client.ts`) and stores display state locally. Backend SQLite database is always the canonical authority.

---

# PART R — Thesis-to-Code Consistency

| Thesis Claim | Repository Implementation | Status |
|---|---|---|
| Workflow Reconstruction via WSG | NetworkX DiGraph builder & SQLite node/edge tables | **MATCH** |
| Exact Parameter Dependency Tracking | `analyzer.py` matching path, query, body, header | **MATCH** |
| OpenAPI Template Resolution | `loader.py` regex template parser (`/projects/{id}`) | **MATCH** |
| Shadow Identity Model Duplication | `cloner.py` creating `ShadowWorkflow` | **MATCH** |
| Credential Isolation Invariant | `redact_headers()` & SHA-256 token hashing | **MATCH** |
| Automated Request Replay & BOLA Detection | Deferred to Milestone 2 | **PLANNED (M2)** |

---

# PART S — Actual Completion Percentage

| Subsystem | Milestone Status | Estimated Completion |
|---|---|---:|
| Target & Scope Management | **COMPLETE** | 100% |
| Traffic Ingestion & Proxy Interception | **COMPLETE** | 100% |
| Session & Identity Tracking | **COMPLETE** | 100% |
| OpenAPI Specification Loading | **COMPLETE** | 100% |
| Parameter Dependency Analyzer | **COMPLETE** | 100% |
| Workflow State Graph Generator | **COMPLETE** | 100% |
| Shadow Workflow Model Cloner | **COMPLETE** | 100% |
| Controlled Replay Engine | **DEFERRED** | 0% (Milestone 2) |
| Response Authorization Comparator | **DEFERRED** | 0% (Milestone 2) |
| Violation Detection Engine | **DEFERRED** | 0% (Milestone 2) |
| Evidence & Report Exporter | **DEFERRED** | 0% (Milestone 2) |
| Workstation UI Dashboard | **COMPLETE (M1)** | 100% |

**Overall Project Engineering Progress**: **50% (Milestone 1 Foundation Complete)**

---

# PART T — Remaining 50% Roadmap

```text
[Milestone 1 Baseline WSG Model]
               │
               ▼
   [Phase 1: Shadow Session Binding] ──► Bind active session tokens for Alternate Identity
               │
               ▼
   [Phase 2: Differential Replay]   ──► Replay WSG nodes substituting Alternate Identity tokens
               │                        & parameter map derived from Dependency Graph
               │
               ▼
   [Phase 3: Auth Comparator]       ──► Calculate status code, body length, & structural JSON deltas
               │
               ▼
   [Phase 4: Violation Engine]       ──► Classify BOLA (200 OK on unauthorized resource),
               │                        BFLA (privileged endpoint accessible), etc.
               ▼
   [Phase 5: Evidence & Reporting]  ──► Export cryptographically signed PDF/HTML reports
```

---

# PART U — Live Demonstration Procedure

1. **Launch System**:
   ```bash
   # Terminal 1: Backend API
   cd backend && python -m app.main
   # Terminal 2: Frontend Dashboard
   cd frontend && npm run dev
   # Terminal 3: Target Application
   cd target/reference-api && python app.py
   ```
2. **Open Dashboard**: Navigate browser to `http://127.0.0.1:5173`.
3. **Configure Target**: Go to **Sandbox**, enter `http://127.0.0.1:8090`, and click **Verify & Save Target**.
4. **Capture Traffic**: Click **Start Recording**, perform actions inside the embedded iframe target (Login -> Create Project -> Create Document), then click **Stop Recording & Generate Workflow**.
5. **Inspect WSG Graph**: Navigate to **Workflows**, click on the generated workflow graph, and explore nodes/edges in `GraphVisualizer`. Show parameter dependencies in **Dependencies** tab.
6. **Clone Shadow Model**: Click **Clone Shadow Workflow** for Bob (Alternate Identity). Navigate to **Shadow Workflows** to demonstrate credential-isolated `MODEL_ONLY` state.

---

# PART V — 30-Second Explanation

> "AuthTwin is a workflow-aware authorization testing framework for REST APIs. Unlike traditional scanners that test endpoints in isolation, AuthTwin reconstructs complete application user workflows into a Workflow State Graph from HTTP traffic, identifies dynamic parameter dependencies, and clones structural workflow models for shadow identities under strict credential isolation. Today we demonstrate Milestone 1: complete workflow reconstruction and shadow graph generation."

---

# PART W — 2-Minute Explanation

> "Modern web applications rely on multi-step stateful workflows where resource IDs produced in early requests are consumed in later requests. Standard security scanners fail to detect authorization bugs like BOLA because they replay requests out of context without valid state dependencies.
> 
> AuthTwin solves this using the Deterministic Workflow-Aware Shadow-Session Architecture. In Milestone 1, AuthTwin intercepts live target traffic or ingests HAR files, maps routes to OpenAPI specifications, hashes authentication credentials for privacy, and automatically extracts exact producer-consumer parameter dependencies across response bodies and request paths. It then uses NetworkX to construct a directed Workflow State Graph. Finally, it clones this graph to an alternate identity as a structural shadow workflow model. In Milestone 2, this shadow graph will drive automated differential replay to uncover BOLA and IDOR vulnerabilities."

---

# PART X — 5-Minute Technical Explanation

> "AuthTwin's technical pipeline operates across four main engineering phases in Milestone 1:
> 
> **First: Ingestion and Scope Control.** Traffic enters via our Python reverse proxy middleware (`/api/v1/interceptor/proxy`) or HAR importer. Our scope validator enforces self-targeting protections by resolving hosts against AuthTwin's control plane endpoints (Ports 5000 and 5173) and checking loop headers (`X-AuthTwin-Proxy: 1`).
> 
> **Second: Session and OpenAPI Normalization.** The `SessionTracker` extracts authentication tokens from raw headers, computes a non-reversible SHA-256 fingerprint (`hashlib.sha256(token)[:16]`), and redacts plaintext credentials before database persistence. The `OpenAPILoader` converts OpenAPI route templates like `/projects/{id}` into regex patterns to match observed endpoints.
> 
> **Third: Dependency Analysis.** The `DependencyAnalyzer` recursively parses JSON response payloads to extract primitive scalar values. It scans chronologically subsequent requests to locate these values in path segments, query parameters, request bodies, or headers. It applies noise reduction heuristics—filtering out booleans and demoting coincidental pagination matches—to persist verified producer-consumer links.
> 
> **Fourth: WSG Generation and Shadow Duplication.** The `WSGGenerator` uses NetworkX to build a directed graph where nodes represent HTTP operations and edges represent sequential or parameter-dependent transitions. This graph is persisted to SQLite and rendered interactively on our React/TypeScript dashboard using HTML5 Canvas. Finally, the `ShadowCloner` duplicates the workflow structure to an alternate identity, stripping source credentials and assigning status `MODEL_ONLY` to maintain a strict security boundary prior to Milestone 2 replay."

---

# PART Y — Viva Questions and Answers

### Q1: Why is workflow awareness necessary for authorization testing?
**Answer**: Single-request security scanners cannot test stateful authorization boundaries because accessing protected sub-resources (e.g. `/projects/101/documents/202`) requires valid state, session context, and dynamic parameter propagation established in prior workflow steps.

### Q2: How does AuthTwin prevent credential leakage when cloning workflows?
**Answer**: AuthTwin enforces the **Credential Isolation Invariant**. Source identity tokens are hashed into SHA-256 fingerprints for session identification, and plaintext headers are redacted before storage. Shadow workflows bind strictly to the alternate identity's own credentials.

### Q3: Why does Milestone 1 mark shadow workflows as `MODEL_ONLY`?
**Answer**: To maintain a strict security boundary. Milestone 1 focuses on deterministic workflow reconstruction and data modeling. Active request replay against live target servers is reserved for Milestone 2 to prevent unsanctioned state mutation during initial model validation.

### Q4: How are false positive dependency links avoided?
**Answer**: The `DependencyAnalyzer` filters out single-character strings, boolean keywords (`true`, `false`), and applies a confidence penalty (scoring down to `0.2`) when response metadata (like `total=10`) matches request pagination parameters (like `page=10`). Only dependencies with confidence >= 0.5 are retained.

### Q5: How does AuthTwin prevent infinite proxy recursion if configured to target itself?
**Answer**: `validate_target_scope()` inspects candidate target hostnames and ports against `settings.get_control_plane_endpoints()`. In addition, proxied HTTP requests carry an `X-AuthTwin-Proxy: 1` header, and response HTML is inspected for AuthTwin's UI signature, immediately aborting self-referential loops.

---

# PART Z — Code Study Curriculum

- **Day 1: Architecture & Data Invariants** — Study `ARCHITECTURE.md`, `DECISIONS.md`, `DO_NOT_INVENT.md`.
- **Day 2: Database Models & Config** — Study `backend/app/models/models.py`, `backend/app/config.py`, `backend/app/database.py`.
- **Day 3: Ingestion & Session Tracking** — Study `backend/app/ingestion/har_parser.py`, `backend/app/identity/session_tracker.py`.
- **Day 4: OpenAPI Processing** — Study `backend/app/openapi/loader.py`.
- **Day 5: Dependency Analysis** — Study `backend/app/dependencies/analyzer.py`.
- **Day 6: Workflow State Graph Generation** — Study `backend/app/workflows/wsg_generator.py`.
- **Day 7: Shadow Workflow Cloning** — Study `backend/app/shadow/cloner.py`.
- **Day 8: Live Interceptor & Security Scope** — Study `backend/app/api/interceptor.py`.
- **Day 9: REST API Layer** — Study `backend/app/api/targets.py`, `workflows.py`, `sessions.py`, `imports.py`.
- **Day 10: Pytest Test Suite** — Run and study all test cases in `backend/tests/`.
- **Day 11: Frontend API Integration** — Study `frontend/src/api/client.ts`, `frontend/src/types/index.ts`.
- **Day 12: Frontend Interactive Graph Renderer** — Study `frontend/src/components/GraphVisualizer.tsx`.
- **Day 13: Live Sandbox Workspace** — Study `frontend/src/pages/TargetSandbox.tsx`, `Workflows.tsx`.
- **Day 14: Viva & Presentation Rehearsal** — Practice Parts U, V, W, X, and Y out loud.
