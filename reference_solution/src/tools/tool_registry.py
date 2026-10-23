"""Enterprise service tool registry - REFERENCE SOLUTION"""
import importlib
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ToolDefinition:
    """A single registered tool: its callable plus the metadata needed to
    describe it to the LLM for function calling (see core/decision_engine.py)."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable[..., Any]


class ToolRegistry:
    """Simple name -> function registry for enterprise-service tools.

    Tool definitions come from config/tools_config.yaml so registering a new
    tool is a config change plus a function, not a code change here.
    """

    def __init__(self, config_path: str = "config/tools_config.yaml"):
        config = load_yaml_config(config_path)
        self._fail_on_missing_tool = config.get("registry", {}).get("fail_on_missing_tool", True)
        self._tools: Dict[str, ToolDefinition] = {}

        for entry in config.get("tools", []):
            self._register_from_config(entry)

    def _register_from_config(self, entry: Dict[str, Any]) -> None:
        """Import the configured module/function and register it as a tool."""
        module = importlib.import_module(entry["module"])
        function = getattr(module, entry["function"])
        self.register(
            name=entry["name"],
            description=entry["description"].strip(),
            parameters=entry["parameters"],
            function=function,
        )

    def register(self, name: str, description: str, parameters: Dict[str, Any], function: Callable[..., Any]) -> None:
        """Register a single tool under `name`."""
        self._tools[name] = ToolDefinition(name=name, description=description, parameters=parameters, function=function)
        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Look up a registered tool's definition by name."""
        tool = self._tools.get(name)
        if tool is None and self._fail_on_missing_tool:
            raise KeyError(f"Tool '{name}' is not registered.")
        return tool

    def list_tools(self) -> List[str]:
        """List the names of every registered tool."""
        return list(self._tools.keys())

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """Return every tool's description in OpenAI function-calling schema
        shape, for handing to the LLM as available functions."""
        return [
            {"name": tool.name, "description": tool.description, "parameters": tool.parameters}
            for tool in self._tools.values()
        ]

    def execute(self, name: str, **kwargs: Any) -> Any:
        """Look up and call a registered tool by name with keyword arguments."""
        tool = self.get_tool(name)
        if tool is None:
            return {"error": f"Tool '{name}' is not registered."}
        return tool.function(**kwargs)
