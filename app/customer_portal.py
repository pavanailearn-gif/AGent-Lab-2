"""
Enterprise Customer Service Operations Portal - Streamlit UI
Complete implementation for immediate use.
"""
import sys
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load this project's .env so OPENAI_API_KEY / LLM_BASE_URL are available when
# the portal is launched with a bare `streamlit run` (no shell exports).
# override=True: a stale OPENAI_API_KEY left in the shell from another project
# would otherwise silently shadow this project's own key.
load_dotenv(PROJECT_ROOT / ".env", override=True)

from src.utils.logger import setup_logger
from src.utils.validators import validate_query, sanitize_input

logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Enterprise Customer Service Operations Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f4788; font-weight: bold;}
    .sub-header {font-size: 1.2rem; color: #555; margin-bottom: 2rem;}
    .chat-message {padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;}
    .user-message {background-color: #e3f2fd; border-left: 4px solid #2196f3;}
    .agent-message {background-color: #f5f5f5; border-left: 4px solid #4caf50;}
    .citation {font-size: 0.9rem; color: #666; font-style: italic; margin-top: 0.5rem;}
    .route-badge {display: inline-block; font-size: 0.8rem; padding: 0.1rem 0.6rem; border-radius: 1rem;
                  margin-bottom: 0.4rem; font-weight: bold;}
    .route-knowledge {background-color: #e8f5e9; color: #2e7d32;}
    .route-service {background-color: #fff3e0; color: #e65100;}
    .stButton>button {background-color: #1f4788; color: white; font-weight: bold;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Query-processing pipeline view
#
# A learner-facing picture of what handle_turn() does with a query behind the
# scenes. Each stage names the method that runs and the workbook activity that
# implements it, so the diagram doubles as a progress map: run a query and the
# stages fill in green up to the first one that still raises NotImplementedError.
# ---------------------------------------------------------------------------

PIPELINE = [
    dict(key="entry", label="1 · Query received",
         method="CoordinatorAgent.handle_turn()",
         activity="1.2",
         note="The portal hands your text and a session id to the Coordinator."),
    dict(key="session_in", label="2 · Session loaded",
         method="SessionManager.get_or_create_session() -> add_turn()",
         activity="3.1",
         note="Your message is stored so the platform remembers this conversation."),
    dict(key="route", label="3 · Route decided",
         method="DecisionEngine.route_query()",
         activity="1.3",
         note="One LLM call picks a single specialist: knowledge_agent or customer_service_agent."),
    dict(key="knowledge", label="4 · Knowledge Agent",
         method="KnowledgeAgent.handle() -> Bootcamp 1 agent",
         activity="1.2",
         note="Policy / product questions: retrieves from the knowledge base and writes a cited answer."),
    dict(key="cs", label="4 · Customer Service Agent",
         method="CustomerServiceAgent.handle()",
         activity="2.2",
         note="Anything that needs this customer's data or an action on their behalf."),
    dict(key="select", label="4a · Action selected",
         method="DecisionEngine.select_action()",
         activity="2.3",
         note="LLM function-calling returns a structured {tool_name, parameters}."),
    dict(key="tool", label="4b · Tool executed",
         method="ToolRegistry.execute()  (wrapped by with_retry)",
         activity="2.1 / 3.2",
         note="Resolves the tool name to a function and calls it; transient failures are retried."),
    dict(key="service", label="4c · Enterprise service",
         method="src/services/*.py",
         activity="2.2",
         note="Reads customer_profiles / transaction_records, or opens a service request."),
    dict(key="validate", label="5 · Response validated",
         method="ResponseValidator.validate()",
         activity="3.3",
         note="Confirms the reply has the required fields and non-empty text before it ships."),
    dict(key="session_out", label="6 · Turn recorded",
         method="SessionManager.update_context() -> add_turn()",
         activity="3.1",
         note="Route and reply are saved back to the session for the next turn."),
    dict(key="done", label="7 · Response returned",
         method="-> back to this portal",
         activity="provided",
         note="You see the answer above, tagged with the route it took."),
]

# Maps each stub's NotImplementedError message to the pipeline stage it belongs
# to, so a failed run highlights exactly where it stopped.
ERROR_TO_STAGE = {
    "Turn coordination not implemented": "entry",
    "Adding a conversation turn not implemented": "session_in",
    "Recent history lookup not implemented": "session_in",
    "Updating session context not implemented": "session_out",
    "Query routing not implemented": "route",
    "Knowledge agent handling not implemented": "knowledge",
    "Customer service handling not implemented": "cs",
    "Action selection not implemented": "select",
    "Tool registration not implemented": "tool",
    "Tool lookup not implemented": "tool",
    "Tool execution not implemented": "tool",
    "Retry wrapper not implemented": "tool",
    "Customer profile lookup not implemented": "service",
    "Transaction history lookup not implemented": "service",
    "Service request creation not implemented": "service",
    "Response validation not implemented": "validate",
}

_KNOWLEDGE_BRANCH = {"knowledge"}
_SERVICE_BRANCH = {"cs", "select", "tool", "service"}
_LABEL_BY_KEY = {s["key"]: s["label"] for s in PIPELINE}
_ACTIVITY_BY_KEY = {s["key"]: s["activity"] for s in PIPELINE}

_STAGE_STYLE = {
    #            text       background                 icon
    "done":    ("#2e7d32", "rgba(46,125,50,0.10)",   "&#10003;"),
    "stopped": ("#c62828", "rgba(198,40,40,0.12)",   "&#9632;"),
    "skipped": ("#9e9e9e", "rgba(158,158,158,0.08)", "&#8722;"),
    "pending": ("#607d8b", "transparent",            "&#9675;"),
}


def _stage_row_html(stage: dict, state: str) -> str:
    color, bg, icon = _STAGE_STYLE.get(state, _STAGE_STYLE["pending"])
    indent = "margin-left:1.6rem;" if stage["key"] in ("select", "tool", "service") else ""
    tag = ""
    if state == "stopped":
        tag = (f"<span style='margin-left:.4rem;font-size:.72rem;font-weight:700;color:{color};"
               f"border:1px solid {color};border-radius:.8rem;padding:0 .45rem;'>"
               f"you are here &mdash; implement Activity {stage['activity']}</span>")
    elif state == "skipped":
        tag = "<span style='margin-left:.4rem;font-size:.72rem;color:#9e9e9e;'>not used for this route</span>"
    act = "" if stage["activity"] in ("provided",) else f" &middot; Activity {stage['activity']}"
    return (
        f"<div style='display:flex;gap:.55rem;align-items:flex-start;{indent}"
        f"padding:.45rem .65rem;margin-bottom:.32rem;border:1px solid {color}44;"
        f"border-left:3px solid {color};border-radius:6px;background:{bg};'>"
        f"<span style='color:{color};font-weight:700;line-height:1.4;'>{icon}</span>"
        f"<div style='flex:1;min-width:0;'>"
        f"<div style='font-weight:600;'>{stage['label']}{tag}</div>"
        f"<div style='font-family:ui-monospace,SFMono-Regular,Consolas,monospace;"
        f"font-size:.78rem;opacity:.85;word-break:break-word;'>{stage['method']}</div>"
        f"<div style='font-size:.8rem;opacity:.72;'>{stage['note']}"
        f"<span style='opacity:.6;'>{act}</span></div>"
        f"</div></div>"
    )


def render_pipeline(states: dict, caption: str = "") -> None:
    """Render the pipeline as a vertical list of stage cards coloured by state."""
    if caption:
        st.markdown(
            f"<div style='font-size:.86rem;opacity:.8;margin:.2rem 0 .5rem;'>{caption}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "".join(_stage_row_html(s, states.get(s["key"], "pending")) for s in PIPELINE),
        unsafe_allow_html=True,
    )


def neutral_pipeline_states() -> dict:
    """All stages pending - the 'map' view shown before any query runs."""
    return {s["key"]: "pending" for s in PIPELINE}


def pipeline_states_from_response(resp: dict) -> tuple:
    """Work out each stage's state from a get_platform_response() result.
    Returns (states, caption)."""
    order = [s["key"] for s in PIPELINE]
    states = neutral_pipeline_states()
    route = resp.get("route")
    err = resp.get("pipeline_error")

    if route == "DEMO_MODE":
        return states, "Demo Mode - click <b>Initialize Platform</b> in the sidebar to run the real pipeline."

    stop_key = None
    if err:
        for msg, key in ERROR_TO_STAGE.items():
            if msg in err:
                stop_key = key
                break

    if stop_key is not None:
        idx = order.index(stop_key)
        for k in order[:idx]:
            states[k] = "done"
        states[stop_key] = "stopped"
        caption = (f"Stopped at <b>{_LABEL_BY_KEY[stop_key]}</b> &mdash; implement "
                   f"<b>Activity {_ACTIVITY_BY_KEY[stop_key]}</b>, then ask again.")
    elif err:
        caption = f"The platform raised a runtime error (not a missing activity): {err}"
    else:
        for k in order:
            states[k] = "done"
        caption = "Completed - every stage ran."

    # Grey out whichever specialist branch this turn did not use.
    if route == "knowledge_agent":
        for k in _SERVICE_BRANCH:
            if states[k] in ("pending", "done"):
                states[k] = "skipped"
        caption = "Routed to <b>Knowledge Agent</b>. " + caption
    elif route == "customer_service_agent":
        if states["knowledge"] in ("pending", "done"):
            states["knowledge"] = "skipped"
        if stop_key is None and not err and not resp.get("tool_used"):
            states["select"] = "done"
            states["tool"] = "skipped"
            states["service"] = "skipped"
            caption += " No tool was needed for this query."
        caption = "Routed to <b>Customer Service Agent</b>. " + caption

    return states, caption

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "coordinator_initialized" not in st.session_state:
    st.session_state.coordinator_initialized = False
if "portal_session_id" not in st.session_state:
    # One session_id per browser session, so SessionManager (Activity 3.1)
    # accumulates conversation context across turns for this visitor.
    st.session_state.portal_session_id = str(uuid.uuid4())


def initialize_coordinator():
    """Initialize the real Coordinator Agent, wiring the whole platform together."""
    try:
        from src.agents.coordinator_agent import CoordinatorAgent
        st.session_state.coordinator = CoordinatorAgent()
        st.session_state.coordinator_initialized = True
        return True
    except Exception as e:
        logger.error(f"Coordinator initialization failed: {e}")
        st.session_state.coordinator_initialized = False
        return False


DEMO_RESPONSE = {
    "response": """Thank you for your query. The Enterprise Customer Service Operations Platform is currently being configured.

Once implemented, I will be able to:
- Answer questions about bank accounts, cards, loans, and services (routed to the Knowledge Agent)
- Look up a customer's profile, recent transactions, or open a service request (routed to the Customer Service Agent)
- Remember context across turns in this conversation

**Note:** This is a demonstration interface. Complete the Guided Project Workbook activities, then click **Initialize Platform** in the sidebar to activate full functionality.""",
    "source": "demo",
    "route": "DEMO_MODE",
}


def get_platform_response(query: str, customer_id: str) -> dict:
    """Get a response from the real Coordinator Agent, falling back to a
    demo message if it isn't initialized yet, and to a guided message if a
    downstream activity hasn't been implemented."""
    if not st.session_state.get("coordinator_initialized") or "coordinator" not in st.session_state:
        return DEMO_RESPONSE

    try:
        result = st.session_state.coordinator.handle_turn(
            session_id=st.session_state.portal_session_id,
            query=query,
            customer_id=customer_id or None,
        )
        return {
            "response": result.get("response") or "I wasn't able to generate a response for that query.",
            "citations": result.get("citations", []),
            "route": result.get("route"),
            "tool_used": result.get("tool_used"),
        }
    except NotImplementedError as e:
        return {
            "response": f"⚠️ This capability hasn't been implemented yet: **{e}**\n\n"
                        "Complete the corresponding activity in the Guided Project Workbook, then try again. "
                        "See **Behind the scenes** below for exactly where the query stopped.",
            "citations": [],
            "route": "NOT_IMPLEMENTED",
            "tool_used": None,
            "pipeline_error": str(e),
        }
    except Exception as e:
        logger.error(f"Coordinator execution error: {e}")
        return {
            "response": f"⚠️ The platform raised an error while processing your query: {e}",
            "citations": [],
            "route": "ERROR",
            "tool_used": None,
            "pipeline_error": str(e),
        }


def display_message(role: str, content: str, citations: list = None, route: str = None, tool_used: str = None):
    """Display a chat message."""
    css_class = "user-message" if role == "user" else "agent-message"
    icon = "👤" if role == "user" else "🤖"

    if role == "agent" and route in ("knowledge_agent", "customer_service_agent"):
        badge_class = "route-knowledge" if route == "knowledge_agent" else "route-service"
        badge_label = "📚 Knowledge Agent" if route == "knowledge_agent" else "🛠️ Customer Service Agent"
        st.markdown(f'<span class="route-badge {badge_class}">{badge_label}</span>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{icon} {role.title()}:</strong><br/>
        {content}
    </div>
    """, unsafe_allow_html=True)

    if citations:
        st.markdown(f'<div class="citation">📚 Sources: {", ".join(citations)}</div>',
                    unsafe_allow_html=True)
    if tool_used:
        st.markdown(f'<div class="citation">🛠️ Action taken: {tool_used}</div>',
                    unsafe_allow_html=True)


# Main UI
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<p class="main-header">🏦 Enterprise Customer Service Operations Portal</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Agent AI Banking Assistant</p>',
                unsafe_allow_html=True)

with col2:
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = []
        st.session_state.pop("last_response_meta", None)
        st.rerun()

# Sidebar
with st.sidebar:
    st.header("📋 Platform Information")

    if st.session_state.coordinator_initialized:
        st.success("✅ Platform Active")
    else:
        st.warning("⚠️ Demo Mode")
        if st.button("Initialize Platform"):
            if initialize_coordinator():
                st.success("Platform initialized!")
            else:
                st.error("Initialization failed. Implement the platform's modules first.")

    st.markdown("---")

    st.subheader("👤 Customer Context")
    customer_id = st.text_input(
        "Customer ID (optional)",
        value=st.session_state.get("customer_id", ""),
        placeholder="e.g. CUST-1001",
        help="Simulates a logged-in customer. Try CUST-1001 through CUST-1005 "
             "(see data/business_data/customer_profiles.json)."
    )
    st.session_state.customer_id = customer_id

    st.markdown("---")

    st.subheader("🎯 Capabilities")
    st.markdown("""
    - **Coordinator Agent**: routes each turn to one sub-agent
    - **Knowledge Agent**: policy/product Q&A (wraps Bootcamp 1's agent)
    - **Customer Service Agent**: profile lookup, transactions, service requests
    - **Session Memory**: context carried across turns
    """)

    st.markdown("---")

    st.subheader("💡 Example Queries")
    example_queries = [
        "What documents do I need to open a savings account?",
        "How do I report a lost debit card?",
        "What is my account profile?",
        "Show me my recent transactions",
        "I need to block my card, please open a request",
    ]

    for i, example in enumerate(example_queries):
        if st.button(f"📝 {example[:40]}...", key=f"example_{i}"):
            st.session_state.temp_query = example

    st.markdown("---")

    st.subheader("📊 Session Stats")
    st.metric("Queries", len([m for m in st.session_state.messages if m["role"] == "user"]))
    st.metric("Responses", len([m for m in st.session_state.messages if m["role"] == "agent"]))

# Main chat area
st.markdown("### 💬 Conversation")

# Always-available map of what handle_turn() does with a query. Expanded until
# the learner has run something, then it collapses to make room for the chat.
with st.expander("🧭 How a query is processed — the pipeline you're building",
                 expanded=not st.session_state.messages):
    st.caption(
        "Each step below is one workbook activity. Submit a query and the "
        "**Behind the scenes** panel fills these in with what actually ran — green "
        "up to the first stage that still raises `NotImplementedError`."
    )
    render_pipeline(neutral_pipeline_states())

for message in st.session_state.messages:
    display_message(
        message["role"],
        message["content"],
        message.get("citations"),
        message.get("route"),
        message.get("tool_used"),
    )

# Live trace of the most recent query: which route it took and where it stopped.
if st.session_state.get("last_response_meta"):
    _states, _caption = pipeline_states_from_response(st.session_state.last_response_meta)
    with st.expander("🔍 Behind the scenes — how your last query was processed", expanded=True):
        render_pipeline(_states, _caption)

st.markdown("---")

query_input = st.text_input(
    "Ask me anything about banking services:",
    value=st.session_state.get("temp_query", ""),
    placeholder="E.g., What are the KYC requirements for opening an account?",
    key="query_input"
)

col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    submit_button = st.button("🚀 Submit", type="primary", use_container_width=True)

with col2:
    clear_button = st.button("🗑️ Clear Input", use_container_width=True)

if clear_button:
    if "temp_query" in st.session_state:
        del st.session_state.temp_query
    st.rerun()

if submit_button and query_input:
    validation_error = validate_query(query_input)
    if validation_error:
        st.error(f"❌ {validation_error}")
    else:
        sanitized_query = sanitize_input(query_input)
        st.session_state.messages.append({
            "role": "user",
            "content": sanitized_query
        })

        with st.spinner("🤔 Thinking..."):
            try:
                response_data = get_platform_response(sanitized_query, st.session_state.get("customer_id", ""))
                st.session_state.last_response_meta = response_data

                st.session_state.messages.append({
                    "role": "agent",
                    "content": response_data["response"],
                    "citations": response_data.get("citations", []),
                    "route": response_data.get("route"),
                    "tool_used": response_data.get("tool_used"),
                })

                if "temp_query" in st.session_state:
                    del st.session_state.temp_query

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Query processing error: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.9rem;'>
    Enterprise Customer Service Operations Platform | Bootcamp 2 |
    <a href='#' style='color: #1f4788;'>Documentation</a> |
    <a href='#' style='color: #1f4788;'>Support</a>
</div>
""", unsafe_allow_html=True)
