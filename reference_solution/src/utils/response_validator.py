"""Response validation for enterprise customer service operations - REFERENCE SOLUTION"""
from typing import Any, Dict, Optional

from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Every response returned by the platform (see agents/*.py) shares these
# fields at minimum, regardless of which sub-agent produced it.
DEFAULT_REQUIRED_FIELDS = ["response", "source"]


class ResponseValidator:
    """Validates a sub-agent's response dict against the required fields
    declared in config/agent_config.yaml before it's returned to the caller.
    A field-presence/schema check, not a validation framework."""

    def __init__(self):
        config = load_yaml_config("config/agent_config.yaml")
        self.required_fields = config.get("validation", {}).get(
            "required_response_fields", DEFAULT_REQUIRED_FIELDS
        )

    def validate(self, response: Dict[str, Any]) -> Optional[str]:
        """Return None if `response` is valid, otherwise a human-readable
        validation error describing what's wrong."""
        missing = [field for field in self.required_fields if field not in response]
        if missing:
            return f"Response is missing required field(s): {', '.join(missing)}"

        text = response.get("response")
        if not isinstance(text, str) or not text.strip():
            return "Response text is empty"

        return None
