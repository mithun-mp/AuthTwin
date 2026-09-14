import json
import uuid
import datetime
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List, Tuple
from app.core.logging import logger, redact_headers

def parse_har_content(har_content: str | dict) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Parses HAR 1.2 content into a list of normalized transaction dictionaries.
    Returns (transactions_data, warnings).
    """
    warnings = []
    transactions = []

    if isinstance(har_content, str):
        try:
            har_json = json.loads(har_content)
        except Exception as e:
            raise ValueError(f"Invalid HAR JSON: {str(e)}")
    else:
        har_json = har_content

    log_obj = har_json.get("log", {})
    entries = log_obj.get("entries", [])
    if not entries:
        warnings.append("HAR file contains no entries in log.entries")
        return transactions, warnings

    for idx, entry in enumerate(entries):
        try:
            req = entry.get("request", {})
            res = entry.get("response", {})

            method = req.get("method", "GET").upper()
            url = req.get("url", "")
            if not url:
                warnings.append(f"Entry #{idx} skipped: Missing URL")
                continue

            parsed_url = urlparse(url)
            path = parsed_url.path or "/"

            # Query params
            query_params = {}
            if req.get("queryString"):
                for q in req.get("queryString", []):
                    query_params[q.get("name")] = q.get("value")
            elif parsed_url.query:
                qs = parse_qs(parsed_url.query)
                query_params = {k: v[0] if len(v) == 1 else v for k, v in qs.items()}

            # Request Headers
            req_headers_raw = {h.get("name"): h.get("value") for h in req.get("headers", [])} if req.get("headers") else {}
            req_headers_redacted = redact_headers(req_headers_raw)

            # Request Body
            post_data = req.get("postData", {})
            req_body = post_data.get("text", "")

            # Response Status & Headers
            res_status = res.get("status", 200)
            res_headers_raw = {h.get("name"): h.get("value") for h in res.get("headers", [])} if res.get("headers") else {}
            res_headers_redacted = redact_headers(res_headers_raw)

            # Response Body
            res_content = res.get("content", {})
            res_body = res_content.get("text", "")

            # Timestamp
            started_date_time = entry.get("startedDateTime")
            if started_date_time:
                try:
                    dt = datetime.datetime.fromisoformat(started_date_time.replace("Z", "+00:00"))
                except Exception:
                    dt = datetime.datetime.utcnow()
            else:
                dt = datetime.datetime.utcnow()

            trans_dict = {
                "id": str(uuid.uuid4()),
                "timestamp": dt,
                "method": method,
                "url": url,
                "path": path,
                "query_params": query_params,
                "req_headers": req_headers_redacted,
                "raw_req_headers": req_headers_raw,  # used temporarily for session tracker token extraction
                "req_body": req_body,
                "res_status": res_status,
                "res_headers": res_headers_redacted,
                "res_body": res_body,
                "operation_id": None
            }
            transactions.append(trans_dict)
        except Exception as err:
            warnings.append(f"Entry #{idx} error: {str(err)}")
            logger.warning(f"Error parsing HAR entry #{idx}: {err}")

    return transactions, warnings
