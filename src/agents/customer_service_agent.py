"""
Customer Service Agent.

TODO: Participants will implement handle() (Activity 2.2).
"""
import json
from typing import Any, Dict, Optional

from src.core.decision_engine import DecisionEngine
from src.llm.llm_client import LLMClient
from src.llm.prompt_manager import PromptManager
from src.utils.logger import setup_logger
from src.utils.retry import with_retry

logger = setup_logger(__name__)


class CustomerServiceAgent:
    """Handles requests that need a specific customer's data or an action
    taken on their behalf, by selecting and invoking a registered enterprise
    service tool through the Decision Engine's function calling."""

    def __init__(self, decision_engine: Optional[DecisionEngine] = None):
        self.decision_engine = decision_engine or DecisionEngine()
        self.llm = LLMClient()
        self.prompt_mgr = PromptManager()

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Select and execute at most one tool for this query, then phrase the
        result - or the lack of a matching tool - as a customer-facing response.

        TODO (Activity 2.2):
        1. Call self.decision_engine.select_action(query, context=context)
           to get {"tool_name": ..., "parameters": ..., "reasoning": ...}.
        2. If tool_name is falsy (no tool was selected), return:
           {"response": action.get("reasoning") or "Could you tell me a bit
           more about what you need?", "source": "customer_service_agent",
           "tool_used": None, "tool_result": None}
        3. Otherwise execute the tool via
           self._execute_tool(tool_name, action.get("parameters", {}))
           (already implemented below - it's the retry-wrapped call, Activity 3.2),
           then call self._format_response(query, tool_name, tool_result)
           (already implemented below) to phrase a reply.
        4. Return {"response": response, "source": "customer_service_agent",
           "tool_used": tool_name, "tool_result": tool_result}.
        """
        # TODO: select an action, execute the tool if one was chosen, and
        # build the response dict as described above.
        raise NotImplementedError("Customer service handling not implemented")

    @with_retry()
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a registered tool with retry-with-backoff (Activity 3.2) -
        the one enterprise service call this platform demonstrates retry on."""
        return self.decision_engine.tool_registry.execute(tool_name, **parameters)

    def _format_response(self, query: str, tool_name: str, tool_result: Any) -> str:
        """Phrase a tool's raw result as a customer-facing reply using the LLM."""
        prompt = self.prompt_mgr.get_prompt("service_response_prompt")
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user_template"].format(
                query=query, tool_name=tool_name, tool_result=json.dumps(tool_result)
            )},
        ]
        return self.llm.generate(messages, temperature=0.3, max_tokens=300)
