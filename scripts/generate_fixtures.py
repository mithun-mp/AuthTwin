import os
import json

HAR_DIR = "fixtures/har"
OPENAPI_DIR = "fixtures/openapi"

os.makedirs(HAR_DIR, exist_ok=True)
os.makedirs(OPENAPI_DIR, exist_ok=True)

# 1. Sample HAR File
har_data = {
    "log": {
        "version": "1.2",
        "creator": {"name": "AuthTwin Reference Traffic Generator", "version": "1.0"},
        "entries": [
            {
                "startedDateTime": "2026-09-04T10:00:00.000Z",
                "request": {
                    "method": "POST",
                    "url": "http://127.0.0.1:8090/login",
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "postData": {"text": '{"username": "alice", "password": "password123"}'}
                },
                "response": {
                    "status": 200,
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "content": {"text": '{"token": "bearer_alice_secret_token_12345", "user": "alice"}'}
                }
            },
            {
                "startedDateTime": "2026-09-04T10:00:02.000Z",
                "request": {
                    "method": "POST",
                    "url": "http://127.0.0.1:8090/projects",
                    "headers": [
                        {"name": "Authorization", "value": "Bearer bearer_alice_secret_token_12345"},
                        {"name": "Content-Type", "value": "application/json"}
                    ],
                    "postData": {"text": '{"name": "Project Alpha"}'}
                },
                "response": {
                    "status": 201,
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "content": {"text": '{"id": 101, "name": "Project Alpha", "owner": "alice"}'}
                }
            },
            {
                "startedDateTime": "2026-09-04T10:00:04.000Z",
                "request": {
                    "method": "GET",
                    "url": "http://127.0.0.1:8090/projects/101",
                    "headers": [
                        {"name": "Authorization", "value": "Bearer bearer_alice_secret_token_12345"}
                    ]
                },
                "response": {
                    "status": 200,
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "content": {"text": '{"id": 101, "name": "Project Alpha", "owner": "alice"}'}
                }
            },
            {
                "startedDateTime": "2026-09-04T10:00:06.000Z",
                "request": {
                    "method": "POST",
                    "url": "http://127.0.0.1:8090/projects/101/documents",
                    "headers": [
                        {"name": "Authorization", "value": "Bearer bearer_alice_secret_token_12345"},
                        {"name": "Content-Type", "value": "application/json"}
                    ],
                    "postData": {"text": '{"title": "Architecture Plan"}'}
                },
                "response": {
                    "status": 201,
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "content": {"text": '{"id": 501, "project_id": 101, "title": "Architecture Plan"}'}
                }
            },
            {
                "startedDateTime": "2026-09-04T10:00:08.000Z",
                "request": {
                    "method": "GET",
                    "url": "http://127.0.0.1:8090/documents/501",
                    "headers": [
                        {"name": "Authorization", "value": "Bearer bearer_alice_secret_token_12345"}
                    ]
                },
                "response": {
                    "status": 200,
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "content": {"text": '{"id": 501, "project_id": 101, "title": "Architecture Plan"}'}
                }
            }
        ]
    }
}

with open(f"{HAR_DIR}/alice_workflow.har", "w") as f:
    json.dump(har_data, f, indent=2)

# 2. Sample OpenAPI Specification
openapi_data = {
    "openapi": "3.0.0",
    "info": {
        "title": "Reference Target API",
        "version": "1.0.0",
        "description": "OpenAPI specification for AuthTwin reference target."
    },
    "servers": [{"url": "http://127.0.0.1:8090"}],
    "paths": {
        "/login": {
            "post": {
                "summary": "Login User",
                "operationId": "loginUser",
                "responses": {"200": {"description": "Successful Login"}}
            }
        },
        "/projects": {
            "get": {
                "summary": "List Projects",
                "operationId": "listProjects",
                "responses": {"200": {"description": "List of projects"}}
            },
            "post": {
                "summary": "Create Project",
                "operationId": "createProject",
                "responses": {"201": {"description": "Project created"}}
            }
        },
        "/projects/{project_id}": {
            "get": {
                "summary": "Get Project Details",
                "operationId": "getProject",
                "responses": {"200": {"description": "Project details"}}
            }
        },
        "/projects/{project_id}/documents": {
            "post": {
                "summary": "Create Document under Project",
                "operationId": "createDocument",
                "responses": {"201": {"description": "Document created"}}
            }
        },
        "/documents/{document_id}": {
            "get": {
                "summary": "Get Document Details",
                "operationId": "getDocument",
                "responses": {"200": {"description": "Document details"}}
            }
        }
    }
}

with open(f"{OPENAPI_DIR}/reference_api_spec.json", "w") as f:
    json.dump(openapi_data, f, indent=2)

print("Fixtures generated successfully!")
