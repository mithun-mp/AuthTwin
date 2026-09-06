import json
import uuid
import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session as DBSession
from app.models import Transaction, Dependency
from app.logging import logger

def extract_primitive_values_from_json(data: Any, prefix: str = "response.body") -> List[Tuple[str, str]]:
    """
    Recursively extracts scalar values (ints, strings > 1 char, UUIDs) from JSON payload.
    Returns list of (field_path, value_str).
    """
    results = []
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{prefix}.{k}"
            if isinstance(v, (dict, list)):
                results.extend(extract_primitive_values_from_json(v, current_path))
            elif v is not None and not isinstance(v, bool):
                val_str = str(v).strip()
                # Exclude trivial values like empty string or single-digit numbers 0-9 if desired, or keep integers >= 10 or strings
                if len(val_str) > 0 and val_str not in ("true", "false", "null"):
                    results.append((current_path, val_str))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            current_path = f"{prefix}[{idx}]"
            if isinstance(item, (dict, list)):
                results.extend(extract_primitive_values_from_json(item, current_path))
            elif item is not None and not isinstance(item, bool):
                val_str = str(item).strip()
                if len(val_str) > 0 and val_str not in ("true", "false", "null"):
                    results.append((current_path, val_str))
    return results

def find_value_in_consumer(consumer_tx: Transaction, target_val: str) -> List[Dict[str, str]]:
    """
    Checks if target_val appears in consumer request path, query params, headers, or body.
    Returns list of match location dicts.
    """
    matches = []
    val_str = str(target_val)
    if len(val_str) < 2: # Ignore single character matches to prevent noisy false dependencies
        return matches

    # 1. Path match
    path_segments = [seg for seg in consumer_tx.path.split("/") if seg]
    for idx, seg in enumerate(path_segments):
        if seg == val_str:
            matches.append({
                "location": "PATH",
                "name": f"path_segment_{idx}",
                "type": "RESPONSE_TO_PATH"
            })

    # 2. Query Params match
    if consumer_tx.query_params:
        for qk, qv in consumer_tx.query_params.items():
            if str(qv) == val_str:
                matches.append({
                    "location": "QUERY",
                    "name": qk,
                    "type": "RESPONSE_TO_QUERY"
                })

    # 3. Request Body match
    if consumer_tx.req_body:
        try:
            body_json = json.loads(consumer_tx.req_body)
            body_scalars = extract_primitive_values_from_json(body_json, "request.body")
            for bpath, bval in body_scalars:
                if bval == val_str:
                    field_name = bpath.split(".")[-1]
                    matches.append({
                        "location": "BODY",
                        "name": field_name,
                        "type": "RESPONSE_TO_BODY"
                    })
        except Exception:
            if val_str in consumer_tx.req_body:
                matches.append({
                    "location": "BODY",
                    "name": "raw_body",
                    "type": "RESPONSE_TO_BODY"
                })

    # 4. Request Headers match
    if consumer_tx.req_headers:
        for hk, hv in consumer_tx.req_headers.items():
            if hk.lower() not in ("authorization", "host", "content-length", "content-type", "user-agent", "accept"):
                if str(hv) == val_str:
                    matches.append({
                        "location": "HEADER",
                        "name": hk,
                        "type": "RESPONSE_TO_HEADER"
                    })

    return matches


def analyze_session_dependencies(db: DBSession, session_id: str) -> List[Dependency]:
    """
    Analyzes all transactions in a session chronologically and creates Dependency records.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.session_id == session_id)
        .order_by(Transaction.timestamp.asc())
        .all()
    )

    if len(transactions) < 2:
        return []

    # Clear previous dependencies for these transactions to avoid duplicates
    tx_ids = [t.id for t in transactions]
    db.query(Dependency).filter(Dependency.producer_transaction_id.in_(tx_ids)).delete(synchronize_session=False)
    db.commit()

    created_dependencies = []

    for i in range(len(transactions)):
        producer_tx = transactions[i]
        if not producer_tx.res_body or producer_tx.res_status >= 400:
            continue

        try:
            res_json = json.loads(producer_tx.res_body)
            produced_scalars = extract_primitive_values_from_json(res_json, "response.body")
        except Exception:
            continue

        for field_path, val in produced_scalars:
            # Skip generic boolean/status keywords or common response count fields matching pagination params
            field_name_lower = field_path.split(".")[-1].lower()
            
            # Look ahead at consumer transactions
            for j in range(i + 1, len(transactions)):
                consumer_tx = transactions[j]
                consumer_matches = find_value_in_consumer(consumer_tx, val)

                for match in consumer_matches:
                    consumer_param_lower = match["name"].lower()
                    
                    # Heuristic for false positive coincidental matches (e.g. total=101 matching page=101)
                    confidence = 1.0
                    if consumer_param_lower in ("page", "limit", "offset", "size", "per_page", "page_size"):
                        if field_name_lower in ("total", "count", "total_count", "length"):
                            confidence = 0.2 # Low confidence coincidental match

                    # Exclude low confidence coincidental matches from primary dependency graph
                    if confidence >= 0.5:
                        dep = Dependency(
                            id=str(uuid.uuid4()),
                            producer_transaction_id=producer_tx.id,
                            consumer_transaction_id=consumer_tx.id,
                            producer_field_path=field_path,
                            consumer_field_location=match["location"],
                            consumer_field_name=match["name"],
                            extracted_value=val,
                            dependency_type=match["type"],
                            confidence=confidence
                        )
                        db.add(dep)
                        created_dependencies.append(dep)

    db.commit()
    logger.info(f"Session {session_id}: Discovered {len(created_dependencies)} producer-consumer dependencies.")
    return created_dependencies
