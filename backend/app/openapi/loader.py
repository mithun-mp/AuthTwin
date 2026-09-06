import json
import re
import uuid
import yaml
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session as DBSession
from app.models import OpenAPISpec, OpenAPIOperation, Transaction
from app.logging import logger

def parse_openapi_content(content_str: str) -> Dict[str, Any]:
    """Parses raw OpenAPI YAML or JSON content."""
    try:
        return json.loads(content_str)
    except Exception:
        try:
            return yaml.safe_load(content_str)
        except Exception as e:
            raise ValueError(f"Failed to parse OpenAPI as JSON or YAML: {str(e)}")

def path_template_to_regex(template: str) -> re.Pattern:
    """Converts an OpenAPI path template like /projects/{project_id} to regex pattern."""
    # Escape special regex characters except curly braces
    escaped = re.escape(template)
    # Replace \{param\} with named capturing group or wildcard match
    pattern = re.sub(r'\\\{([^/]+)\\\}', r'([^/]+)', escaped)
    return re.compile(f"^{pattern}$")

def match_path_template(actual_path: str, path_templates: List[str]) -> Optional[str]:
    """Finds the best matching OpenAPI path template for an actual path."""
    actual = actual_path.rstrip("/") or "/"
    for tmpl in path_templates:
        norm_tmpl = tmpl.rstrip("/") or "/"
        if norm_tmpl == actual:
            return tmpl
        pattern = path_template_to_regex(norm_tmpl)
        if pattern.match(actual):
            return tmpl
    return None

def load_and_save_openapi(db: DBSession, target_id: str, spec_content_str: str) -> OpenAPISpec:
    """Parses OpenAPI spec and saves spec and operations to database."""
    spec_json = parse_openapi_content(spec_content_str)

    info = spec_json.get("info", {})
    title = info.get("title", "OpenAPI Specification")
    version = info.get("version", "1.0.0")

    spec_obj = OpenAPISpec(
        id=str(uuid.uuid4()),
        target_id=target_id,
        title=title,
        version=version,
        spec_json=spec_json
    )
    db.add(spec_obj)
    db.flush()

    paths = spec_json.get("paths", {})
    for path_template, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, op_data in path_item.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue
            if not isinstance(op_data, dict):
                continue

            op_id = op_data.get("operationId") or f"{method.lower()}_{path_template.replace('/', '_')}"
            summary = op_data.get("summary", "")

            op_obj = OpenAPIOperation(
                id=str(uuid.uuid4()),
                spec_id=spec_obj.id,
                operation_id=op_id,
                method=method.upper(),
                path_template=path_template,
                summary=summary,
                parameters_schema=op_data.get("parameters"),
                responses_schema=op_data.get("responses")
            )
            db.add(op_obj)

    db.commit()

    # Automatically map existing transactions to new spec operations
    match_transactions_to_operations(db, spec_obj)
    return spec_obj

def match_transactions_to_operations(db: DBSession, spec: OpenAPISpec):
    """Maps unassigned or existing transactions to the loaded OpenAPI operations."""
    ops = db.query(OpenAPIOperation).filter(OpenAPIOperation.spec_id == spec.id).all()
    if not ops:
        return

    path_templates = list({op.path_template for op in ops})

    transactions = db.query(Transaction).all()
    for tx in transactions:
        matched_template = match_path_template(tx.path, path_templates)
        if matched_template:
            matched_op = next((op for op in ops if op.path_template == matched_template and op.method == tx.method), None)
            if matched_op:
                tx.operation_id = matched_op.operation_id
    db.commit()
