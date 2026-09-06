import pytest
from app.openapi.loader import match_path_template

def test_match_path_template():
    templates = [
        "/projects",
        "/projects/{project_id}",
        "/projects/{project_id}/documents/{document_id}"
    ]

    assert match_path_template("/projects", templates) == "/projects"
    assert match_path_template("/projects/101", templates) == "/projects/{project_id}"
    assert match_path_template("/projects/101/documents/501", templates) == "/projects/{project_id}/documents/{document_id}"
    assert match_path_template("/unknown/route", templates) is None
