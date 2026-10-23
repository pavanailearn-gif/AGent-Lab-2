"""
Retry-with-backoff wrapper for enterprise service calls.

TODO: Participants will implement the retry loop (Activity 3.2).
"""
import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type

from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def with_retry(
    max_attempts: Optional[int] = None,
    backoff_seconds: Optional[float] = None,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
) -> Callable:
    """Decorator: retry a function up to max_attempts times, with
    exponential backoff between attempts, on any of `exceptions`.

    Defaults for max_attempts/backoff_seconds come from config/agent_config.yaml's
    "retry" section when not passed explicitly - one retry policy, applied
    once (see agents/customer_service_agent.py's _execute_tool), not a
    comprehensive resilience framework.
    """
    config = load_yaml_config("config/agent_config.yaml").get("retry", {})
    resolved_max_attempts = max_attempts if max_attempts is not None else config.get("max_attempts", 3)
    resolved_backoff = backoff_seconds if backoff_seconds is not None else config.get("backoff_seconds", 0.5)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            TODO: Loop `for attempt in range(1, resolved_max_attempts + 1)`.
            Inside, try `return func(*args, **kwargs)`. On any exception in
            `exceptions`, log a warning (attempt number / resolved_max_attempts),
            and if this wasn't the last attempt, sleep for an exponentially
            growing delay - e.g. `time.sleep(resolved_backoff * (2 ** (attempt - 1)))` -
            before looping again. If every attempt fails, log an error and
            re-raise the last caught exception (don't swallow it).
            """
            # TODO: implement the retry-with-backoff loop described above.
            raise NotImplementedError("Retry wrapper not implemented")
        return wrapper
    return decorator
