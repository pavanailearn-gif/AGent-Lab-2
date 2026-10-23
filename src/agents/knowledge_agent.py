"""
Knowledge Agent, wrapping the vendored Bootcamp 1 agent.

TODO: Participants will implement handle() (Activity 1.2).
"""
from typing import Any, Dict, Optional

from src.bootcamp1_agent.core.agent_workflow import CustomerOperationsAgent
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class KnowledgeAgent:
    """Answers policy/procedure/product questions by delegating to the
    already-complete Bootcamp 1 CustomerOperationsAgent, used as a black box
    - not edited or partially reimplemented."""

    def __init__(self):
        self.agent = CustomerOperationsAgent()

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run the vendored agent's workflow and translate its AgentState
        result into this platform's shared response shape."""
        state = self.agent.run(query)

        return {
            "response": state.get("response") or "I wasn't able to find an answer to that.",
            "citations": state.get("citations", []),
            "source": "knowledge_agent",
            "needs_escalation": bool(state.get("needs_escalation")),
        }
