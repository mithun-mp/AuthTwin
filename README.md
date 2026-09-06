# AuthTwin: A Workflow-Aware IDOR and BOLA Testing Framework

> **Thesis / Research Project**: Black-box, workflow-aware authorization testing framework for web applications and REST APIs.

## Milestone 1 Scope: Workflow Reconstruction & Shadow Workflow Model Duplication

AuthTwin constructs a **Workflow State Graph (WSG)** from observed authenticated HTTP traffic, tracks producer-consumer parameter dependencies, maps API endpoints against OpenAPI specifications, and duplicates workflow models into **Shadow Workflows** bound to alternate registered identities under strict credential isolation.

> **IMPORTANT**: Milestone 1 implements **MODEL-ONLY construction**. Shadow workflows represent structural models for alternate identities. No differential request replay or live target vulnerability testing is executed in this milestone.

---

## Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**

### 1. Install & Setup Backend
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m app.main
```
Backend runs on `http://127.0.0.1:5000`. API docs available at `http://127.0.0.1:5000/docs`.


### 2. Run Backend Pytest Suite
```bash
cd backend
pytest -v
```

### 3. Install & Setup Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend dashboard runs on `http://127.0.0.1:5173`.

### 4. Run Reference API (Optional Test Target)
```bash
cd target/reference-api
python app.py
```
Reference target API runs on `http://127.0.0.1:8090`.

---

## High-Level Architecture (M1)

```text
HTTP Traffic / HAR File
         │
         ▼
 ┌───────────────┐
 │ HAR Ingestion │ ──► Normalized Transactions
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │Session Tracker│ ──► Identity & Session Association (Redacted Credentials)
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │OpenAPI Loader │ ──► Operation Mapping & Endpoint Templates
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │  Dependency   │ ──► Producer-Consumer Parameter Links (exact value matching)
 │   Analyzer    │
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Workflow State│ ──► Directed Graph (WSG) Nodes & Edges
 │Graph Generator│
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │Shadow Workflow│ ──► Model Clone for Alternate Identity
 │    Cloner     │     (STRICT CREDENTIAL ISOLATION - MODEL ONLY)
 └───────────────┘
```

---

## Key Security Invariants

1. **Credential Isolation**: Cloning a workflow to a shadow identity explicitly strips all authentication secrets (Authorization headers, session cookies, secret tokens) of the source identity.
2. **Model-Only Boundary**: Milestone 1 creates model clones only. It does not send replayed requests to the target or declare security verdicts.

---

## Documentation Index
- [`ARCHITECTURE.md`](file:///c:/Dev/Projects/AuthTwin2/ARCHITECTURE.md) - Deep architectural specification & pipeline description.
- [`IMPLEMENTATION_STATUS.md`](file:///c:/Dev/Projects/AuthTwin2/IMPLEMENTATION_STATUS.md) - Exact implementation status of all 14 thesis modules.
- [`DECISIONS.md`](file:///c:/Dev/Projects/AuthTwin2/DECISIONS.md) - Architectural decision record (ADR).
- [`DO_NOT_INVENT.md`](file:///c:/Dev/Projects/AuthTwin2/DO_NOT_INVENT.md) - Non-negotiable scope boundaries and assumptions.
