"""Customer session management - REFERENCE SOLUTION"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionState(TypedDict):
    """Per-customer conversation state - the same state-passing pattern
    Bootcamp 1's AgentState uses (see src/bootcamp1_agent/core/agent_state.py),
    scoped to a session_id across turns instead of a single query."""
    session_id: str
    customer_id: Optional[str]
    conversation_history: List[Dict[str, str]]
    last_route: Optional[str]
    context: Dict[str, Any]
    created_at: str
    updated_at: str


class SessionManager:
    """In-memory store of SessionState, keyed by session_id. Backs customer
    context across turns for the Coordinator Agent - LangGraph-style state
    passing applied at session scope, per the scope-bounding decision to
    piggyback on that rather than build a custom persistence layer."""

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def create_session(self, session_id: str, customer_id: Optional[str] = None) -> SessionState:
        """Create and store a new session."""
        now = datetime.now(timezone.utc).isoformat()
        session: SessionState = {
            "session_id": session_id,
            "customer_id": customer_id,
            "conversation_history": [],
            "last_route": None,
            "context": {},
            "created_at": now,
            "updated_at": now,
        }
        self._sessions[session_id] = session
        logger.info(f"Created session {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Look up an existing session, or None if it doesn't exist yet."""
        return self._sessions.get(session_id)

    def get_or_create_session(self, session_id: str, customer_id: Optional[str] = None) -> SessionState:
        """Return the existing session, or create one if it doesn't exist yet."""
        return self.get_session(session_id) or self.create_session(session_id, customer_id)

    def add_turn(self, session_id: str, role: str, content: str) -> SessionState:
        """Append one conversation turn to a session's history."""
        session = self.get_or_create_session(session_id)
        session["conversation_history"].append({"role": role, "content": content})
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        return session

    def update_context(self, session_id: str, route: Optional[str] = None, **context_updates: Any) -> SessionState:
        """Record the route taken for the latest turn and merge in any
        additional context (e.g. a resolved customer_id) for future turns."""
        session = self.get_or_create_session(session_id)
        if route is not None:
            session["last_route"] = route
        session["context"].update(context_updates)
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        return session

    def get_recent_history(self, session_id: str, turns: int = 6) -> List[Dict[str, str]]:
        """Return the most recent `turns` conversation entries for a session."""
        session = self.get_session(session_id)
        if not session:
            return []
        return session["conversation_history"][-turns:]
