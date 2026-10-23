"""
Coordinator Agent.

TODO: Participants will implement handle_turn() (Activity 1.2).
"""
from typing import Any, Dict, Optional

from src.agents.customer_service_agent import CustomerServiceAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.core.decision_engine import DecisionEngine
from src.core.session_manager import SessionManager
from src.utils.logger import setup_logger
from src.utils.response_validator import ResponseValidator

logger = setup_logger(__name__)


class CoordinatorAgent:
    """Routes each turn of a conversation to exactly one sub-agent -
    KnowledgeAgent or CustomerServiceAgent - and maintains customer context
    across turns via SessionManager. The same route-to-one-destination shape
    as Bootcamp 1's route_decision, one level up."""

    def __init__(
        self,
        decision_engine: Optional[DecisionEngine] = None,
        knowledge_agent: Optional[KnowledgeAgent] = None,
        customer_service_agent: Optional[CustomerServiceAgent] = None,
        session_manager: Optional[SessionManager] = None,
        response_validator: Optional[ResponseValidator] = None,
    ):
        self.decision_engine = decision_engine or DecisionEngine()
        self.knowledge_agent = knowledge_agent or KnowledgeAgent()
        self.customer_service_agent = customer_service_agent or CustomerServiceAgent(self.decision_engine)
        self.session_manager = session_manager or SessionManager()
        self.response_validator = response_validator or ResponseValidator()

    def handle_turn(self, session_id: str, query: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle one conversational turn: route it to exactly one sub-agent,
        delegate, and record the turn in the session.

        TODO (Activity 1.2):
        1. Get (or create) the session via
           self.session_manager.get_or_create_session(session_id, customer_id),
           then record the incoming turn with
           self.session_manager.add_turn(session_id, "user", query).
        2. Call self.decision_engine.route_query(query) to get
           {"route": ..., "confidence": ..., "reasoning": ...}.
        3. Build a context dict, e.g. {"customer_id": session.get("customer_id"),
           **session.get("context", {})}, to pass to whichever sub-agent handles this turn.
        4. If route == "customer_service_agent", call
           self.customer_service_agent.handle(query, context=context);
           otherwise call self.knowledge_agent.handle(query, context=context).
        5. Validate the result before returning it: call
           validation_error = self.response_validator.validate(result) (Activity 3.3).
           If it's not None, log a warning and replace `result` with a safe
           fallback: {"response": "I'm sorry, something went wrong while
           preparing a response. Please try again.", "source": result.get("source", "unknown")}.
        6. Record the route with self.session_manager.update_context(session_id, route=route),
           and record the reply with
           self.session_manager.add_turn(session_id, "assistant", result["response"]).
        7. Return {**result, "route": route, "route_confidence": route_decision.get("confidence"),
           "session_id": session_id}.
        """
        session = self.session_manager.get_or_create_session(session_id, customer_id)
        self.session_manager.add_turn(session_id, "user", query)

        route_decision = self.decision_engine.route_query(query)
        route = route_decision["route"]

        context = {"customer_id": session.get("customer_id"), **session.get("context", {})}

        if route == "customer_service_agent":
            result = self.customer_service_agent.handle(query, context=context)
        else:
            result = self.knowledge_agent.handle(query, context=context)

        # Activity 3.3: validate the response shape before it goes back to
        # the caller. This never raises - an invalid response is replaced
        # with a safe, generic reply rather than surfacing a broken one.
        validation_error = self.response_validator.validate(result)
        if validation_error:
            logger.warning(f"Response validation failed for session {session_id}: {validation_error}")
            result = {
                "response": "I'm sorry, something went wrong while preparing a response. Please try again.",
                "source": result.get("source", "unknown"),
            }

        self.session_manager.update_context(session_id, route=route)
        self.session_manager.add_turn(session_id, "assistant", result["response"])

        return {
            **result,
            "route": route,
            "route_confidence": route_decision.get("confidence"),
            "session_id": session_id,
        }
    
