from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(
    title="AuthTwin Reference Target API",
    description="Local reference API for generating realistic multi-step user workflow traffic.",
    version="1.0.0"
)

# In-memory storage
projects_db = {}
documents_db = {}
project_id_counter = 101
doc_id_counter = 501

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateProjectRequest(BaseModel):
    name: str

class CreateDocumentRequest(BaseModel):
    title: str

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reference Target Web Application</title>
        <link rel="stylesheet" href="/target-style.css">
        <script src="/target-script.js"></script>
    </head>
    <body>
        <h2>Reference Target Application (TARGET_PLANE_OK)</h2>
        <p>This is the test software running on your local device. Perform user actions below to generate live HTTP/API traffic for AuthTwin capture.</p>
        <img src="/target-image.png" alt="Target Logo" style="display:none;" />
        <form action="/login" method="POST" style="display:none;"></form>
        
        <div class="card">
            <h3>1. Authentication (Login)</h3>
            <button onclick="login()">Login as Alice (Generate JWT Token)</button>
            <div id="auth-status" style="margin-top:10px; font-size: 13px; font-family: monospace; color: #38bdf8;">Status: Not authenticated</div>
        </div>

        <div class="card">
            <h3>2. Project Management</h3>
            <input type="text" id="proj-name" value="Project Alpha" />
            <button onclick="createProject()">Create Project (POST /projects)</button>
            <button onclick="getProject()">Get Project Details (GET /projects/101)</button>
        </div>

        <div class="card">
            <h3>3. Document Management</h3>
            <input type="text" id="doc-title" value="Architecture Document" />
            <button onclick="createDocument()">Create Document (POST /projects/101/documents)</button>
            <button onclick="getDocument()">Get Document Details (GET /documents/501)</button>
        </div>

        <div class="card">
            <h3>API Response Output Log</h3>
            <pre id="output-log">// Click buttons above to execute target API calls...</pre>
        </div>

        <script>
            let authToken = "";
            let currentProjectId = 101;
            let currentDocId = 501;

            function log(msg) {
                document.getElementById('output-log').innerText = typeof msg === 'object' ? JSON.stringify(msg, null, 2) : msg;
            }

            async function login() {
                const res = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: 'alice', password: 'password123' })
                });
                const data = await res.json();
                authToken = data.token;
                document.getElementById('auth-status').innerText = "Authenticated as Alice | Token: " + authToken;
                log(data);
            }

            async function createProject() {
                const name = document.getElementById('proj-name').value;
                const res = await fetch('/projects', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                    body: JSON.stringify({ name: name })
                });
                const data = await res.json();
                if(data.id) currentProjectId = data.id;
                log(data);
            }

            async function getProject() {
                const res = await fetch('/projects/' + currentProjectId, {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const data = await res.json();
                log(data);
            }

            async function createDocument() {
                const title = document.getElementById('doc-title').value;
                const res = await fetch('/projects/' + currentProjectId + '/documents', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                    body: JSON.stringify({ title: title })
                });
                const data = await res.json();
                if(data.id) currentDocId = data.id;
                log(data);
            }

            async function getDocument() {
                const res = await fetch('/documents/' + currentDocId, {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const data = await res.json();
                log(data);
            }
        </script>
    </body>
    </html>
    """

@app.get("/api/v1/test-target")
def test_target_api():
    return {"status": "TARGET_API_OK"}

@app.get("/target-script.js")
def target_script():
    return Response(content="console.log('TARGET_SCRIPT_OK');", media_type="application/javascript")

@app.get("/target-style.css")
def target_style():
    return Response(content="/* TARGET_STYLE_OK */ body { background: #0f172a; color: #e2e8f0; }", media_type="text/css")

@app.post("/login")
def login(req: LoginRequest):
    if req.username == "alice" and req.password == "password123":
        return {"token": "bearer_alice_secret_token_12345", "user": "alice", "role": "user"}
    elif req.username == "bob" and req.password == "password123":
        return {"token": "bearer_bob_secret_token_67890", "user": "bob", "role": "user"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/projects")
def list_projects(authorization: Optional[str] = Header(None)):
    return list(projects_db.values())

@app.post("/projects", status_code=201)
def create_project(req: CreateProjectRequest, authorization: Optional[str] = Header(None)):
    global project_id_counter
    pid = project_id_counter
    project_id_counter += 1
    
    owner = "alice" if authorization and "alice" in authorization else "bob"
    proj = {"id": pid, "name": req.name, "owner": owner}
    projects_db[pid] = proj
    return proj

@app.get("/projects/{project_id}")
def get_project(project_id: int, authorization: Optional[str] = Header(None)):
    proj = projects_db.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@app.post("/projects/{project_id}/documents", status_code=201)
def create_document(project_id: int, req: CreateDocumentRequest, authorization: Optional[str] = Header(None)):
    global doc_id_counter
    did = doc_id_counter
    doc_id_counter += 1

    doc = {"id": did, "project_id": project_id, "title": req.title}
    documents_db[did] = doc
    return doc

@app.get("/documents/{document_id}")
def get_document(document_id: int, authorization: Optional[str] = Header(None)):
    doc = documents_db.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

if __name__ == "__main__":
    import os
    import uvicorn
    host = os.getenv("REFERENCE_TARGET_HOST", "127.0.0.1")
    port = int(os.getenv("REFERENCE_TARGET_PORT", "8001"))
    uvicorn.run("app:app", host=host, port=port, reload=True)

