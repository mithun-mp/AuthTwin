# AuthTwin — Interactive Clickable End-to-End Architectural Execution Flow (`flowa.md`)

> **File Purpose**: Complete, clickable step-by-step execution path mapping the entire AuthTwin lifecycle from workstation launch, identity creation, target probe & validation, session capture, WSG generation, dynamic parameter analysis, to 2D flowchart & 3D cybernetic spatial visualization.  
> **Navigation**: Click any blue file link `[filename](file:///c:/Dev/Projects/AuthTwin2/...)` to navigate directly to the exact file location and function definition in your IDE.

---

## 1. End-to-End System Execution Flowchart

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. OPEN SOFTWARE & START WORKSTATION                                                   │
│    start-dev.ps1 ──► scripts/start_dev.py ──► backend/app/main.py (FastAPI on :5000)   │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. CREATE IDENTITY                                                                     │
│    TargetSandbox.tsx (handleQuickCreateIdentity) ──► client.ts (createIdentity)        │
│    ──► backend/app/api/identities.py (create_identity)                                 │
│    ──► backend/app/services/identity_service.py (create_identity)                      │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. TARGET PROBE                                                                        │
│    TargetSandbox.tsx (handleVerify) ──► client.ts (verifyTargetServer)                 │
│    ──► backend/app/api/interceptor.py (verify_target_server)                           │
│    ──► backend/app/api/interceptor.py (validate_target_scope)                          │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. VALIDATE & SAVE TARGET                                                              │
│    TargetSandbox.tsx (handleSaveTarget) ──► client.ts (setActiveTarget)                │
│    ──► backend/app/api/interceptor.py (save_and_set_active_target)                     │
│    ──► backend/app/services/target_service.py (set_active_target)                      │
│    ──► backend/app/core/database.py (get_active_target_model)                          │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. START SESSION CAPTURE                                                               │
│    TargetSandbox.tsx (startRecordingSession) ──► client.ts (startLiveRecording)        │
│    ──► backend/app/api/interceptor.py (start_live_recording)                           │
│    ──► secret_proxy_middleware ──► validate_transaction_target ──► redact_headers      │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 6. STOP SESSION CAPTURE                                                                │
│    TargetSandbox.tsx (stopAndBuildGraph) ──► client.ts (stopLiveRecording)             │
│    ──► backend/app/api/interceptor.py (stop_live_recording)                            │
│    ──► backend/app/api/interceptor.py (capture_live_session)                           │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 7. ANALYSE THE WSG & DEPENDENCIES                                                      │
│    session_tracker.py (process_and_group_session, extract_token_fingerprint)           │
│    ──► analyzer.py (analyze_session_dependencies)                                      │
│    ──► dependency_service.py (analyze_session_dependencies)                            │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 8. GENERATE WSG & DUAL GRAPH REPRESENTATION                                            │
│    wsg_generator.py (generate_workflow_state_graph)                                    │
│    ──► workflow_service.py (generate_workflow_state_graph, build_canonical_graph)      │
│    ──► workflow_service.py (build_linear_workflow, hash_deterministic_id)              │
│    ──► workflows.py (get_workflow_graph)                                               │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 9. VISUALIZE 2D FLOWCHART & 3D SPATIAL CANVAS                                          │
│    client.ts (getWorkflowGraph) ──► adapter.ts (adaptWorkflowResponseToCanonicalGraph) │
│    ──► GraphVisualizer.tsx ──► Renderer2D.tsx (2D SVG Curves & Edge Click Listeners)   │
│    ──► Renderer3D.tsx (3D Perspective Matrix & Proximity Picking)                      │
│    ──► NodeInspector.tsx (Canonical Node & Edge Evidence Drawer)                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Master Function & File Reference Matrix

| Step # | Pipeline Stage | Primary Function Name | File & Line Location | Description |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Open Software | `main()` | [`scripts/start_dev.py:L43-L140`](file:///c:/Dev/Projects/AuthTwin2/scripts/start_dev.py#L43-L140) | Workstation clean, rebuild, and startup launcher script. |
| **1** | Open Software | `root()` | [`backend/app/main.py:L43-L50`](file:///c:/Dev/Projects/AuthTwin2/backend/app/main.py#L43-L50) | FastAPI application entrypoint and health root handler. |
| **2** | Create Identity | `handleQuickCreateIdentity()` | [`TargetSandbox.tsx:L267-L284`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L267-L284) | UI button handler for instant user identity registration. |
| **2** | Create Identity | `create_identity()` | [`backend/app/api/identities.py:L18-L48`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/identities.py#L18-L48) | REST endpoint for storing User Identity (role, auth_type). |
| **2** | Create Identity | `create_identity()` | [`backend/app/services/identity_service.py:L14-L48`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/identity_service.py#L14-L48) | Service logic creating Identity bound to target application. |
| **3** | Target Probe | `handleVerify()` | [`TargetSandbox.tsx:L124-L154`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L124-L154) | UI button probing target URL health and reachability. |
| **3** | Target Probe | `verify_target_server()` | [`backend/app/api/interceptor.py:L187-L228`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L187-L228) | HTTP probe checking target responsiveness and CORS/headers. |
| **3** | Target Probe | `validate_target_scope()` | [`backend/app/api/interceptor.py:L76-L130`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L76-L130) | Security validator enforcing allowed target hosts (SSRF prevention). |
| **4** | Validate & Save Target | `handleSaveTarget()` | [`TargetSandbox.tsx:L98-L122`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L98-L122) | UI action committing tested target URL to system active state. |
| **4** | Validate & Save Target | `save_and_set_active_target()` | [`backend/app/api/interceptor.py:L230-L260`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L230-L260) | REST endpoint saving active target and updating proxy routing. |
| **4** | Validate & Save Target | `get_active_target_model()` | [`backend/app/core/database.py:L26-L54`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L26-L54) | Single source-of-truth lookup for currently active Target DB row. |
| **5** | Start Session Capture | `startRecordingSession()` | [`TargetSandbox.tsx:L156-L174`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L156-L174) | UI action launching live HTTP interception mode. |
| **5** | Start Session Capture | `start_live_recording()` | [`backend/app/api/interceptor.py:L280-L310`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L280-L310) | Initializes live buffer and creates active session record. |
| **5** | Start Session Capture | `secret_proxy_middleware()` | [`backend/app/api/interceptor.py:L496-L766`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L496-L766) | Intercepts HTTP traffic, redacts credentials, forwards to target. |
| **6** | Stop Session Capture | `stopAndBuildGraph()` | [`TargetSandbox.tsx:L231-L265`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L231-L265) | UI action ending capture session and requesting graph synthesis. |
| **6** | Stop Session Capture | `stop_live_recording()` | [`backend/app/api/interceptor.py:L380-L407`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L380-L407) | Flushes proxy buffer and stops active interception timer. |
| **6** | Stop Session Capture | `capture_live_session()` | [`backend/app/api/interceptor.py:L409-L494`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L409-L494) | Saves raw captured transactions into SQLite database. |
| **7** | Analyse WSG | `process_and_group_session()` | [`session_tracker.py:L10-L60`](file:///c:/Dev/Projects/AuthTwin2/backend/app/identity/session_tracker.py#L10-L60) | Groups transactions by user identity and auth token fingerprint. |
| **7** | Analyse WSG | `analyze_session_dependencies()` | [`analyzer.py:L10-L100`](file:///c:/Dev/Projects/AuthTwin2/backend/app/dependencies/analyzer.py#L10-L100) | Computes parameter dependencies between HTTP response and request. |
| **8** | Generate WSG | `generate_workflow_state_graph()` | [`wsg_generator.py:L1-L30`](file:///c:/Dev/Projects/AuthTwin2/backend/app/workflows/wsg_generator.py#L1-L30) | Entry handler generating state graph from session transactions. |
| **8** | Generate WSG | `build_canonical_graph()` | [`workflow_service.py:L131-L394`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L131-L394) | Constructs deduplicated state graph with edge evidence and bindings. |
| **8** | Generate WSG | `build_linear_workflow()` | [`workflow_service.py:L80-L130`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L80-L130) | Constructs sequential execution timeline for replay drawer. |
| **9** | Visualize (2D & 3D) | `GraphVisualizer` | [`GraphVisualizer.tsx:L16-L280`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/GraphVisualizer.tsx#L16-L280) | Master interactive graph container with view toggle (2D vs 3D). |
| **9** | Visualize (2D) | `Renderer2D` | [`Renderer2D.tsx:L22-L370`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L22-L370) | Interactive SVG flowchart renderer with Bezier curves & edge clicks. |
| **9** | Visualize (3D) | `Renderer3D` | [`Renderer3D.tsx:L16-L349`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer3D.tsx#L16-L349) | HTML5 Canvas 3D spatial visualizer with node/edge proximity picking. |

---

## 3. Comprehensive Step-by-Step Function & Code Locations

### STEP 1: Open Software & Initialize Workstation
- **PowerShell Workstation Script**: [`start-dev.ps1:L1-L3`](file:///c:/Dev/Projects/AuthTwin2/start-dev.ps1#L1-L3)
- **Python Automation Orchestrator**: [`scripts/start_dev.py:L43-L140`](file:///c:/Dev/Projects/AuthTwin2/scripts/start_dev.py#L43-L140)
  - `clean_cache()`: [`scripts/start_dev.py:L8-L42`](file:///c:/Dev/Projects/AuthTwin2/scripts/start_dev.py#L8-L42)
  - `main()`: [`scripts/start_dev.py:L43-L140`](file:///c:/Dev/Projects/AuthTwin2/scripts/start_dev.py#L43-L140)
- **Backend FastAPI Entry Point**: [`backend/app/main.py:L1-L60`](file:///c:/Dev/Projects/AuthTwin2/backend/app/main.py#L1-L60)
  - `root()`: [`backend/app/main.py:L43-L50`](file:///c:/Dev/Projects/AuthTwin2/backend/app/main.py#L43-L50)
- **Infrastructure Core Configuration**: [`backend/app/core/config.py:L7-L58`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/config.py#L7-L58)
  - `validate_infrastructure_ports()`: [`backend/app/core/config.py:L24-L32`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/config.py#L24-L32)
  - `get_control_plane_endpoints()`: [`backend/app/core/config.py:L34-L56`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/config.py#L34-L56)
- **Database Connection & Seeder**: [`backend/app/core/database.py:L18-L114`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L18-L114)
  - `init_db()`: [`backend/app/core/database.py:L108-L113`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L108-L113)
  - `seed_demo_data()`: [`backend/app/core/database.py:L56-L106`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L56-L106)
  - `get_active_target_model()`: [`backend/app/core/database.py:L26-L54`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L26-L54)
- **Target Reference API Server**: [`target/reference-api/app.py:L1-L200`](file:///c:/Dev/Projects/AuthTwin2/target/reference-api/app.py#L1-L200)
  - `index()`: [`target/reference-api/app.py:L28-L132`](file:///c:/Dev/Projects/AuthTwin2/target/reference-api/app.py#L28-L132)
  - `login()`: [`target/reference-api/app.py:L146-L154`](file:///c:/Dev/Projects/AuthTwin2/target/reference-api/app.py#L146-L154)
  - `create_project()`: [`target/reference-api/app.py:L159-L168`](file:///c:/Dev/Projects/AuthTwin2/target/reference-api/app.py#L159-L168)
- **Frontend Launchers**: [`frontend/src/main.tsx:L1-L10`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/main.tsx#L1-L10) & [`frontend/src/App.tsx:L1-L80`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/App.tsx#L1-L80)

---

### STEP 2: Create User Identity
- **UI Button Click**: [`TargetSandbox.tsx:L267-L284`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L267-L284) (`handleQuickCreateIdentity()`)
- **Frontend API Client**: [`frontend/src/api/client.ts:L40-L45`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L40-L45) (`createIdentity()`)
- **Backend API Router**: [`backend/app/api/identities.py:L18-L48`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/identities.py#L18-L48) (`create_identity()`)
- **Service Logic Layer**: [`backend/app/services/identity_service.py:L14-L48`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/identity_service.py#L14-L48) (`create_identity()`)
- **SQLAlchemy Identity Model**: [`backend/app/models/models.py:L25-L35`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L25-L35) (`Identity`)

---

### STEP 3: Probe Target Application Address
- **UI Verification Button**: [`TargetSandbox.tsx:L124-L154`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L124-L154) (`handleVerify()`)
- **Frontend API Client**: [`frontend/src/api/client.ts:L10-L15`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L10-L15) (`verifyTargetServer()`)
- **REST API Probe Endpoint**: [`backend/app/api/interceptor.py:L187-L228`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L187-L228) (`verify_target_server()`)
- **SSRF Target Scope Guard**: [`backend/app/api/interceptor.py:L76-L130`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L76-L130) (`validate_target_scope()`)

---

### STEP 4: Validate & Save Active Target Config
- **UI Save Button**: [`TargetSandbox.tsx:L98-L122`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L98-L122) (`handleSaveTarget()`)
- **Frontend API Client**: [`frontend/src/api/client.ts:L16-L20`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L16-L20) (`setActiveTarget()`)
- **REST API Save Endpoint**: [`backend/app/api/interceptor.py:L230-L260`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L230-L260) (`save_and_set_active_target()`)
- **Target Service Operations**: [`backend/app/services/target_service.py:L10-L60`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/target_service.py#L10-L60) (`set_active_target()`)
- **Active Target Database Resolution**: [`backend/app/core/database.py:L26-L54`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L26-L54) (`get_active_target_model()`)
- **SQLAlchemy Target Model**: [`backend/app/models/models.py:L10-L24`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L10-L24) (`Target`)

---

### STEP 5: Start Session Capture & Live Proxy Middleware
- **UI Start Capture Button**: [`TargetSandbox.tsx:L156-L174`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L156-L174) (`startRecordingSession()`)
- **Frontend API Client**: [`frontend/src/api/client.ts:L100-L105`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L100-L105) (`startLiveRecording()`)
- **REST Interceptor Start Endpoint**: [`backend/app/api/interceptor.py:L280-L310`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L280-L310) (`start_live_recording()`)
- **Live Proxy Middleware Engine**: [`backend/app/api/interceptor.py:L496-L766`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L496-L766) (`secret_proxy_middleware()`)
- **Transaction Path Normalizer**: [`backend/app/api/interceptor.py:L147-L184`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L147-L184) (`validate_transaction_target()`)
- **HTML Proxy Attribute Rewriter**: [`backend/app/api/interceptor.py:L46-L73`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L46-L73) (`rewrite_html_target_urls()`)
- **Credential & Token Redactor**: [`backend/app/logging.py:L1-L20`](file:///c:/Dev/Projects/AuthTwin2/backend/app/logging.py#L1-L20) (`redact_headers()`)

---

### STEP 6: Stop Session Capture
- **UI Stop & Build Button**: [`TargetSandbox.tsx:L231-L265`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L231-L265) (`stopAndBuildGraph()`)
- **Frontend API Client**: [`frontend/src/api/client.ts:L130-L135`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L130-L135) (`stopLiveRecording()`)
- **REST Interceptor Stop Endpoint**: [`backend/app/api/interceptor.py:L380-L407`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L380-L407) (`stop_live_recording()`)
- **Live Session Ingestion Handler**: [`backend/app/api/interceptor.py:L409-L494`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L409-L494) (`capture_live_session()`)

---

### STEP 7: Group Session & Dynamic Dependency Analysis
- **Session Tracking & Grouping Engine**: [`session_tracker.py:L10-L60`](file:///c:/Dev/Projects/AuthTwin2/backend/app/identity/session_tracker.py#L10-L60) (`process_and_group_session()`)
- **Auth Token Fingerprinter**: [`session_tracker.py:L62-L80`](file:///c:/Dev/Projects/AuthTwin2/backend/app/identity/session_tracker.py#L62-L80) (`extract_token_fingerprint()`)
- **OpenAPI Route Matcher Engine**: [`loader.py:L10-L50`](file:///c:/Dev/Projects/AuthTwin2/backend/app/openapi/loader.py#L10-L50) (`match_transactions_to_operations()`)
- **Parameter Dependency Analyzer Engine**: [`analyzer.py:L10-L100`](file:///c:/Dev/Projects/AuthTwin2/backend/app/dependencies/analyzer.py#L10-L100) (`analyze_session_dependencies()`)
- **Dependency Service Wrapper**: [`dependency_service.py:L10-L90`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/dependency_service.py#L10-L90) (`analyze_session_dependencies()`)
- **SQLAlchemy Models**: [`models.py:L37-L110`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L37-L110) (`Session`, `Transaction`, `Dependency`)

---

### STEP 8: Generate WSG & Dual Graph Representation (Canonical + Linear)
- **WSG Generator Submodule**: [`wsg_generator.py:L1-L30`](file:///c:/Dev/Projects/AuthTwin2/backend/app/workflows/wsg_generator.py#L1-L30) (`generate_workflow_state_graph()`)
- **Workflow Service Generator Entry**: [`workflow_service.py:L396-L450`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L396-L450) (`generate_workflow_state_graph()`)
- **Canonical Deduplicated Graph Builder**: [`workflow_service.py:L131-L394`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L131-L394) (`build_canonical_graph()`)
- **Linear Timeline Builder**: [`workflow_service.py:L80-L130`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L80-L130) (`build_linear_workflow()`)
- **Deterministic Hashing Engine**: [`workflow_service.py:L55-L75`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L55-L75) (`hash_deterministic_id()`)
- **REST Graph Delivery Endpoint**: [`workflows.py:L35-L55`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/workflows.py#L35-L55) (`get_workflow_graph()`)
- **Workflow Detail Fetcher**: [`workflow_service.py:L480-L524`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L480-L524) (`get_workflow_graph_details()`)
- **Pydantic Response Schemas**: [`schemas.py:L265-L280`](file:///c:/Dev/Projects/AuthTwin2/backend/app/schemas/schemas.py#L265-L280) (`WorkflowGraphResponse`, `CanonicalGraphSchema`)

---

### STEP 9: Visualize 2D Flowchart & 3D Cybernetic Spatial Canvas
- **Frontend REST Graph Client**: [`client.ts:L80-L85`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L80-L85) (`getWorkflowGraph()`)
- **Graph Response Visual Adapter**: [`adapter.ts:L1-L30`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/adapter.ts#L1-L30) (`adaptWorkflowResponseToCanonicalGraph()`)
- **TypeScript Type Contracts**: [`types/index.ts:L106-L177`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/types/index.ts#L106-L177) (`CanonicalNode`, `CanonicalEdge`, `EdgeEvidence`, `CanonicalGraph`)
- **Master Visualizer Component**: [`GraphVisualizer.tsx:L16-L280`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/GraphVisualizer.tsx#L16-L280) (`GraphVisualizer`)
- **2D SVG Flowchart Component**: [`Renderer2D.tsx:L22-L370`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L22-L370) (`Renderer2D`)
  - Topological Grid Layout: [`Renderer2D.tsx:L48-L83`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L48-L83) (`useEffect`)
  - Bezier Curve Drawing & Selection: [`Renderer2D.tsx:L237-L255`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L237-L255) (`onClick={() => onSelectEdge?.(edge)}`)
- **3D Spatial Canvas Component**: [`Renderer3D.tsx:L16-L349`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer3D.tsx#L16-L349) (`Renderer3D`)
  - Perspective Projection Loop: [`Renderer3D.tsx:L50-L215`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer3D.tsx#L50-L215) (`render3D()`)
  - Node & Edge Proximity Picking: [`Renderer3D.tsx:L218-L300`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer3D.tsx#L218-L300) (`handleMouseDown()`)
- **Slide-Out Evidence Inspector Drawer**: [`NodeInspector.tsx:L15-L327`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/NodeInspector.tsx#L15-L327) (`NodeInspector`)
  - Edge Payload Inspection: [`NodeInspector.tsx:L200-L290`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/NodeInspector.tsx#L200-L290)
  - Linear Jump & Replay Synchronization: [`GraphVisualizer.tsx:L58-L79`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/GraphVisualizer.tsx#L58-L79) (`handleJumpToLinearStep()`, `handleLinearStepClick()`)
