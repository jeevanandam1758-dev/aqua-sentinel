from typing import Any, Dict, List, Optional


class ScanCreatePayload(dict):
    """Compatibility wrapper for legacy payloads."""

    pass


def ensure_scan_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Prediction payload must be an object.")
    return payload
