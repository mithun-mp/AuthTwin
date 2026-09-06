import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

logger = logging.getLogger("authtwin")

def redact_secret(value: str) -> str:
    """Safely redact secret tokens, cookies, or auth headers."""
    if not value:
        return ""
    if len(value) <= 12:
        return "[REDACTED]"
    return f"{value[:4]}...[REDACTED]...{value[-4:]}"

def redact_headers(headers: dict) -> dict:
    """Returns a copy of headers with sensitive authorization fields redacted."""
    if not headers:
        return {}
    sensitive_keys = {"authorization", "cookie", "set-cookie", "x-api-key", "api-key", "token", "session"}
    sanitized = {}
    for k, v in headers.items():
        if k.lower() in sensitive_keys:
            sanitized[k] = redact_secret(str(v))
        else:
            sanitized[k] = str(v)
    return sanitized
