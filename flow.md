# AuthTwin — Interactive Clickable End-to-End Architectural Execution Flow

> **File Purpose**: Complete, clickable step-by-step execution path mapping the entire AuthTwin lifecycle from workstation launch to 2D/3D visualization and shadow replay.  
> **Clickable Scheme**: Click any blue file link `[filename](file:///c:/Dev/Projects/AuthTwin2/...)` to navigate directly to the exact file location and function definition.

---

## 1. Complete Step-by-Step Architectural Flow Diagram

```text
[STEP 1: LAUNCH WORKSTATION]
  │ (start-dev.ps1 → scripts/start_dev.py → backend/app/main.py)
  ▼
[STEP 2: REGISTER IDENTITY]
  │ (TargetSandbox.tsx → client.ts → identities.py → identity_service.py)
  ▼
[STEP 3: TARGET PROBE & VERIFY SERVER]
  │ (TargetSandbox.tsx → interceptor.py verify_target_server → validate_target_scope)
  ▼
[STEP 4: SAVE ACTIVE TARGET CONFIG]
  │ (TargetSandbox.tsx → interceptor.py save_and_set_active_target → database.py)
  ▼
[STEP 5: START REPLAY SESSION & LIVE INTERCEPTOR PROXY]
  │ (TargetSandbox.tsx → interceptor.py secret_proxy_middleware → validate_transaction_target)
  ▼
[STEP 6: INTERCEPT & REDACT LIVE TRAFFIC BUFFER]
  │ (interceptor.py → logging.py redact_headers → Target application HTTP response)
  ▼
[STEP 7: STOP RECORDING & INGEST SESSION]
  │ (TargetSandbox.tsx → interceptor.py stop_live_recording → capture_live_session)
  ▼
[STEP 8: SESSION GROUPING & TOKEN FINGERPRINTING]
  │ (session_tracker.py process_and_group_session → loader.py match_transactions_to_operations)
  ▼
[STEP 9: DYNAMIC PARAMETER DEPENDENCY ANALYSIS]
  │ (analyzer.py analyze_session_dependencies → dependency_service.py)
  ▼
[STEP 10: BUILD DUAL REPRESENTATION WORKFLOW & CANONICAL GRAPH]
  │ (wsg_generator.py → workflow_service.py build_canonical_graph & build_linear_workflow)
  ▼
[STEP 11: DELIVER GRAPH PAYLOAD OVER REST API]
  │ (workflows.py get_workflow_graph → workflow_service.py get_workflow_graph_details)
  ▼
[STEP 12: ADAPT GRAPH CONTRACT ON FRONTEND]
  │ (client.ts getWorkflowGraph → adapter.ts adaptWorkflowResponseToCanonicalGraph)
  ▼
[STEP 13: VISUALIZE 2D INTERACTIVE BEZIER FLOWCHART]
  │ (GraphVisualizer.tsx → Renderer2D.tsx → SVG Cubic Bezier curves & click listeners)
  ▼
[STEP 14: VISUALIZE 3D CYBERNETIC SPATIAL CANVAS]
  │ (GraphVisualizer.tsx → Renderer3D.tsx → Canvas perspective matrix & light pulses)
  ▼
[STEP 15: EDGE EVIDENCE INSPECTION & REPLAY STEP SYNC]
  │ (NodeInspector.tsx → GraphVisualizer.tsx handleSelectEdge & handleJumpToLinearStep)
  ▼
[STEP 16: CLONE SHADOW WORKFLOW & DIFFERENTIAL REPLAY]
  │ (ShadowWorkflows.tsx → shadow.py → shadow_service.py clone_shadow_workflow)
```

---

## 2. Clickable Step-by-Step Function & File Reference

### STEP 1: Launch Software & Initialize Workstation
- **PowerShell Launcher Script**: [`start-dev.ps1:L1-L3`](file:///c:/Dev/Projects/AuthTwin2/start-dev.ps1#L1-L3)
- **Python Automation Orchestrator**: [`scripts/start_dev.py:L43-L140`](file:///c:/Dev/Projects/AuthTwin2/scripts/start_dev.py#L43-L140)
  - `clean_cache()`: [`scripts/start_dev.py:L8-L42`](file:///c:/Dev/Projects/AuthTwin2/scripts/start_dev.py#L8-L42)
  - `main()`: [`scripts/start_dev.py:L43-L140`](file:///c:/Dev/Projects/AuthTwin2/scripts/start_dev.py#L43-L140)
- **Backend FastAPI Entry Point**: [`backend/app/main.py:L1-L60`](file:///c:/Dev/Projects/AuthTwin2/backend/app/main.py#L1-L60)
  - `root()`: [`backend/app/main.py:L43-L50`](file:///c:/Dev/Projects/AuthTwin2/backend/app/main.py#L43-L50)
- **Infrastructure Core Configuration**: [`backend/app/core/config.py:L7-L58`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/config.py#L7-L58)
  - `validate_infrastructure_ports()`: [`backend/app/core/config.py:L24-L32`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/config.py#L24-L32)
  - `get_control_plane_endpoints()`: [`backend/app/core/config.py:L34-L56`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/config.py#L34-L56)
- **Database Initialization & Seeder**: [`backend/app/core/database.py:L18-L114`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L18-L114)
  - `init_db()`: [`backend/app/core/database.py:L108-L113`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L108-L113)
  - `seed_demo_data()`: [`backend/app/core/database.py:L56-L106`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L56-L106)
  - `get_active_target_model()`: [`backend/app/core/database.py:L26-L54`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L26-L54)
- **Reference Target Test Application**: [`target/reference-api/app.py:L1-L200`](file:///c:/Dev/Projects/AuthTwin2/target/reference-api/app.py#L1-L200)
  - `index()`: [`target/reference-api/app.py:L28-L132`](file:///c:/Dev/Projects/AuthTwin2/target/reference-api/app.py#L28-L132)
  - `login()`: [`target/reference-api/app.py:L146-L154`](file:///c:/Dev/Projects/AuthTwin2/target/reference-api/app.py#L146-L154)
  - `create_project()`: [`target/reference-api/app.py:L159-L168`](file:///c:/Dev/Projects/AuthTwin2/target/reference-api/app.py#L159-L168)
- **Frontend App Launchers**: [`frontend/src/main.tsx:L1-L10`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/main.tsx#L1-L10) & [`frontend/src/App.tsx:L1-L80`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/App.tsx#L1-L80)

---

### STEP 2: Register Database User Identity
- **UI Button Action**: [`TargetSandbox.tsx:L267-L284`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L267-L284) (`handleQuickCreateIdentity()`)
- **API Client Function**: [`frontend/src/api/client.ts:L40-L45`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L40-L45) (`createIdentity()`)
- **REST API Handler**: [`backend/app/api/identities.py:L16-L28`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/identities.py#L16-L28) (`create_identity()`)
- **Service Layer**: [`backend/app/services/identity_service.py:L10-L30`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/identity_service.py#L10-L30) (`create_identity_service()`)
- **SQLAlchemy Model**: [`backend/app/models/models.py:L25-L35`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L25-L35) (`Identity`)

---

### STEP 3: Probe & Verify Target Application Address
- **UI Button Action**: [`TargetSandbox.tsx:L124-L154`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L124-L154) (`handleVerify()`)
- **API Client Function**: [`frontend/src/api/client.ts:L10-L15`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L10-L15) (`verifyTargetServer()`)
- **REST API Handler**: [`backend/app/api/interceptor.py:L187-L228`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L187-L228) (`verify_target_server()`)
- **Target Scope Bounds Validator**: [`backend/app/api/interceptor.py:L76-L130`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L76-L130) (`validate_target_scope()`)

---

### STEP 4: Save & Configure Active Project Target
- **UI Button Action**: [`TargetSandbox.tsx:L98-L122`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L98-L122) (`handleSaveTarget()`)
- **API Client Function**: [`frontend/src/api/client.ts:L16-L20`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L16-L20) (`setActiveTarget()`)
- **REST API Handler**: [`backend/app/api/interceptor.py:L230-L260`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L230-L260) (`save_and_set_active_target()`)
- **Single Source of Truth Lookup**: [`backend/app/core/database.py:L26-L54`](file:///c:/Dev/Projects/AuthTwin2/backend/app/core/database.py#L26-L54) (`get_active_target_model()`)
- **SQLAlchemy Model**: [`backend/app/models/models.py:L10-L24`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L10-L24) (`Target`)

---

### STEP 5: Start Live Interceptor Proxy Session
- **UI Button Action**: [`TargetSandbox.tsx:L156-L174`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L156-L174) (`startRecordingSession()`)
- **API Client Function**: [`frontend/src/api/client.ts:L100-L105`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L100-L105) (`startLiveRecording()`)
- **REST API Handler**: [`backend/app/api/interceptor.py:L280-L310`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L280-L310) (`start_live_recording()`)
- **Reverse Proxy Middleware**: [`backend/app/api/interceptor.py:L496-L766`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L496-L766) (`secret_proxy_middleware()`)
- **HTML URL Attribute Rewriter**: [`backend/app/api/interceptor.py:L46-L73`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L46-L73) (`rewrite_html_target_urls()`)
- **Transaction URL Resolver**: [`backend/app/api/interceptor.py:L147-L184`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L147-L184) (`validate_transaction_target()`)
- **Header Secret Redactor**: [`backend/app/logging.py:L1-L20`](file:///c:/Dev/Projects/AuthTwin2/backend/app/logging.py#L1-L20) (`redact_headers()`)

---

### STEP 6: Stop Recording & Process Captured Session
- **UI Button Action**: [`TargetSandbox.tsx:L231-L265`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/TargetSandbox.tsx#L231-L265) (`stopAndBuildGraph()`)
- **API Client Function**: [`frontend/src/api/client.ts:L130-L135`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L130-L135) (`stopLiveRecording()`)
- **REST API Handler**: [`backend/app/api/interceptor.py:L380-L407`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L380-L407) (`stop_live_recording()`)
- **Capture Session Ingestion Handler**: [`backend/app/api/interceptor.py:L409-L494`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/interceptor.py#L409-L494) (`capture_live_session()`)

---

### STEP 7: Session Grouping & Token Fingerprinting
- **Session Tracker Logic**: [`backend/app/identity/session_tracker.py:L10-L60`](file:///c:/Dev/Projects/AuthTwin2/backend/app/identity/session_tracker.py#L10-L60) (`process_and_group_session()`)
- **Token Fingerprinter**: [`backend/app/identity/session_tracker.py:L62-L80`](file:///c:/Dev/Projects/AuthTwin2/backend/app/identity/session_tracker.py#L62-L80) (`extract_token_fingerprint()`)
- **OpenAPI Route Matcher**: [`backend/app/openapi/loader.py:L10-L50`](file:///c:/Dev/Projects/AuthTwin2/backend/app/openapi/loader.py#L10-L50) (`match_transactions_to_operations()`)
- **SQLAlchemy Models**: [`backend/app/models/models.py:L37-L70`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L37-L70) (`Session`, `Transaction`)

---

### STEP 8: Dynamic Parameter Dependency Analysis
- **Dependency Analyzer Engine**: [`backend/app/dependencies/analyzer.py:L10-L100`](file:///c:/Dev/Projects/AuthTwin2/backend/app/dependencies/analyzer.py#L10-L100) (`analyze_session_dependencies()`)
- **Dependency Service Wrapper**: [`backend/app/services/dependency_service.py:L10-L90`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/dependency_service.py#L10-L90) (`analyze_session_dependencies()`)
- **SQLAlchemy Model**: [`backend/app/models/models.py:L90-L110`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L90-L110) (`Dependency`)

---

### STEP 9: Generate Workflow State Graph (WSG) & Dual Representation
- **WSG Generator Submodule**: [`backend/app/workflows/wsg_generator.py:L1-L30`](file:///c:/Dev/Projects/AuthTwin2/backend/app/workflows/wsg_generator.py#L1-L30) (`generate_workflow_state_graph()`)
- **Workflow Service Generator**: [`backend/app/services/workflow_service.py:L396-L450`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L396-L450) (`generate_workflow_state_graph()`)
- **Canonical Graph Builder**: [`backend/app/services/workflow_service.py:L131-L394`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L131-L394) (`build_canonical_graph()`)
- **Linear Workflow Builder**: [`backend/app/services/workflow_service.py:L80-L130`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L80-L130) (`build_linear_workflow()`)
- **SHA-256 Deterministic Hashing**: [`backend/app/services/workflow_service.py:L55-L75`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L55-L75) (`hash_deterministic_id()`)
- **Graph Integrity Validator**: [`backend/app/services/workflow_service.py:L77-L79`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L77-L79) (`validate_canonical_graph()`)
- **SQLAlchemy Models**: [`backend/app/models/models.py:L112-L160`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L112-L160) (`Workflow`, `WorkflowNode`, `WorkflowEdge`)

---

### STEP 10: Deliver Graph Payload Over REST API
- **REST API Handler**: [`backend/app/api/workflows.py:L35-L55`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/workflows.py#L35-L55) (`get_workflow_graph()`)
- **Service Handler**: [`backend/app/services/workflow_service.py:L480-L524`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/workflow_service.py#L480-L524) (`get_workflow_graph_details()`)
- **Pydantic Response Schema**: [`backend/app/schemas/schemas.py:L265-L280`](file:///c:/Dev/Projects/AuthTwin2/backend/app/schemas/schemas.py#L265-L280) (`WorkflowGraphResponse`)

---

### STEP 11: Receive & Adapt Graph Contract in Frontend
- **API Client Function**: [`frontend/src/api/client.ts:L80-L85`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L80-L85) (`getWorkflowGraph()`)
- **Visual Data Adapter**: [`frontend/src/graph/adapter.ts:L1-L30`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/adapter.ts#L1-L30) (`adaptWorkflowResponseToCanonicalGraph()`)
- **TypeScript Interfaces**: [`frontend/src/types/index.ts:L106-L177`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/types/index.ts#L106-L177) (`CanonicalNode`, `CanonicalEdge`, `DependencyBinding`, `EdgeEvidence`, `CanonicalGraph`)

---

### STEP 12: Visualize 2D Interactive Bezier Flowchart
- **Master Graph Container**: [`frontend/src/components/GraphVisualizer.tsx:L16-L280`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/GraphVisualizer.tsx#L16-L280) (`GraphVisualizer`)
- **2D Flowchart Visualizer**: [`frontend/src/graph/Renderer2D.tsx:L22-L370`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L22-L370) (`Renderer2D`)
- **Topological Layout Algorithm**: [`frontend/src/graph/Renderer2D.tsx:L48-L83`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L48-L83) (`useEffect`)
- **Canvas Drag & Pan Handlers**: [`frontend/src/graph/Renderer2D.tsx:L96-L138`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L96-L138) (`handleCanvasMouseDown()`, `handleMouseMove()`, `handleMouseUp()`)
- **Node Drag Handler**: [`frontend/src/graph/Renderer2D.tsx:L102-L107`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L102-L107) (`handleNodeMouseDown()`)
- **Edge Selection Click Listener**: [`frontend/src/graph/Renderer2D.tsx:L237-L255`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer2D.tsx#L237-L255) (`onClick={() => onSelectEdge?.(edge)}`)

---

### STEP 13: Visualize 3D Cybernetic Spatial Canvas
- **3D Canvas Renderer**: [`frontend/src/graph/Renderer3D.tsx:L16-L349`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer3D.tsx#L16-L349) (`Renderer3D`)
- **3D Spatial Projection Loop**: [`frontend/src/graph/Renderer3D.tsx:L50-L215`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer3D.tsx#L50-L215) (`render3D()`)
- **3D Node & Edge Picking**: [`frontend/src/graph/Renderer3D.tsx:L218-L300`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer3D.tsx#L218-L300) (`handleMouseDown()`)
- **Camera Orbit Controls**: [`frontend/src/graph/Renderer3D.tsx:L262-L295`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/graph/Renderer3D.tsx#L262-L295) (`handleMouseMove()`, `handleWheel()`, `handleResetCamera()`)

---

### STEP 14: Inspect Edge Evidence & Synchronize Linear Replay Step
- **Slide-Out Inspector Drawer**: [`frontend/src/components/NodeInspector.tsx:L15-L327`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/NodeInspector.tsx#L15-L327) (`NodeInspector`)
- **Edge Selection State Handler**: [`frontend/src/components/GraphVisualizer.tsx:L52-L56`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/GraphVisualizer.tsx#L52-L56) (`handleSelectEdge()`)
- **Linear Step Jump Trigger**: [`frontend/src/components/GraphVisualizer.tsx:L58-L67`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/GraphVisualizer.tsx#L58-L67) (`handleJumpToLinearStep()`)
- **Linear Step Click Handler**: [`frontend/src/components/GraphVisualizer.tsx:L71-L79`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/components/GraphVisualizer.tsx#L71-L79) (`handleLinearStepClick()`)

---

### STEP 15: Create Shadow Workflow & Execute Differential Replay
- **Shadow Workflows Page**: [`frontend/src/pages/ShadowWorkflows.tsx:L1-L120`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/pages/ShadowWorkflows.tsx#L1-L120) (`ShadowWorkflows`)
- **API Client Function**: [`frontend/src/api/client.ts:L90-L95`](file:///c:/Dev/Projects/AuthTwin2/frontend/src/api/client.ts#L90-L95) (`createShadowWorkflow()`)
- **REST API Handler**: [`backend/app/api/shadow.py:L12-L25`](file:///c:/Dev/Projects/AuthTwin2/backend/app/api/shadow.py#L12-L25) (`create_shadow_workflow()`)
- **Shadow Service & Cloner**: [`backend/app/services/shadow_service.py:L1-L30`](file:///c:/Dev/Projects/AuthTwin2/backend/app/services/shadow_service.py#L1-L30) & [`backend/app/shadow/cloner.py:L1-L40`](file:///c:/Dev/Projects/AuthTwin2/backend/app/shadow/cloner.py#L1-L40) (`clone_shadow_workflow()`)
- **SQLAlchemy Model**: [`backend/app/models/models.py:L162-L180`](file:///c:/Dev/Projects/AuthTwin2/backend/app/models/models.py#L162-L180) (`ShadowWorkflow`)
