"""Customer Service Agent - REFERENCE SOLUTION"""
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
        """Select and execute at most one tool for this query, then phrase
        the result - or the lack of a matching tool - as a customer-facing
        response."""
        action = self.decision_engine.select_action(query, context=context)
        tool_name = action.get("tool_name")

        if not tool_name:
            return {
                "response": action.get("reasoning") or "Could you tell me a bit more about what you need?",
                "source": "customer_service_agent",
                "tool_used": None,
                "tool_result": None,
            }

        tool_result = self._execute_tool(tool_name, action.get("parameters", {}))
        response = self._format_response(query, tool_name, tool_result)

        return {
            "response": response,
            "source": "customer_service_agent",
            "tool_used": tool_name,
            "tool_result": tool_result,
        }

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
