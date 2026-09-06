import pytest
from app.ingestion.har_parser import parse_har_content

SAMPLE_HAR = {
    "log": {
        "version": "1.2",
        "entries": [
            {
                "startedDateTime": "2026-09-04T10:00:00.000Z",
                "request": {
                    "method": "POST",
                    "url": "http://127.0.0.1:8090/projects",
                    "headers": [
                        {"name": "Authorization", "value": "Bearer secret_token_alice_12345"},
                        {"name": "Content-Type", "value": "application/json"}
                    ],
                    "postData": {"text": '{"name": "Project Alpha"}'}
                },
                "response": {
                    "status": 201,
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "content": {"text": '{"id": 101, "name": "Project Alpha"}'}
                }
            },
            {
                "startedDateTime": "2026-09-04T10:00:05.000Z",
                "request": {
                    "method": "GET",
                    "url": "http://127.0.0.1:8090/projects/101",
                    "headers": [
                        {"name": "Authorization", "value": "Bearer secret_token_alice_12345"}
                    ]
                },
                "response": {
                    "status": 200,
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "content": {"text": '{"id": 101, "name": "Project Alpha"}'}
                }
            }
        ]
    }
}

def test_parse_valid_har():
    txs, warnings = parse_har_content(SAMPLE_HAR)
    assert len(txs) == 2
    assert len(warnings) == 0

    assert txs[0]["method"] == "POST"
    assert txs[0]["path"] == "/projects"
    assert "101" in txs[0]["res_body"]

    # Assert headers are redacted in normalized tx dict
    assert txs[0]["req_headers"]["Authorization"] != "Bearer secret_token_alice_12345"
    assert "[REDACTED]" in txs[0]["req_headers"]["Authorization"]

def test_parse_empty_har():
    txs, warnings = parse_har_content({"log": {"entries": []}})
    assert len(txs) == 0
    assert len(warnings) == 1
