"""
Enterprise decision engine.

TODO: Participants will implement query routing (Activity 1.3) and, later,
function-calling action selection (Activity 2.3).
"""
import json
from typing import Any, Dict, Optional

from src.llm.llm_client import LLMClient
from src.llm.prompt_manager import PromptManager
from src.tools.tool_registry import ToolRegistry
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DecisionEngine:
    """Decides how to handle a customer query: which sub-agent should own it
    (route_query), and - once routed to the Customer Service Agent - which
    registered tool, if any, to call and with what parameters
    (select_action), using the LLM's native function calling."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.llm = LLMClient()
        self.prompt_mgr = PromptManager()
        # Built lazily (see the `tool_registry` property below): route_query()
        # (Activity 1.3) doesn't need a ToolRegistry at all, and Activity 2.1
        # (Tool Registry) isn't implemented yet at that point in the
        # workbook. Only select_action() (Activity 2.3) needs one.
        self._tool_registry = tool_registry

        agent_config = load_yaml_config("config/agent_config.yaml")
        coordination = agent_config.get("coordination", {})
        self.default_route = coordination.get("default_route", "knowledge_agent")
        self.valid_routes = coordination.get("routes", ["knowledge_agent", "customer_service_agent"])
        self.confidence_threshold = coordination.get("confidence_threshold", 0.6)

        self.max_tool_calls = agent_config.get("action_selection", {}).get("max_tool_calls", 1)

    @property
    def tool_registry(self) -> ToolRegistry:
        """Lazily construct the ToolRegistry on first use (see __init__)."""
        if self._tool_registry is None:
            self._tool_registry = ToolRegistry()
        return self._tool_registry

    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Decide which single sub-agent should handle this query.

        TODO (Activity 1.3):
        1. Get the "coordinator_routing_prompt" from self.prompt_mgr and build
           a system + user message pair (format the user_template with `query`).
        2. Call self.llm.generate(messages, temperature=0.0, max_tokens=200)
           and json.loads() the result - the prompt asks the LLM for a JSON
           object shaped {"route": ..., "confidence": ..., "reasoning": ...}.
        3. If parsing fails, or the parsed "route" isn't in self.valid_routes,
           fall back to {"route": self.default_route, "confidence": 0.0,
           "reasoning": "..."} rather than raising.
        4. Otherwise: read confidence = float(parsed.get("confidence", 0.0)); if
           confidence < self.confidence_threshold, log a warning (proceed anyway -
           this is a flag, not a hard gate). Return {"route": ..., "confidence": confidence,
           "reasoning": ...} from the parsed JSON.
        """
        prompt = self.prompt_mgr.get_prompt("coordinator_routing_prompt") 
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user_template"].format(query=query)},
        ]
        raw = self.llm.generate(messages, temperature=0.0, max_tokens=200)

        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Routing response was not valid JSON, defaulting to '{self.default_route}': {raw!r}")
            return {
                "route": self.default_route,
                "confidence": 0.0,
                "reasoning": "Fell back to the default route after an unparseable routing response.",
            }

        route = parsed.get("route", self.default_route)
        if route not in self.valid_routes:
            route = self.default_route

        confidence = float(parsed.get("confidence", 0.0))
        if confidence < self.confidence_threshold:
            logger.warning(
                f"Routing confidence {confidence:.2f} is below the configured threshold "
                f"({self.confidence_threshold}) for route '{route}' - proceeding anyway, but flagging it."
            )

        return {
            "route": route,
            "confidence": confidence,
            "reasoning": parsed.get("reasoning", ""),
        }        
         
    def select_action(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use the LLM's native function calling to pick at most one registered
        tool - and its parameters - to satisfy this query.

        TODO (Activity 2.3):
        1. Get the "action_selection_prompt" system text from self.prompt_mgr;
           if `context` is given, append it (e.g. via json.dumps) to the
           system message so the LLM knows what's already known.
        2. Get the available function schemas from
           self.tool_registry.get_function_schemas().
        3. Call self.llm.client.chat.completions.create(...) with `messages`
           (system + the user query) and `tools=[{"type": "function",
           "function": schema} for schema in functions]`, tool_choice=
           ("auto" if self.max_tool_calls > 0 else "none").
        4. Read response.choices[0].message. If message.tool_calls is empty,
           return {"tool_name": None, "parameters": {}, "reasoning": message.content or "..."}.
        5. Otherwise take the first tool call, json.loads() its
           .function.arguments (default to {} on a parse error), and return
           {"tool_name": call.function.name, "parameters": arguments, "reasoning": "..."}.
        """
        # TODO: build the function-calling request, call the LLM, and parse
        # the tool call (or lack of one) as described above.
        raise NotImplementedError("Action selection not implemented")
