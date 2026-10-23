"""Customer service request creation service - REFERENCE SOLUTION"""
from datetime import datetime, timezone
from typing import Any, Dict, List

# In-memory service-request store. This is a mock enterprise service for a
# guided lab - it resets whenever the process restarts, which is fine for
# the lab's purposes (illustrating the integration pattern, not building a
# durable ticketing system).
_SERVICE_REQUESTS: List[Dict[str, Any]] = []


def create_service_request(customer_id: str, request_type: str, description: str) -> Dict[str, Any]:
    """Open a new customer service request and return a tracking confirmation."""
    request_id = f"SR-{len(_SERVICE_REQUESTS) + 1:05d}"
    record = {
        "request_id": request_id,
        "customer_id": customer_id,
        "request_type": request_type,
        "description": description,
        "status": "Open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _SERVICE_REQUESTS.append(record)
    return record


def get_service_request(request_id: str) -> Dict[str, Any]:
    """Look up a previously created service request by its tracking ID."""
    for record in _SERVICE_REQUESTS:
        if record["request_id"] == request_id:
            return record
    return {"error": "Service request not found", "request_id": request_id}
