"""
Response validation for enterprise customer service operations.

TODO: Participants will implement the validate() check (Activity 3.3).
"""
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
        """
        Return None if `response` is valid, otherwise a human-readable
        validation error describing what's wrong.

        TODO:
        1. Find which of self.required_fields are missing from `response`
           (not present as a key at all). If any are missing, return
           f"Response is missing required field(s): {', '.join(missing)}".
        2. Otherwise check response.get("response") is a non-empty string
           (after .strip()). If it isn't, return "Response text is empty".
        3. Otherwise return None (valid).
        """
        # TODO: implement the field-presence and non-empty-text checks above.
        raise NotImplementedError("Response validation not implemented")
