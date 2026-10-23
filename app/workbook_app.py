"""
Guided Project Workbook: interactive Streamlit runner.

The single guided path through the lab: edit the actual src/ files in your own
IDE, then run each activity's validation against them via a fresh subprocess
(so results always reflect exactly what's saved on disk, with no
stale-import/kernel-state surprises). Every script below is self-contained per
activity (it rebuilds any earlier-activity object it needs), so activities can
be run in any order.
"""
import ast
import os
import subprocess
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
# override=True: load_dotenv() otherwise refuses to replace an env var that's
# already set in the shell, so a stray OPENAI_API_KEY left over from some
# other project (or a global shell profile export) would silently shadow
# this project's own .env with no error, just a confusing wrong-key failure.
load_dotenv(PROJECT_ROOT / ".env", override=True)

st.set_page_config(
    page_title="Guided Project Workbook",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Streamlit's floating top toolbar (Deploy button, hamburger menu) is
       position:absolute with a very high z-index, so it renders on top of
       page content rather than pushing it down. 4.5rem clears it with room
       to spare across the Streamlit versions this project has run on. */
    .block-container {padding-top: 4.5rem;}
    .hero-banner {
        background: linear-gradient(120deg, #0b2545 0%, #13315c 35%, #1f6f78 70%, #13315c 100%);
        background-size: 300% 300%;
        animation: heroShift 14s ease-in-out infinite;
        border-radius: 14px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 18px rgba(11, 37, 69, 0.25);
    }
    @keyframes heroShift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    @media (prefers-reduced-motion: reduce) {
        .hero-banner {animation: none;}
    }
    .hero-title {font-size: 1.7rem; font-weight: 700; color: #ffffff; margin: 0;}
    .hero-subtitle {font-size: 0.95rem; color: #cfe3ea; margin-top: 0.3rem;}
    textarea {font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace !important;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Animated diagrams (Overview → What Makes This "Multi-Agent" / Solution
# Architecture tabs): the same coordination flow every activity implements a
# piece of, drawn as a live diagram instead of static ASCII art. Pure inline
# SVG + CSS, no JS or external assets, so it works the same in the sandboxed
# preview as anywhere else Streamlit renders it.
# ---------------------------------------------------------------------------

# Shared by every diagram below: one CSS block, reused per <svg> so each
# stays a single self-contained string for components.html (its own iframe,
# so identical class names across diagrams never collide).
WF_STYLE_BLOCK = """
<style>
    html, body {margin: 0; padding: 0; background: #ffffff;}
    .wf-line {
        stroke: #1f6f78; stroke-width: 2.5; fill: none;
        stroke-dasharray: 6 7; animation: wf-dash 1.1s linear infinite;
    }
    .wf-line-dashed {
        stroke: #4a5a6a; stroke-width: 1.5; fill: none; stroke-dasharray: 4 4;
    }
    @keyframes wf-dash { to { stroke-dashoffset: -26; } }
    .wf-node rect {
        fill: #eef3f6; stroke: #0b2545; stroke-width: 1.5; rx: 8;
        animation: wf-pulse 3.2s ease-in-out infinite;
    }
    .wf-node.wf-cross rect {
        fill: #f6f1e6; stroke: #93590b; stroke-dasharray: 5 4; animation: none;
    }
    /* Deliberately inert: used for the "single agent" side of the
       single-vs-multi-agent comparison, so the contrast with the pulsing,
       branching multi-agent side is visual, not just textual: one is a
       static pipe, the other is a live, coordinated system. */
    .wf-node.wf-static rect { fill: #f0f0f0; stroke: #8a8a8a; animation: none; }
    .wf-node.wf-static text { fill: #5a5a5a; }
    .wf-line-static {
        stroke: #9a9a9a; stroke-width: 2; fill: none;
    }
    .wf-node text { fill: #0b2545; font: 600 13px sans-serif; text-anchor: middle; }
    .wf-node .wf-sub { font: 400 11px sans-serif; fill: #4a5a6a; }
    .wf-label { font: 500 11px sans-serif; fill: #4a5a6a; text-anchor: middle; }
    .wf-section { font: 700 14px sans-serif; fill: #0b2545; }
    @keyframes wf-pulse {
        0%, 100% { filter: drop-shadow(0 0 0 rgba(31,111,120,0)); }
        50% { filter: drop-shadow(0 0 6px rgba(31,111,120,0.55)); }
    }
    @media (prefers-reduced-motion: reduce) {
        .wf-line { animation: none; }
        .wf-node rect { animation: none; }
    }
</style>
"""

# Single agent (Bootcamp 1) vs. multi-agent (Bootcamp 2): the comparison from
# Section 6, "Introduction to Multi-Agent Systems."
MULTI_AGENT_DIAGRAM_SVG = WF_STYLE_BLOCK + """
<svg viewBox="0 0 800 460" style="width:100%; height:auto; max-width:760px; display:block; margin:0.5rem auto;">
    <defs>
        <marker id="wf-arrow3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#1f6f78"/>
        </marker>
        <marker id="wf-arrow-static" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#9a9a9a"/>
        </marker>
    </defs>

    <text class="wf-section" x="20" y="20">A single agent (Bootcamp 1): one workflow does everything</text>
    <path class="wf-line-static" marker-end="url(#wf-arrow-static)" d="M180,65 L224,65"/>
    <path class="wf-line-static" marker-end="url(#wf-arrow-static)" d="M490,65 L534,65"/>
    <g class="wf-node wf-static">
        <rect x="40" y="45" width="140" height="40"/>
        <text x="110" y="70">Query</text>
    </g>
    <g class="wf-node wf-static">
        <rect x="230" y="45" width="260" height="40"/>
        <text x="360" y="66">CustomerOperationsAgent</text>
        <text class="wf-sub" x="360" y="80">classify, retrieve, tool, respond</text>
    </g>
    <g class="wf-node wf-static">
        <rect x="540" y="45" width="140" height="40"/>
        <text x="610" y="70">Response</text>
    </g>
    <text class="wf-label" x="400" y="108">One classifier-and-responder, doing every kind of work</text>

    <text class="wf-section" x="20" y="140">A multi-agent system (Bootcamp 2): specialists, coordinated</text>

    <path class="wf-line" marker-end="url(#wf-arrow3)" d="M400,195 L400,214"/>
    <path class="wf-line" marker-end="url(#wf-arrow3)" d="M340,265 L230,304"/>
    <path class="wf-line" marker-end="url(#wf-arrow3)" d="M460,265 L560,304"/>
    <path class="wf-line" marker-end="url(#wf-arrow3)" d="M230,355 L340,399"/>
    <path class="wf-line" marker-end="url(#wf-arrow3)" d="M560,355 L460,399"/>

    <g class="wf-node" style="animation-delay:0s">
        <rect x="320" y="155" width="160" height="40"/>
        <text x="400" y="180">Query</text>
    </g>
    <g class="wf-node" style="animation-delay:0.3s">
        <rect x="210" y="215" width="380" height="50"/>
        <text x="400" y="238">Coordinator</text>
        <text class="wf-sub" x="400" y="254">which specialist owns this turn?</text>
    </g>
    <g class="wf-node" style="animation-delay:0.6s">
        <rect x="90" y="305" width="260" height="50"/>
        <text x="220" y="326">Knowledge Agent</text>
        <text class="wf-sub" x="220" y="342">wraps the Bootcamp 1 agent, unchanged</text>
    </g>
    <g class="wf-node" style="animation-delay:0.6s">
        <rect x="450" y="305" width="270" height="50"/>
        <text x="585" y="326">Customer Service Agent</text>
        <text class="wf-sub" x="585" y="342">enterprise services via function calling</text>
    </g>
    <g class="wf-node" style="animation-delay:0.9s">
        <rect x="20" y="400" width="760" height="50"/>
        <text x="400" y="430">Response</text>
    </g>
</svg>
"""

# Layered architecture (Section 7): app/ -> Coordinator -> Knowledge Agent /
# Customer Service Agent -> Decision -> Tool Access -> Enterprise Services,
# with the cross-cutting layer every stage depends on.
ARCHITECTURE_DIAGRAM_SVG = WF_STYLE_BLOCK + """
<svg viewBox="0 0 800 640" style="width:100%; height:auto; max-width:720px; display:block; margin:0.5rem auto;">
    <defs>
        <marker id="wf-arrow2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#1f6f78"/>
        </marker>
    </defs>

    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M400,60 L400,94"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M340,150 L200,194"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M460,150 L590,194"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M590,255 L590,289"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M590,345 L590,379"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M590,435 L590,469"/>

    <g class="wf-node" style="animation-delay:0s">
        <rect x="280" y="10" width="240" height="50"/>
        <text x="400" y="32">Presentation</text>
        <text class="wf-sub" x="400" y="48">app/customer_portal.py</text>
    </g>
    <g class="wf-node" style="animation-delay:0.3s">
        <rect x="210" y="100" width="380" height="55"/>
        <text x="400" y="124">Orchestration</text>
        <text class="wf-sub" x="400" y="140">CoordinatorAgent: src/agents/coordinator_agent.py</text>
    </g>
    <g class="wf-node" style="animation-delay:0.6s">
        <rect x="40" y="200" width="320" height="60"/>
        <text x="200" y="224">Knowledge Agent</text>
        <text class="wf-sub" x="200" y="240">wraps Bootcamp 1: src/agents/knowledge_agent.py</text>
        <text class="wf-sub" x="200" y="253">(a leaf: no decision/tool layer below it)</text>
    </g>
    <g class="wf-node" style="animation-delay:0.6s">
        <rect x="420" y="200" width="340" height="60"/>
        <text x="590" y="224">Customer Service Agent</text>
        <text class="wf-sub" x="590" y="240">src/agents/customer_service_agent.py</text>
    </g>
    <g class="wf-node" style="animation-delay:0.9s">
        <rect x="460" y="295" width="260" height="55"/>
        <text x="590" y="319">Decision Layer</text>
        <text class="wf-sub" x="590" y="335">DecisionEngine: src/core/decision_engine.py</text>
    </g>
    <g class="wf-node" style="animation-delay:1.2s">
        <rect x="460" y="385" width="260" height="55"/>
        <text x="590" y="409">Tool Access Layer</text>
        <text class="wf-sub" x="590" y="425">ToolRegistry: src/tools/tool_registry.py</text>
    </g>
    <g class="wf-node" style="animation-delay:1.5s">
        <rect x="420" y="475" width="340" height="55"/>
        <text x="590" y="499">Enterprise Services Layer</text>
        <text class="wf-sub" x="590" y="515">src/services/*.py: profile, transactions, requests</text>
    </g>
    <g class="wf-node wf-cross">
        <rect x="40" y="565" width="720" height="55"/>
        <text x="400" y="588">Cross-cutting: used by every layer above</text>
        <text class="wf-sub" x="400" y="604">SessionManager (src/core/session_manager.py) · config/*.yaml · src/utils/ · data/</text>
    </g>
</svg>
"""

# Orchestration flow (Section 7's second diagram): the same routing flow,
# this time with each stage mapped to the activity that implements it.
ORCHESTRATION_FLOW_SVG = WF_STYLE_BLOCK + """
<svg viewBox="0 0 800 610" style="width:100%; height:auto; max-width:760px; display:block; margin:0.5rem auto;">
    <defs>
        <marker id="wf-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#1f6f78"/>
        </marker>
    </defs>

    <path class="wf-line" marker-end="url(#wf-arrow)" d="M400,50 L400,84"/>
    <path class="wf-line" marker-end="url(#wf-arrow)" d="M400,140 L400,174"/>
    <path class="wf-line" marker-end="url(#wf-arrow)" d="M400,230 L180,264"/>
    <path class="wf-line" marker-end="url(#wf-arrow)" d="M400,230 L560,264"/>
    <path class="wf-line" marker-end="url(#wf-arrow)" d="M560,320 L560,354"/>
    <path class="wf-line" marker-end="url(#wf-arrow)" d="M180,320 L340,449"/>
    <path class="wf-line" marker-end="url(#wf-arrow)" d="M560,410 L420,449"/>
    <path class="wf-line" marker-end="url(#wf-arrow)" d="M400,500 L400,534"/>

    <g class="wf-node" style="animation-delay:0s">
        <rect x="320" y="10" width="160" height="40"/>
        <text x="400" y="32">Customer Query</text>
        <text class="wf-sub" x="400" y="45">+ session_id</text>
    </g>
    <g class="wf-node" style="animation-delay:0.3s">
        <rect x="250" y="90" width="300" height="50"/>
        <text x="400" y="112">handle_turn()</text>
        <text class="wf-sub" x="400" y="128">Activity 1.2 · CoordinatorAgent</text>
    </g>
    <g class="wf-node" style="animation-delay:0.6s">
        <rect x="270" y="180" width="260" height="50"/>
        <text x="400" y="202">route_query()</text>
        <text class="wf-sub" x="400" y="218">Activity 1.3 · DecisionEngine</text>
    </g>

    <text class="wf-label" x="180" y="256">knowledge_agent</text>
    <text class="wf-label" x="580" y="256">customer_service_agent</text>

    <g class="wf-node" style="animation-delay:0.9s">
        <rect x="40" y="270" width="280" height="50"/>
        <text x="180" y="292">KnowledgeAgent.handle()</text>
        <text class="wf-sub" x="180" y="308">Activity 1.2, delegates to Bootcamp 1</text>
    </g>
    <g class="wf-node" style="animation-delay:0.9s">
        <rect x="420" y="270" width="280" height="50"/>
        <text x="560" y="292">select_action()</text>
        <text class="wf-sub" x="560" y="308">Activity 2.3 · DecisionEngine</text>
    </g>
    <g class="wf-node" style="animation-delay:1.2s">
        <rect x="420" y="360" width="280" height="50"/>
        <text x="560" y="382">ToolRegistry.execute()</text>
        <text class="wf-sub" x="560" y="398">Activity 2.1/2.2, retried by Activity 3.2</text>
    </g>

    <g class="wf-node" style="animation-delay:1.5s">
        <rect x="270" y="450" width="260" height="50"/>
        <text x="400" y="472">ResponseValidator.validate()</text>
        <text class="wf-sub" x="400" y="488">Activity 3.3</text>
    </g>
    <g class="wf-node" style="animation-delay:1.8s">
        <rect x="20" y="540" width="760" height="55"/>
        <text x="400" y="562">Response recorded in the session</text>
        <text class="wf-sub" x="400" y="578">Activity 3.1 · SessionManager, then returned to the executive</text>
    </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Execution + file helpers
# ---------------------------------------------------------------------------

REFERENCE_PATH_PREFIX = """import sys as _sys
_sys.path.insert(0, "reference_solution")
"""


def run_snippet(code: str, timeout: int = 180, use_reference: bool = False) -> dict:
    """Run `code` in a fresh subprocess using this same interpreter, from the
    project root, so every run picks up exactly what's saved on disk right
    now, no module-cache or notebook-kernel staleness possible.

    With use_reference=True, `reference_solution` is inserted ahead of the
    project root on sys.path, so every `from src...` import in the script
    resolves to reference_solution/src instead of the participant's own
    src/, letting a stuck learner see the completed solution actually run,
    not just read its code. `config/` and `data/` paths are untouched since
    cwd stays the project root, and reference_solution/src mirrors src/'s
    package layout exactly, so no other code path needs to change."""
    code_to_run = (REFERENCE_PATH_PREFIX + code) if use_reference else code
    env = os.environ.copy()
    # Windows defaults a child process's stdout/stderr to the system codepage
    # (cp1252), which crashes on the emoji every activity script prints
    # ([WARN], ✓, ...). Force UTF-8 for the subprocess itself.
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        result = subprocess.run(
            [sys.executable, "-c", code_to_run],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode, "timed_out": False}
    except subprocess.TimeoutExpired as e:
        return {"stdout": e.stdout or "", "stderr": e.stderr or "", "returncode": None, "timed_out": True}


def classify_run(result: dict) -> str:
    if result["timed_out"]:
        return "error"
    if result["returncode"] != 0:
        return "error"
    combined = result["stdout"] + result["stderr"]
    if "NotImplementedError" in combined or "[WARN]" in combined:
        return "warn"
    return "pass"


def read_file(rel_path: str) -> str:
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        return f"# File not found: {rel_path}"
    return path.read_text(encoding="utf-8-sig")


if "activity_status" not in st.session_state:
    st.session_state.activity_status = {}
if "activity_output" not in st.session_state:
    st.session_state.activity_output = {}


# ---------------------------------------------------------------------------
# Activity content: 9 activities across 3 phases, mirroring the guided lab
# ---------------------------------------------------------------------------

ACTIVITIES = [
    dict(
        id="1.1", phase=1, title="Explore the Enterprise Operations Platform",
        module="*No module to implement: orientation activity*",
        business_context="""You're extending a real, partially-built enterprise codebase, not starting from a blank file. Before writing anything, you need to know what's already complete (the Bootcamp 1 agent, the knowledge base, the LLM/utils infrastructure) versus what you're about to build (the coordination layer), otherwise it's easy to duplicate work that already exists or build something inconsistent with it.""",
        objective="Ground the layered architecture from the Solution Architecture tab in the actual repository, then confirm the starter application is running in demo mode.",
        instructions="""1. Skim the project tree and match each folder to the layer it belongs to: `src/agents/` and `src/core/` (Orchestration/Decision layers, you'll implement these), `src/tools/` and `src/services/` (Tool Access/Enterprise Services layers, you'll implement these), `src/bootcamp1_agent/` (your completed Bootcamp 1 agent, vendored in as provided infrastructure, do not edit it), `src/llm/`, `src/knowledge/`, `src/utils/` (already complete), `app/` (Presentation layer, already complete), `reference_solution/` (instructor/self-check only, avoid looking unless you're stuck).
2. Open `config/agent_config.yaml` and `config/tools_config.yaml` and skim them: you'll be reading from both throughout this lab instead of hardcoding routing rules or tool definitions.
3. In a separate terminal, run `streamlit run app/customer_portal.py` and submit a query. You should see a "Demo Mode" placeholder response: that's expected, since the platform hasn't been implemented yet.
4. Scroll down and click **Run Activity 1.1** below to get a live orientation summary of the codebase you're extending: this is the same run-and-check pattern you'll use to validate every activity in this lab.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to summarize what a given `src/` module is responsible for before you start implementing it: it's a fast way to build context on unfamiliar code.",
        files=[],
        reference_only_files=["config/agent_config.yaml", "config/tools_config.yaml"],
        milestone="You can explain the platform's architecture and locate every module you'll implement in this lab.",
        validation="""Confirm that the scan lists 8 modules with TODO markers and stub methods: the three `src/agents/*.py` files, `src/core/decision_engine.py`, `src/core/session_manager.py`, `src/tools/tool_registry.py`, `src/utils/retry.py`, and `src/utils/response_validator.py` (`src/services/*.py` may or may not show yet depending on how your starter was generated; either is fine). That maps directly onto the Solution Architecture tab's layers: Orchestration/Reasoning (Phase 1), Decision/Tool Access/Enterprise Services (Phase 2), Session/Resilience/Validation (Phase 3).""",
        pass_label="✓ Orientation scan complete: nothing to implement here yet",
        script="""from pathlib import Path
import yaml

def scan_todos(base="src"):
    summary = []
    for py_file in sorted(Path(base).rglob("*.py")):
        if "bootcamp1_agent" in py_file.parts:
            continue  # vendored, provided infrastructure - not part of this lab's scan
        text = py_file.read_text(encoding="utf-8")
        todo_count = text.count("TODO")
        raises = text.count("raise NotImplementedError")
        if todo_count or raises:
            summary.append((str(py_file), todo_count, raises))
    return summary

todos = scan_todos()
print(f"{'Module':<45}{'TODO markers':<15}{'Stub methods'}")
print("-" * 70)
for path, todo_count, raises in todos:
    print(f"{path:<45}{todo_count:<15}{raises}")

print(f"\\n✓ {len(todos)} modules contain implementation work for you across this lab.")
print("  src/bootcamp1_agent/, src/llm/, src/knowledge/, src/utils/ are already complete - use them as-is.")

agent_config = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
tools_config = yaml.safe_load(open("config/tools_config.yaml", encoding="utf-8"))
print(f"\\n✓ Coordinator can route to: {agent_config['coordination']['routes']}")
print(f"✓ Enterprise service tools declared in config/tools_config.yaml: {[t['name'] for t in tools_config['tools']]}")
""",
    ),
    dict(
        id="1.2", phase=1, title="Implement the Coordinator Agent",
        module="`src/agents/coordinator_agent.py` (and `src/agents/knowledge_agent.py`)",
        business_context="""Every customer turn needs to land with the right specialist without the customer having to say which one they want. That's the Coordinator's job: look at the request, decide who owns it, delegate, and keep track of the conversation so far, the same responsibility Bootcamp 1's `route_decision` had, just one level up, choosing between agents instead of between workflow nodes.""",
        objective="Implement `CoordinatorAgent.handle_turn()` so it routes a query, delegates to the chosen sub-agent, and records the turn in the session, and implement `KnowledgeAgent.handle()`, the simplest of the two sub-agents it delegates to.",
        concept_overview="""`CoordinatorAgent.__init__` is already wired for you: it constructs a `DecisionEngine`, a `KnowledgeAgent`, a `CustomerServiceAgent`, a `SessionManager`, and a `ResponseValidator`. None of those constructors make it crash even before you've implemented anything downstream: `DecisionEngine` builds its `ToolRegistry` lazily, and every other constructor here is plumbing only. That means you can build and test the Coordinator's *wiring* right now, even though `route_query()` (Activity 1.3) and the tool-selection path (Activities 2.1-2.3) don't work yet.

`KnowledgeAgent` has no such downstream dependency at all: it only delegates to your already-complete Bootcamp 1 `CustomerOperationsAgent`, so it's fully testable the moment you implement it.""",
        instructions="""1. Implement `KnowledgeAgent.handle()` in `src/agents/knowledge_agent.py`: call `self.agent.run(query)` and translate the returned `AgentState` dict into this platform's shared response shape (see the docstring in the file for the exact keys).
2. Implement `CoordinatorAgent.handle_turn()` in `src/agents/coordinator_agent.py`: look up or create the session, route the query, delegate to the chosen sub-agent, validate the response, record the turn, and return the combined result (see the numbered docstring in the file for the exact steps).""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to explain why constructing `CoordinatorAgent()` doesn't fail even though nothing downstream is implemented yet: the answer is in how its dependencies are wired, not in try/except.",
        files=["src/agents/knowledge_agent.py", "src/agents/coordinator_agent.py"],
        target_methods={
            "src/agents/knowledge_agent.py": ["handle"],
            "src/agents/coordinator_agent.py": ["handle_turn"],
        },
        milestone="The Coordinator Agent is wired to both sub-agents and a session manager, and can already answer knowledge questions directly through the Knowledge Agent.",
        validation="""Confirm that:
- `coordinator` was constructed without raising an exception, with all four dependencies wired to the expected types
- `KnowledgeAgent.handle()` returned a grounded response about savings account documents, with `source="knowledge_agent"`
- The full-turn attempt printed the "not runnable yet" message rather than crashing the cell

Notice what this proves: the Coordinator's *structure* (which sub-agents it owns, how they're wired) is independent of whether every sub-agent's *behaviour* is implemented yet, the same separation Bootcamp 1's compiled-but-unimplemented `StateGraph` demonstrated.""",
        script="""from src.agents.coordinator_agent import CoordinatorAgent

coordinator = CoordinatorAgent()
print(f"✓ CoordinatorAgent constructed successfully: {type(coordinator).__name__}")
print(f"✓ Wired sub-agents: {type(coordinator.knowledge_agent).__name__}, {type(coordinator.customer_service_agent).__name__}")
print(f"✓ Wired decision engine: {type(coordinator.decision_engine).__name__}")
print(f"✓ Wired session manager: {type(coordinator.session_manager).__name__}")

# The Knowledge Agent only depends on the already-complete Bootcamp 1 agent,
# so it's fully testable now, before the Decision Engine (Activity 1.3) or
# the other sub-agent (Activity 2.2) exist.
try:
    result = coordinator.knowledge_agent.handle("What documents do I need to open a savings account?")
    print(f"\\n✓ KnowledgeAgent responded (source={result['source']}):")
    print(result["response"][:300])
except NotImplementedError as e:
    print(f"\\n[WARN] Task 1.2 not yet implemented: {e}")
    print("   Implement KnowledgeAgent.handle() in src/agents/knowledge_agent.py")

# A full conversational turn also needs the Decision Engine (Activity 1.3) to
# route it, so this is expected to raise NotImplementedError until then,
# that's the very next activity, not a bug here.
try:
    turn_result = coordinator.handle_turn("demo-session", "What documents do I need to open a savings account?")
    print(f"\\n✓ Full turn handled - route: {turn_result['route']}")
except NotImplementedError as e:
    print(f"\\n[INFO] A full conversational turn isn't runnable yet: {e}")
    print("   That's expected until Activity 1.3 (and later activities) are complete.")
""",
    ),
    dict(
        id="1.3", phase=1, title="Build the Enterprise Decision Engine",
        module="`src/core/decision_engine.py`",
        business_context="""Once the Coordinator has a query, something needs to decide which specialist owns it. A policy question and "what's my balance" require fundamentally different handling, and that decision needs to be consistent and explainable, not a hardcoded keyword check that breaks the moment phrasing changes.""",
        objective="Implement `DecisionEngine.route_query()`: classify a customer query into exactly one route using the LLM, with a safe fallback when the response can't be parsed.",
        concept_overview="""`route_query()` uses the same classify-with-an-LLM-and-parse-the-result pattern as Bootcamp 1's `classify_intent`, just with a different (and simpler) output shape: a JSON object naming one of two routes instead of one of four intents. `config/prompts.yaml`'s `coordinator_routing_prompt` asks the LLM for exactly that shape. The fallback logic matters here as much as the happy path: an LLM occasionally returns malformed JSON or an unexpected route name, and this method needs to degrade to a sensible default (`config/agent_config.yaml`'s `coordination.default_route`) rather than raise.""",
        instructions="""1. Build the prompt: get `"coordinator_routing_prompt"` from `self.prompt_mgr`, format its `user_template` with `query`.
2. Call `self.llm.generate(...)` and `json.loads()` the result.
3. If parsing fails, or the parsed `"route"` isn't in `self.valid_routes`, fall back to `{"route": self.default_route, "confidence": 0.0, "reasoning": "..."}`.
4. Otherwise return the parsed `{"route", "confidence", "reasoning"}`.

(See the numbered docstring in the file for the exact code shape expected.)""",
        ai_assist="**AI Assist:** Ask your AI coding assistant for a short list of edge cases an LLM-based JSON classifier can fail on: it's a good sanity check on whether your fallback branch actually covers them.",
        files=["src/core/decision_engine.py"],
        target_methods={"src/core/decision_engine.py": ["route_query"]},
        milestone="The platform can classify a customer query and choose which specialized agent should handle it.",
        validation="""Confirm that:
- The first query (a policy question) routes to `knowledge_agent`
- The second query (a personal-data request) routes to `customer_service_agent`
- Each decision includes a non-empty `reasoning` string

The LLM won't always phrase its reasoning identically between runs; that's fine, as long as the routing decision itself is sensible. Try a deliberately ambiguous query (e.g. `"Can you help me?"`) and see which route it falls into: there's no single right answer, but it should still be one of `self.valid_routes`, never something else.""",
        script="""from src.core.decision_engine import DecisionEngine

engine = DecisionEngine()

sample_queries = [
    "What documents do I need to open a savings account?",
    "Can you show me my recent transactions?",
]

for query in sample_queries:
    try:
        decision = engine.route_query(query)
        print(f"Query: {query}")
        print(f"  -> route={decision['route']}  confidence={decision['confidence']:.2f}")
        print(f"     reasoning: {decision['reasoning']}\\n")
    except NotImplementedError as e:
        print(f"[WARN] Task 1.3 not yet implemented: {e}")
        print("   Implement DecisionEngine.route_query() in src/core/decision_engine.py")
        break
""",
    ),
    dict(
        id="2.1", phase=2, title="Configure the Tool Registry",
        module="`src/tools/tool_registry.py`",
        business_context="""The Customer Service Agent needs to call enterprise services by name without hardcoding which Python function backs each one: that indirection is what lets `config/tools_config.yaml` stay the single source of truth for what's available, instead of scattering tool wiring across the codebase.""",
        objective="Implement the registry mechanics: registering a tool, looking one up by name, and executing it. The dynamic config-driven wiring in `__init__`/`_register_from_config` is already done for you.",
        concept_overview="""A tool registry is a `name -> function` map, nothing more exotic. `config/tools_config.yaml` declares three tools; `_register_from_config()` (provided) dynamically imports each one's module and function and calls `self.register(...)`, the method you're about to implement, to store it. `get_tool()` adds one policy decision on top of a plain dict lookup: `config/tools_config.yaml`'s `registry.fail_on_missing_tool` setting controls whether an unregistered name is a hard error or a quiet `None`.""",
        instructions="""1. Implement `register()`: build a `ToolDefinition` from the arguments and store it in `self._tools`, keyed by name.
2. Implement `get_tool()`: look up the tool; if it's missing and `self._fail_on_missing_tool` is `True`, raise `KeyError`.
3. Implement `execute()`: look up the tool via `self.get_tool()`; if it's `None`, return an error dict; otherwise call `tool.function(**kwargs)` and return the result.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant why `list_tools()` and `get_function_schemas()` were left fully implemented for you while `register()`/`get_tool()`/`execute()` weren't: it's a useful check on whether you can articulate what 'mechanical plumbing vs. the actual learning objective' means in your own words.",
        files=["src/tools/tool_registry.py"],
        target_methods={"src/tools/tool_registry.py": ["register", "get_tool", "execute"]},
        milestone="Enterprise services are discoverable and callable by name through a single Tool Registry.",
        validation="""Confirm that:
- All three tools (`get_customer_profile`, `get_recent_transactions`, `create_service_request`) are registered and listed
- The function-calling schemas list the same three names
- Executing `get_customer_profile` either returns real profile data, **or** raises `NotImplementedError` naming the *service* function (`Customer profile lookup not implemented`) rather than the registry itself: either outcome confirms the registry correctly resolved the name and called the right function; only the service's own implementation (Activity 2.2) is still pending.""",
        script="""from src.tools.tool_registry import ToolRegistry

# ToolRegistry's __init__ registers every tool from config/tools_config.yaml
# immediately, so constructing it (not just executing a tool) is itself part
# of this activity's TODO until register() is implemented.
try:
    registry = ToolRegistry()
    registered = set(registry.list_tools())
    expected = {"get_customer_profile", "get_recent_transactions", "create_service_request"}
    print(f"✓ Registered tools: {sorted(registered)}")
    if registered != expected:
        print(f"[WARN] Expected exactly {sorted(expected)}, got {sorted(registered)}")
    print(f"✓ Function-calling schemas: {[s['name'] for s in registry.get_function_schemas()]}")

    try:
        result = registry.execute("get_customer_profile", customer_id="CUST-1001")
        print(f"\\n✓ Executed 'get_customer_profile': {result}")
    except NotImplementedError as e:
        print(f"\\n[WARN] Not yet fully implemented: {e}")
        print("   If this names the service itself (e.g. 'Customer profile lookup'), that's expected here, it's Activity 2.2, next.")
except NotImplementedError as e:
    print(f"[WARN] Task 2.1 not yet implemented: {e}")
    print("   Implement register(), get_tool(), and execute() in src/tools/tool_registry.py")
""",
    ),
    dict(
        id="2.2", phase=2, title="Implement Enterprise Service Integration",
        module="`src/services/*.py` (and `src/agents/customer_service_agent.py`)",
        business_context="""This is where the platform stops being purely conversational and starts touching enterprise data: a customer's profile, their transaction history, and the ability to open a service request on their behalf, the same JSON-file-backed pattern Bootcamp 1's product/branch tools used, just for customer-specific data instead of static catalogs.""",
        objective="Implement the three mock enterprise services, then implement `CustomerServiceAgent.handle()`, which selects and executes one of them per query.",
        instructions="""1. `src/services/customer_profile_service.py`: implement `get_customer_profile()`: search `data/business_data/customer_profiles.json`'s `"customers"` list for a matching `customer_id`; return the not-found shape if none matches.
2. `src/services/transaction_service.py`: implement `get_recent_transactions()`: filter `data/business_data/transaction_records.json`'s `"transactions"` list to the customer, sort by date descending, slice to `limit`.
3. `src/services/service_request_service.py`: implement `create_service_request()`: build a tracking record (request ID, status `"Open"`, timestamp) and append it to the in-memory store.
4. `src/agents/customer_service_agent.py`: implement `handle()`: call `self.decision_engine.select_action()`, and if a tool was selected, execute it via the already-implemented `self._execute_tool()` (retry-wrapped, Activity 3.2) and phrase the result with the already-implemented `self._format_response()`.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to double-check your sort key when implementing `get_recent_transactions()`: sorting date *strings* only gives the right order if every date is in the same `YYYY-MM-DD` format, which this dataset is, but it's worth confirming you understand why.",
        files=[
            "src/services/customer_profile_service.py",
            "src/services/transaction_service.py",
            "src/services/service_request_service.py",
            "src/agents/customer_service_agent.py",
        ],
        target_methods={
            "src/services/customer_profile_service.py": ["get_customer_profile"],
            "src/services/transaction_service.py": ["get_recent_transactions"],
            "src/services/service_request_service.py": ["create_service_request"],
            "src/agents/customer_service_agent.py": ["handle"],
        },
        milestone="The three mock enterprise services return real customer data, and the Customer Service Agent is wired to use them.",
        validation="""Confirm that:
- `get_customer_profile` returns Ananya Rao's profile for `CUST-1001`
- `get_recent_transactions` returns transactions in newest-first order
- `create_service_request` returns a record with `status="Open"` and a `request_id`
- `agent.handle()` either produces a full response, **or** prints the "not fully runnable yet" message; both are correct depending on whether you've already peeked ahead at Activity 2.3""",
        script="""from src.services.customer_profile_service import get_customer_profile
from src.services.transaction_service import get_recent_transactions
from src.services.service_request_service import create_service_request
from src.agents.customer_service_agent import CustomerServiceAgent

try:
    profile = get_customer_profile("CUST-1001")
    print(f"✓ get_customer_profile: {profile}")
    if profile.get("first_name") != "Ananya":
        print(f"[WARN] Expected CUST-1001 to be Ananya Rao, got first_name={profile.get('first_name')!r}")

    txns = get_recent_transactions("CUST-1001", limit=3)
    dates = [t["date"] for t in txns]
    print(f"✓ get_recent_transactions: {len(txns)} results, newest first: {dates[0] if dates else 'n/a'}")
    if dates != sorted(dates, reverse=True):
        print(f"[WARN] Transactions are not sorted newest-first: {dates}")

    request = create_service_request("CUST-1001", "card_block", "Lost debit card")
    print(f"✓ create_service_request: {request}")
    if request.get("status") != "Open" or not request.get("request_id"):
        print(f"[WARN] Expected status='Open' and a non-empty request_id, got {request}")
except NotImplementedError as e:
    print(f"[WARN] Task 2.2 not yet implemented: {e}")
    print("   Implement the service function named above in src/services/")

agent = CustomerServiceAgent()
try:
    result = agent.handle("What is my account profile?", context={"customer_id": "CUST-1001"})
    print(f"\\n✓ CustomerServiceAgent responded: {result['response']}")
except NotImplementedError as e:
    print(f"\\n[INFO] A full CustomerServiceAgent turn isn't runnable yet: {e}")
    print("   This is expected. The remaining pieces are built in later activities:")
    print("   - DecisionEngine.select_action()      -> Activity 2.3")
    print("   - retry wrapper around _execute_tool  -> Activity 3.2")
    print("   The whole turn is exercised end to end in Activity 3.3.")
""",
    ),
    dict(
        id="2.3", phase=2, title="Implement Function Calling and Structured Outputs",
        module="`src/core/decision_engine.py` (extends Activity 1.3)",
        business_context="""Knowing a query needs the Customer Service Agent (Activity 1.3's job) isn't the same as knowing *which* action it needs and with *what* parameters. Rather than parsing that out of free text with regex or a second classification prompt, this activity uses the LLM's native function-calling API: the model itself returns a structured `{name, arguments}` object when it decides a tool applies.""",
        objective="Implement `DecisionEngine.select_action()`, completing the last piece the Customer Service Agent needs to work end to end.",
        concept_overview="""Function calling works by describing your available tools to the LLM (via `tools=[...]`, using the JSON-schema shape `ToolRegistry.get_function_schemas()` already builds from `config/tools_config.yaml`) and letting the API return either normal text or a structured tool call, chosen by the model itself based on the conversation. This is the same idea as Bootcamp 1's `tool_selection_prompt`, except the *parsing* is handled by the OpenAI API rather than by you: no more brittle text parsing of "which tool and what arguments" out of a free-text response.""",
        instructions="""1. Build the system message from `"action_selection_prompt"`, appending `context` (as JSON) if provided.
2. Get `functions = self.tool_registry.get_function_schemas()`.
3. Call `self.llm.client.chat.completions.create(...)` with `tools=[{"type": "function", "function": schema} for schema in functions]` and `tool_choice="auto"`.
4. If `message.tool_calls` is empty, return `{"tool_name": None, "parameters": {}, "reasoning": message.content or "..."}`.
5. Otherwise `json.loads()` the first tool call's `.function.arguments` and return `{"tool_name", "parameters", "reasoning"}`.

(See the numbered docstring in the file for the exact code shape expected.)""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to explain the difference between `tool_choice=\"auto\"` and `tool_choice=\"required\"`, and why `\"auto\"` is the right choice for a query that might not need any tool at all.",
        files=["src/core/decision_engine.py"],
        target_methods={"src/core/decision_engine.py": ["select_action"]},
        milestone="The platform selects and invokes the correct enterprise action via the LLM's native function calling, end to end.",
        validation="""Confirm that:
- `select_action` returns `tool_name="get_customer_profile"` with `parameters={"customer_id": "CUST-1001"}` — that alone is Activity 2.3 done
- The full `CustomerServiceAgent.handle()` turn only runs end to end once **Activity 2.2** (`handle()` itself) and **Activity 3.2** (the retry wrapper on `_execute_tool`) are also complete. Until then the script prints an `[INFO]` line naming what's still pending — that is expected, not a failure.

Try a query that shouldn't need any tool at all (e.g. `"Thanks, that's all for now"`) and confirm `select_action` returns `tool_name=None` instead of forcing a tool call: that's `tool_choice="auto"` working as intended.""",
        script="""from src.core.decision_engine import DecisionEngine
from src.agents.customer_service_agent import CustomerServiceAgent

engine = DecisionEngine()
try:
    action = engine.select_action("Can you pull up my account profile?", context={"customer_id": "CUST-1001"})
    print(f"✓ select_action result: {action}")
    if action.get("tool_name") != "get_customer_profile":
        print(f"[WARN] Expected tool_name='get_customer_profile', got {action.get('tool_name')!r}")
    elif action.get("parameters", {}).get("customer_id") != "CUST-1001":
        print(f"[WARN] Expected parameters.customer_id='CUST-1001', got {action.get('parameters')}")
except NotImplementedError as e:
    print(f"[WARN] Task 2.3 not yet implemented: {e}")
    print("   Implement DecisionEngine.select_action() in src/core/decision_engine.py")

# A full Customer Service Agent turn also needs CustomerServiceAgent.handle()
# (Activity 2.2) and the retry wrapper around _execute_tool (Activity 3.2).
# Until those later activities are done, a NotImplementedError here is expected:
# it names the piece still pending downstream, not a fault in the
# select_action() you just implemented.
agent = CustomerServiceAgent(decision_engine=engine)
try:
    result = agent.handle("Can you pull up my account profile?", context={"customer_id": "CUST-1001"})
    print(f"\\n✓ CustomerServiceAgent full response: {result['response']}")
    print(f"  tool_used={result['tool_used']}")
except NotImplementedError as e:
    print(f"\\n[INFO] A full end-to-end turn isn't runnable yet: {e}")
    print("   This is expected. It will be implemented in later activities:")
    print("   - CustomerServiceAgent.handle()  -> Activity 2.2")
    print("   - retry wrapper around _execute_tool  -> Activity 3.2")
    print("   Your select_action() (Activity 2.3) above is complete.")
""",
    ),
    dict(
        id="3.1", phase=3, title="Implement Customer Session Management",
        module="`src/core/session_manager.py`",
        business_context="""A customer shouldn't have to repeat their identity or context on every message within one conversation. Without session state, the Coordinator you built in Activity 1.2 treats every turn as a cold start: this activity is what lets it actually remember.""",
        objective="Implement the three `SessionManager` methods that make a session accumulate state across turns: recording a turn, updating context, and reading recent history.",
        concept_overview="""This mirrors the state-passing idea from Bootcamp 1's `AgentState`, scoped to a `session_id` across many turns instead of one query. `SessionManager` is intentionally a plain in-memory dict keyed by `session_id`, per this lab's scope, that's "LangGraph-style state passing at session scope," not a database-backed session store.""",
        instructions="""1. Implement `add_turn()`: get-or-create the session, append `{"role", "content"}` to its `conversation_history`, refresh `updated_at`.
2. Implement `update_context()`: get-or-create the session, set `last_route` if given, merge `context_updates` into `context`, refresh `updated_at`.
3. Implement `get_recent_history()`: look up the session (return `[]` if it doesn't exist), return the last `turns` entries of `conversation_history`.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant why `create_session()` and `get_session()` were left fully implemented for you while these three weren't: same 'plumbing vs. objective' question as Activity 2.1's Tool Registry.",
        files=["src/core/session_manager.py"],
        target_methods={"src/core/session_manager.py": ["add_turn", "update_context", "get_recent_history"]},
        milestone="Customer context, conversation history and route history, now persists across turns within a session.",
        validation="""Confirm that:
- Exactly 2 turns were recorded, in the order they were added
- `last_route` is `"knowledge_agent"`
- `context` contains `{"last_topic": "account_opening"}`""",
        script="""from src.core.session_manager import SessionManager

sm = SessionManager()
try:
    sm.create_session("demo-session", customer_id="CUST-1001")
    sm.add_turn("demo-session", "user", "What documents do I need to open a savings account?")
    sm.add_turn("demo-session", "assistant", "You'll need ID proof, address proof, and a passport photo.")
    sm.update_context("demo-session", route="knowledge_agent", last_topic="account_opening")

    history = sm.get_recent_history("demo-session", turns=5)
    session = sm.get_session("demo-session")

    print(f"✓ Turns recorded: {len(history)}")
    if len(history) != 2:
        print(f"[WARN] Expected 2 turns recorded, got {len(history)}")
    print(f"✓ last_route: {session['last_route']}")
    if session["last_route"] != "knowledge_agent":
        print(f"[WARN] Expected last_route='knowledge_agent', got {session['last_route']!r}")
    print(f"✓ context: {session['context']}")
    if session["context"].get("last_topic") != "account_opening":
        print(f"[WARN] Expected context.last_topic='account_opening', got {session['context']}")
except NotImplementedError as e:
    print(f"[WARN] Task 3.1 not yet implemented: {e}")
    print("   Implement add_turn(), update_context(), and get_recent_history() in src/core/session_manager.py")
""",
    ),
    dict(
        id="3.2", phase=3, title="Handle Enterprise Service Failures",
        module="`src/utils/retry.py`",
        business_context="""Enterprise services fail transiently: a momentary timeout is not the same failure mode as a genuinely broken integration, and treating both the same way means customers see errors for problems that would have resolved themselves a second later.""",
        objective="Implement the retry-with-backoff loop inside `with_retry()`'s `wrapper()`. `src/agents/customer_service_agent.py`'s `_execute_tool()` is already decorated with `@with_retry()`, the one enterprise service call this platform demonstrates retry on (per this lab's scope: one policy, applied once, not a resilience framework).",
        instructions="""1. Loop up to `resolved_max_attempts` times, trying `func(*args, **kwargs)` each time.
2. On any exception in `exceptions`, log a warning and, if it wasn't the last attempt, sleep for an exponentially growing delay before retrying.
3. If every attempt fails, log an error and re-raise the last exception, never swallow it.

(See the numbered docstring in the file for the exact code shape expected.)""",
        ai_assist="**AI Assist:** Ask your AI coding assistant why the backoff delay grows exponentially (`backoff_seconds * 2 ** (attempt - 1)`) rather than staying constant between retries: it's a standard resilience pattern worth understanding, not just implementing.",
        files=["src/utils/retry.py"],
        target_methods={"src/utils/retry.py": ["wrapper"]},
        milestone="A transient enterprise service failure is retried automatically instead of failing the whole customer request.",
        validation="""Confirm that:
- `flaky_lookup()` succeeded, and `attempts["count"] == 3`: it failed on attempts 1 and 2, then succeeded on attempt 3
- The Customer Service Agent still returns a normal response for a customer profile lookup, unaffected by the retry wrapper now sitting around it""",
        script="""from src.utils.retry import with_retry

attempts = {"count": 0}

@with_retry(max_attempts=3, backoff_seconds=0.1)
def flaky_lookup():
    attempts["count"] += 1
    if attempts["count"] < 3:
        raise ConnectionError(f"simulated transient failure on attempt {attempts['count']}")
    return "profile data retrieved"

try:
    result = flaky_lookup()
    print(f"✓ Recovered after {attempts['count']} attempts: {result}")
    if attempts["count"] != 3:
        print(f"[WARN] Expected exactly 3 attempts before success, got {attempts['count']}")
except NotImplementedError as e:
    print(f"[WARN] Task 3.2 not yet implemented: {e}")
    print("   Implement the retry loop in with_retry()'s wrapper() in src/utils/retry.py")
except Exception as e:
    print(f"[WARN] Retry exhausted or raised unexpectedly: {e}")

# Confirm normal (non-flaky) tool execution through the Customer Service Agent
# still works now that _execute_tool is retry-wrapped.
from src.agents.customer_service_agent import CustomerServiceAgent
agent = CustomerServiceAgent()
try:
    result = agent.handle("Can you pull up my account profile?", context={"customer_id": "CUST-1001"})
    print(f"\\n✓ Tool execution still works normally: tool_used={result['tool_used']}")
except NotImplementedError as e:
    print(f"\\n[INFO] A full turn still isn't runnable: {e}")
    print("   If this names select_action, complete Activity 2.3 first.")
    print("   The full end-to-end turn is validated in Activity 3.3.")
""",
    ),
    dict(
        id="3.3", phase=3, title="Validate Enterprise Customer Service Operations",
        module="*No new module: end-to-end validation of everything implemented above*",
        business_context="""Every response this platform produces, from either sub-agent, needs to meet a minimum shape before it reaches a customer service executive: it needs response text, and it needs to say where it came from. Catching a malformed response here, with a safe fallback, is cheaper than a customer seeing a broken one.""",
        objective="Implement `ResponseValidator.validate()`, then run the complete platform against the realistic scenario suite in `data/validation/test_scenarios.json`, the first point in this lab where every activity works together.",
        instructions="""1. Find which of `self.required_fields` are missing from the response dict; if any are, return a message naming them.
2. Otherwise check that `response["response"]` is a non-empty string (after `.strip()`); if not, return `"Response text is empty"`.
3. Otherwise return `None` (valid).

`src/agents/coordinator_agent.py`'s `handle_turn()` already calls this validator before returning, falling back to a safe generic message on failure, so once this activity is done, a malformed response from any sub-agent is caught centrally, not per sub-agent.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant what other fields a production version of this validator might check (a maximum length? a citations format for knowledge answers?): this lab intentionally scopes to a field-presence check, but it's worth knowing what a fuller validator would add.",
        files=["src/utils/response_validator.py"],
        target_methods={"src/utils/response_validator.py": ["validate"]},
        milestone="The completed Enterprise Customer Service Operations Platform successfully supports realistic multi-agent banking customer service scenarios end to end.",
        validation="""Review the scorecard:
- Most scenarios should show `✓ PASS`: the `knowledge` and `service` categories should be reliable; occasional mismatches on the `edge_case` category are expected and not necessarily a bug, since those queries are deliberately ambiguous
- If every scenario shows `NOT IMPLEMENTED` naming *response validation*, that's **this** activity - implement `ResponseValidator.validate()`. If it names a different method (routing, action selection, retry, ...), revisit that earlier activity.
- If a scenario shows `[WARN] MISMATCH`, check whether the query is genuinely ambiguous (an `edge_case`) before assuming your `route_query()` implementation is wrong""",
        script="""import json
from src.utils.response_validator import ResponseValidator
from src.agents.coordinator_agent import CoordinatorAgent

validator = ResponseValidator()
try:
    print("Well-formed response ->", validator.validate({"response": "Hi there!", "source": "knowledge_agent"}))
    print("Missing field        ->", validator.validate({"response": "Hi there!"}))
    print("Empty text           ->", validator.validate({"response": "   ", "source": "knowledge_agent"}))
except NotImplementedError as e:
    print(f"[WARN] Task 3.3 not yet implemented: {e}")
    print("   Implement ResponseValidator.validate() in src/utils/response_validator.py")

scenarios = json.load(open("data/validation/test_scenarios.json", encoding="utf-8"))["test_scenarios"]
coordinator = CoordinatorAgent()

print(f"\\n{'ID':<10}{'Category':<12}{'Expected / Got Route':<38}{'Status'}")
print("-" * 78)
for scenario in scenarios:
    session_id = f"validation-{scenario['id']}"
    try:
        result = coordinator.handle_turn(session_id, scenario["query"], customer_id=scenario.get("customer_id"))
        got_route = result.get("route")
        status = "✓ PASS" if got_route == scenario["expected_route"] else "[WARN] MISMATCH"
        route_cell = f"{scenario['expected_route']} / {got_route}"
        print(f"{scenario['id']:<10}{scenario['category']:<12}{route_cell:<38}{status}")
    except NotImplementedError as e:
        msg = str(e)
        this_activity = "validation" in msg.lower()
        hint = "<- implement validate() (this activity)" if this_activity else "<- from an earlier activity"
        print(f"{scenario['id']:<10}{scenario['category']:<12}{'NOT IMPLEMENTED':<38}{msg}  {hint}")
""",
    ),
]

ACTIVITIES_BY_ID = {a["id"]: a for a in ACTIVITIES}
PHASE_TITLES = {
    1: "Phase 1 · Build the Multi-Agent Foundation",
    2: "Phase 2 · Integrate Enterprise Tools and Actions",
    3: "Phase 3 · Session Management, Resilience, and Validation",
}
PHASE_INTRO = {
    1: dict(
        objective="Understand the platform's layered architecture, then implement the Coordinator Agent, the "
                  "Knowledge Agent it routes to, and the Decision Engine that tells it where to route.",
        outcome="By the end of this phase, the platform can classify a customer query and answer it directly "
                "through the Knowledge Agent.",
    ),
    2: dict(
        objective="Give the Customer Service Agent real enterprise data to act on: a Tool Registry, the mock "
                  "services behind it, and the LLM-driven action selection that ties them together.",
        outcome="By the end of this phase, the platform can look up a customer's profile, retrieve their "
                "transactions, or open a service request, choosing the right action automatically.",
    ),
    3: dict(
        objective="Make the platform remember customers across turns, recover from a transient enterprise "
                  "service failure, and confirm every response meets a minimum shape before it ships.",
        outcome="By the end of this phase, the complete platform handles realistic multi-turn banking "
                "conversations end to end.",
    ),
}

# Short, single-line labels for the sidebar nav: the full descriptive title
# (used in PAGES, the hero banner, and Prev/Next buttons) wraps to 2-3 lines
# in the narrow sidebar and, repeated for all 9 activities, buries the actual
# navigation under a wall of text. The nav only needs enough to recognize
# "where am I"; the full title is one click away on the activity page itself.
NAV_SHORT_TITLES = {
    "1.1": "Explore the Platform",
    "1.2": "Build the Coordinator Agent",
    "1.3": "Build the Decision Engine",
    "2.1": "Configure the Tool Registry",
    "2.2": "Enterprise Service Integration",
    "2.3": "Function Calling & Actions",
    "3.1": "Session Management",
    "3.2": "Handle Service Failures",
    "3.3": "Validate the Platform",
}

REFERENCE_MAP = {
    "src/agents/knowledge_agent.py": "reference_solution/src/agents/knowledge_agent.py",
    "src/agents/coordinator_agent.py": "reference_solution/src/agents/coordinator_agent.py",
    "src/core/decision_engine.py": "reference_solution/src/core/decision_engine.py",
    "src/tools/tool_registry.py": "reference_solution/src/tools/tool_registry.py",
    "src/services/customer_profile_service.py": "reference_solution/src/services/customer_profile_service.py",
    "src/services/transaction_service.py": "reference_solution/src/services/transaction_service.py",
    "src/services/service_request_service.py": "reference_solution/src/services/service_request_service.py",
    "src/agents/customer_service_agent.py": "reference_solution/src/agents/customer_service_agent.py",
    "src/core/session_manager.py": "reference_solution/src/core/session_manager.py",
    "src/utils/retry.py": "reference_solution/src/utils/retry.py",
    "src/utils/response_validator.py": "reference_solution/src/utils/response_validator.py",
}


# ---------------------------------------------------------------------------
# Sidebar: navigation + progress tracker
# ---------------------------------------------------------------------------

PAGES = ["Overview & Setup"] + [f"Activity {a['id']} · {a['title']}" for a in ACTIVITIES] + ["Final Review"]

# Two-level nav: a top-level segmented control for Overview / each Phase /
# Final Review, then (only for a Phase) a short radio scoped to that
# phase's 3 activities. This keeps the always-visible list to at most 5
# items instead of all 11 activities at once, without the duplicate-selector
# trap other tools fall into (two separate widgets both choosing the same
# activity); this radio is the *only* control for "which activity."
TOP_LEVEL_OPTIONS = ["Overview"] + [f"Phase {p}" for p in PHASE_TITLES] + ["Final Review"]


def _nav_label(page: str) -> str:
    if page.startswith("Activity "):
        activity_id = page.replace("Activity ", "").split(" · ")[0]
        return f"{activity_id}  {NAV_SHORT_TITLES.get(activity_id, '')}"
    return page


def _phase_pages(phase_num: int) -> list:
    return [f"Activity {a['id']} · {a['title']}" for a in ACTIVITIES if a["phase"] == phase_num]


def _top_level_for(page: str) -> str:
    if page == PAGES[0] or page == PAGES[-1]:
        return TOP_LEVEL_OPTIONS[0] if page == PAGES[0] else TOP_LEVEL_OPTIONS[-1]
    activity_id = page.replace("Activity ", "").split(" · ")[0]
    return f"Phase {ACTIVITIES_BY_ID[activity_id]['phase']}"


if "nav_top" not in st.session_state:
    st.session_state.nav_top = TOP_LEVEL_OPTIONS[0]
# Widget session_state keys can't be reassigned after that widget has
# already been instantiated in the same run, so Previous/Next buttons
# (below) stage their target page here, applied before the widgets run.
if "pending_nav" in st.session_state:
    target = st.session_state.pop("pending_nav")
    st.session_state.nav_top = _top_level_for(target)
    if target not in (PAGES[0], PAGES[-1]):
        phase_num = ACTIVITIES_BY_ID[target.replace("Activity ", "").split(" · ")[0]]["phase"]
        st.session_state[f"nav_sub_{phase_num}"] = target

with st.sidebar:
    st.header("Guided Workbook")
    top_choice = st.segmented_control(
        "Section", TOP_LEVEL_OPTIONS, label_visibility="collapsed", key="nav_top"
    )
    if top_choice is None:
        # Clicking the active segment again deselects it in Streamlit. A
        # widget's session_state key can't be reassigned after that widget
        # has already run in this script pass, so defer the reset to
        # Overview via the same pending_nav mechanism the Previous/Next
        # buttons use (handled at the top of this block, before any widget
        # runs) and start a fresh run.
        st.session_state.pending_nav = PAGES[0]
        st.rerun()

    if top_choice in (TOP_LEVEL_OPTIONS[0], TOP_LEVEL_OPTIONS[-1]):
        selected_page = PAGES[0] if top_choice == TOP_LEVEL_OPTIONS[0] else PAGES[-1]
    else:
        phase_num = int(top_choice.split()[-1])
        phase_pages = _phase_pages(phase_num)
        sub_key = f"nav_sub_{phase_num}"
        if sub_key not in st.session_state:
            st.session_state[sub_key] = phase_pages[0]
        st.caption(f"↳ Activities in {top_choice}")
        selected_page = st.radio(
            "Activity", phase_pages, format_func=_nav_label, label_visibility="collapsed", key=sub_key
        )

    st.divider()
    st.subheader("Progress")

    passed_count = sum(1 for a in ACTIVITIES if st.session_state.activity_status.get(a["id"]) == "pass")
    total_count = len(ACTIVITIES)
    st.metric("Activities Complete", f"{passed_count} / {total_count}")
    st.progress(passed_count / total_count, text=f"{round(100 * passed_count / total_count)}% complete")

    if passed_count == total_count and not st.session_state.get("celebrated"):
        st.session_state.celebrated = True
        st.balloons()

    st.write("")
    for phase, phase_title in PHASE_TITLES.items():
        phase_activities = [a for a in ACTIVITIES if a["phase"] == phase]
        phase_done = sum(1 for a in phase_activities if st.session_state.activity_status.get(a["id"]) == "pass")
        st.caption(f"{phase_title.split('·')[0].strip()} · {phase_done}/{len(phase_activities)}")
        st.progress(phase_done / len(phase_activities))


# ---------------------------------------------------------------------------
# Reusable page pieces
# ---------------------------------------------------------------------------

def render_file_hint(rel_path: str):
    ref_path = REFERENCE_MAP.get(rel_path)
    if ref_path and (PROJECT_ROOT / ref_path).exists():
        with st.expander(f"Need a hint? View reference solution for {rel_path}"):
            st.code(read_file(ref_path), language="python")


def extract_method_source(file_text: str, method_name: str) -> tuple[str | None, str | None]:
    """Pull just one function/method's exact source (decorators included)
    out of a file's current text via ast, rather than the whole file, so
    the highlight below stays scoped to the few lines a participant is
    actually meant to touch. Returns (code, error): code is None if the
    file doesn't parse (a participant mid-edit with a syntax error) or the
    name isn't found; error carries the real SyntaxError detail so it can
    be shown instead of a generic "not found" message."""
    try:
        tree = ast.parse(file_text)
    except SyntaxError as e:
        return None, f"{e.msg} at line {e.lineno}, column {e.offset}"
    lines = file_text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:
            start_line = min([node.lineno] + [d.lineno for d in node.decorator_list])
            return "\n".join(lines[start_line - 1:node.end_lineno]), None
    return None, None


def render_code_to_work_on(rel_path: str, method_names: list):
    """Live, read-only view of exactly the method(s) an activity asks the
    participant to implement, extracted fresh from their current src/ file
    on every render, isolated from the surrounding file so the ~10-30 lines
    that matter aren't buried in a full-file dump."""
    label_col, refresh_col = st.columns([5, 1])
    label_col.markdown("**Code you'll work on**: live from your current file, not the answer.")
    # This block only re-reads the file on a Streamlit rerun (any widget
    # interaction), saving in VS Code alone doesn't trigger one, so it can
    # sit stale while you're just looking at the page. Clicking anything
    # reruns the whole script anyway (read_file() below always re-reads
    # from disk); this button exists so there's something to click even
    # when you haven't touched any other widget.
    refresh_col.button("Refresh", key=f"refresh_code_{rel_path}", help="Re-check this file's status against what's currently saved on disk.")
    text = read_file(rel_path)
    for name in method_names:
        segment, error = extract_method_source(text, name)
        if segment is None:
            if error:
                st.caption(f"`{name}`: can't check TODO status yet - {error} in {rel_path}. Fix this first, then the ✓/○ status below will work again.")
            else:
                st.caption(f"`{name}` not found in {rel_path} (it's been renamed or removed).")
            continue
        # Most stubs signal "not done" with `raise NotImplementedError`, but
        # a couple (e.g. __init__, or a nested wrapper()) only leave a
        # `# TODO:` comment behind, check for both, or a half-finished
        # method reads as done.
        done = "raise NotImplementedError" not in segment and "TODO" not in segment
        st.caption(f"{'✓' if done else '○'} `{name}`" + (": looks implemented" if done else ": still has a TODO"))
        st.code(segment, language="python")


STATUS_LABEL = {
    "pass": "✓ All checks passed",
    "warn": "[WARN] Not fully implemented yet",
    "error": "✗ The script raised an error",
}


def status_label_for(activity: dict, status: str) -> str:
    if status == "pass" and activity.get("pass_label"):
        return activity["pass_label"]
    return STATUS_LABEL.get(status, "Done")


def render_activity_runner(activity: dict):
    st.markdown("### Run & Validate")
    # 1.1 only scans the filesystem for TODOs; it has no `from src...`
    # import for reference_solution to stand in for, so it gets no button.
    has_reference_run = "from src" in activity["script"] or "import src" in activity["script"]

    if has_reference_run:
        run_col, ref_col = st.columns(2)
    else:
        run_col = st.container()
    run_clicked = run_col.button(f"> Run Activity {activity['id']}", type="primary", key=f"run_{activity['id']}")
    ref_clicked = has_reference_run and ref_col.button(
        "See reference solution run", key=f"ref_{activity['id']}",
        help="Runs this same check against the completed reference_solution/ instead of your src/. "
             "Use it if you're stuck and want to see what passing actually looks like. "
             "Doesn't count toward your progress."
    )

    if ref_clicked:
        with st.status("Running against reference_solution/ ...", expanded=True):
            result = run_snippet(activity["script"], use_reference=True)
            output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
            st.code(output.strip() or "(no output)", language="text")
        st.session_state[f"reference_output_{activity['id']}"] = result
    elif f"reference_output_{activity['id']}" in st.session_state:
        with st.status("Reference solution output", expanded=False):
            result = st.session_state[f"reference_output_{activity['id']}"]
            output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
            st.code(output.strip() or "(no output)", language="text")

    if run_clicked:
        with st.status("Running against your current src/ code...", expanded=True) as status_box:
            result = run_snippet(activity["script"])
            status = classify_run(result)
            output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
            st.code(output.strip() or "(no output)", language="text")
            if result["timed_out"]:
                status_box.update(label="Timed out", state="error", expanded=True)
            else:
                status_box.update(
                    label=status_label_for(activity, status),
                    state="complete" if status == "pass" else ("error" if status == "error" else "complete"),
                    expanded=(status != "pass"),
                )
        st.session_state.activity_status[activity["id"]] = status
        st.session_state.activity_output[activity["id"]] = result
        # Rerun so the sidebar's progress tracker (rendered earlier in script
        # order, before this activity page) picks up the status set just now.
        st.rerun()

    elif activity["id"] in st.session_state.activity_output:
        # Re-show the last run's result on a fresh page load, without re-running it.
        result = st.session_state.activity_output[activity["id"]]
        status = st.session_state.activity_status.get(activity["id"])
        with st.status(status_label_for(activity, status), state="complete" if status == "pass" else "error", expanded=(status != "pass")):
            output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
            st.code(output.strip() or "(no output)", language="text")
        if status == "pass":
            st.success("Milestone reached: you're ready for the next activity.")

    if activity.get("validation"):
        # Collapsed by default: this is what to check in your own output
        # beyond "did it run," most useful once you actually have output to
        # read it against, not before.
        with st.expander("✓ How to check your result"):
            st.markdown(activity["validation"])


# ---------------------------------------------------------------------------
# Page: Overview & Setup
# ---------------------------------------------------------------------------

if selected_page == "Overview & Setup":
    st.markdown("""
    <div class="hero-banner">
        <p class="hero-title">Guided Project: Enterprise Customer Service Operations Platform</p>
        <p class="hero-subtitle">Retail Banking · Customer Service Operations · Bootcamp 2, Tier 2 Multi-Agent Systems</p>
    </div>
    """, unsafe_allow_html=True)

    # These facts are fixed for the whole session (not a live metric to
    # track), so a caption (not st.metric) is the honest way to show them:
    # a metric implies "watch this change," which this never does.
    st.caption(
        f"{len(ACTIVITIES)} activities · {len(PHASE_TITLES)} phases · ~3 hrs · 2 specialized sub-agents · 3 enterprise services"
    )

    st.markdown("""
Welcome back. You're stepping into the role of an AI Engineer on the same retail bank's Enterprise AI
programme, picking up where Bootcamp 1 left off. The single agent you built there answered policy questions
well, but it couldn't look up a specific customer's account, pull their transaction history, or open a service
request on their behalf. You're fixing that, not by rebuilding what already works, but by wrapping it inside a
coordinated, multi-agent platform that knows when to answer from policy and when to act on enterprise data.

The project structure, UI, config, and data are already built; your job is the coordination and enterprise-tool
logic itself, one guided activity at a time.
""")

    if st.button("Start Activity 1.1: Explore the Platform", type="primary", use_container_width=True):
        st.session_state.pending_nav = PAGES[1]
        st.rerun()

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Business Context & Objectives", "What Makes This \"Multi-Agent\"", "Solution Architecture"])

    with tab1:
        with st.container(border=True):
            st.markdown("##### What You'll Build")
            st.markdown("""
- A Coordinator Agent that routes each customer turn to exactly one specialized sub-agent
- A Knowledge Agent that wraps your completed Bootcamp 1 agent as a black box
- A Customer Service Agent that selects and invokes enterprise service tools using the LLM's native function calling
- A Tool Registry integrating three mock enterprise services (customer profile, transactions, service requests)
- An Enterprise Decision Engine handling both query routing and structured action selection
- Session management that carries customer context across conversation turns
- Retry-with-backoff error handling and response validation around enterprise service calls
- A live Enterprise Customer Service Operations Portal (Streamlit) built on top of all of the above
""")
            st.caption("Built incrementally across 9 guided activities in 3 phases, each producing a tangible, verifiable output before you move to the next.")

        with st.container(border=True):
            st.markdown("##### The Business Problem")
            st.markdown("""
Customer service executives at the bank spend a large share of every call not talking to the customer, but
switching between systems: one screen for policy lookup, another for the customer's account profile, a third
to check recent transactions, and a fourth to log a service request. Bootcamp 1 solved the policy-lookup half
of that problem with a grounded, cited knowledge agent. It did nothing for the other half: anything that
requires knowing *which customer* is on the line and *acting* on their data. That fragmented workflow is what
drives up average handling time, and it's what this lab's platform is built to close.

This is Phase 2 of the bank's Enterprise AI programme. Leadership wants the Bootcamp 1 Customer Operations
Agent evolved into a full Customer Service Operations Platform: one that coordinates specialized agents
instead of one agent trying to do everything, invokes real enterprise services instead of only retrieving
documents, and remembers who it's talking to across an entire conversation instead of treating every message
as a fresh start.
""")

        with st.container(border=True):
            st.markdown("##### Your Role")
            st.markdown("""
You are the AI Engineer building that platform, on top of infrastructure that already includes your working
Bootcamp 1 agent, a reused knowledge base, and a set of mock enterprise services waiting to be wired together.
""")

        with st.container(border=True):
            st.markdown("##### Learning Objectives: by the end of this lab you will be able to")
            lo_col1, lo_col2 = st.columns(2)
            with lo_col1:
                st.markdown("""
- Design a coordinated multi-agent workflow in which a coordinator routes each turn to exactly one specialized sub-agent
- Implement a simple agent coordination pattern, distinguishing it from a single monolithic agent
- Integrate multiple enterprise services behind a single Tool Registry, decoupling *what* a tool does from *how* it's invoked
- Implement function calling and structured outputs to let an LLM choose an action and its parameters, not just generate text
- Maintain customer session context (conversation history, resolved identity, last route) across multiple turns
""")
            with lo_col2:
                st.markdown("""
- Build an enterprise decision engine that owns both routing and action-selection decisions
- Handle enterprise service failures gracefully with a retry-with-backoff strategy
- Validate that a platform's responses meet a minimum shape before they reach a customer, using a field-presence check
- Extend an existing enterprise application using modular, config-driven practices consistent with how it was originally built
""")

        with st.container(border=True):
            st.markdown("##### Dataset: already provided under `data/`")
            ds_col1, ds_col2 = st.columns(2)
            with ds_col1:
                st.markdown("""
**Enterprise Knowledge Base** (`knowledge_base/`)
The same 20 banking policy documents from Bootcamp 1, reused unchanged; the Knowledge Agent retrieves from these through your already-complete Bootcamp 1 agent.

**Bootcamp 1 Business Data** (`business_data/product_catalog.json`, `branch_directory.json`, `eligibility_rules.json`)
What the vendored Bootcamp 1 agent's tools read from. Reused unchanged.
""")
            with ds_col2:
                st.markdown("""
**New Customer Service Data** (`business_data/customer_profiles.json`, `transaction_records.json`)
Five mock customers (`CUST-1001` through `CUST-1005`) with linked accounts, and ten mock transactions across them. What the new enterprise services read from.

**Validation Scenarios** (`validation/test_scenarios.json`)
8 realistic customer queries spanning knowledge questions, service requests, and edge cases, each with an expected routing decision. Used end to end in Activity 3.3.
""")

    with tab2:
        st.markdown("""
The agent you built in Bootcamp 1 is a **single agent**: one workflow that classifies, retrieves, and
responds, all inside one class. That works well when every request needs the same kind of handling. It breaks
down once requests start needing fundamentally different capabilities, grounded policy answers versus live
account lookups, because cramming both into one classifier-and-responder makes that one agent harder to
reason about, test, and extend every time you add a new capability.
""")
        components.html(MULTI_AGENT_DIAGRAM_SVG, height=460)
        st.markdown("""
A **multi-agent system** solves this by specializing instead of generalizing: instead of one agent trying to
do everything, a coordinator decides *which* specialist should own each turn, then delegates to it. That
routing decision, not the number of LLM calls, is what makes something "multi-agent" rather than just "an
agent with more prompts." This lab's platform adds four properties on top of what you already built, and you
will implement all four:

- **Specialization**: each sub-agent owns one kind of work instead of one agent trying to do everything. You will implement this as `KnowledgeAgent` and `CustomerServiceAgent` in Activities 1.2 and 2.2.
- **Coordination**: exactly one sub-agent is chosen per turn, the same route-to-one-destination shape as Bootcamp 1's `route_decision`, one level up. You will implement this as `CoordinatorAgent.handle_turn()` and `DecisionEngine.route_query()` in Activities 1.2 and 1.3.
- **Structured decision-making**: the platform doesn't just generate text, it decides *which* action to take and with *what* parameters, using the LLM's native function calling instead of parsing free text. You will implement this as `DecisionEngine.select_action()` in Activity 2.3.
- **Shared context**: sub-agents don't lose track of who they're talking to between turns. You will implement this as `SessionManager` in Activity 3.1.

Keep this loop in mind as you go: every activity in this lab implements one piece of it. The Solution
Architecture tab shows the specific architecture this platform uses to do it.
""")

    with tab3:
        st.markdown("Here is how this platform is layered, and which folder each layer lives in:")
        components.html(ARCHITECTURE_DIAGRAM_SVG, height=660)
        st.markdown("""
Two things to notice, because you will feel their effect throughout the lab:
- **The Coordinator is the only thing the Portal talks to.** Nothing in `app/customer_portal.py` decides routing or picks a tool, it only calls `CoordinatorAgent.handle_turn()` and displays the result. That keeps business logic out of the UI, exactly like Bootcamp 1.
- **The Knowledge Agent is a wrapper, not a rewrite.** It constructs your Bootcamp 1 `CustomerOperationsAgent` and calls `.run()` on it: you are not reimplementing RAG in this lab.

Zooming into the Orchestration layer, here is the flow you will build across the phases ahead, with each stage
mapped to the activity that implements it:
""")
        components.html(ORCHESTRATION_FLOW_SVG, height=630)

    import importlib.util
    required_packages = ["langgraph", "faiss", "openai", "streamlit", "yaml", "dotenv"]
    missing_packages = [pkg for pkg in required_packages if importlib.util.find_spec(pkg) is None]

    # OPENAI_API_KEY works with either a real OpenAI key or an OpenRouter
    # key (see .env.example); LLM_BASE_URL picks which one src/llm/ and
    # src/knowledge/embeddings.py actually talk to.
    key = os.getenv("OPENAI_API_KEY")
    key_missing = not key or key in ("your_openai_api_key_here", "your_openai_or_openrouter_api_key_here")

    required_paths = [
        "data/knowledge_base/accounts", "data/knowledge_base/cards",
        "data/knowledge_base/loans", "data/knowledge_base/operations",
        "data/business_data/product_catalog.json", "data/business_data/branch_directory.json",
        "data/business_data/eligibility_rules.json", "data/business_data/customer_profiles.json",
        "data/business_data/transaction_records.json", "data/validation/test_scenarios.json",
        "config/agent_config.yaml", "config/llm_config.yaml", "config/prompts.yaml", "config/tools_config.yaml",
    ]
    missing_paths = [p for p in required_paths if not (PROJECT_ROOT / p).exists()]

    # The Knowledge Agent (Activity 1.2) delegates to the vendored Bootcamp 1
    # agent, which loads a cached FAISS index from VECTOR_DB_PATH instead of
    # re-embedding the knowledge base on every run. Nothing builds that index
    # automatically, so without this check a learner's first live run of
    # Activity 1.2 fails with a raw "file not found" error from faiss, not a
    # clean NotImplementedError, before they've written any code themselves.
    index_path = PROJECT_ROOT / os.getenv("VECTOR_DB_PATH", "./vector_store") / "kb_index"
    index_ready = index_path.with_suffix(".index").exists() and index_path.with_suffix(".docs").exists()

    all_ok = not missing_packages and not key_missing and not missing_paths and index_ready
    expander_label = "✓ Environment ready" if all_ok else "[WARN] Environment Validation: action needed"

    with st.expander(expander_label, expanded=not all_ok):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("**Packages**")
            if missing_packages:
                st.error(f"Missing: {', '.join(missing_packages)}\n\nRun: `pip install -r requirements.txt`")
            else:
                st.success("All required packages are installed.")

        with col2:
            st.markdown("**API Key**")
            if key_missing:
                st.error("OPENAI_API_KEY is not set.\n\nCopy `.env.example` to `.env`, then paste the API key from your lab desktop's **Lab Details** icon into `OPENAI_API_KEY`.")
            else:
                st.success("OPENAI_API_KEY is configured.")

        with col3:
            st.markdown("**Project Assets**")
            if missing_paths:
                st.error(f"Missing: {', '.join(missing_paths)}")
            else:
                st.success(f"All {len(required_paths)} required project assets are present.")

        with col4:
            st.markdown("**Knowledge Base Index**")
            if index_ready:
                st.success("Cached FAISS index found - no rebuild needed.")
            else:
                st.error("No cached index at `vector_store/kb_index.*`.")
                st.caption(
                    "One-time build: makes a real, billed OpenAI embeddings call per document "
                    "chunk (~220 chunks across the 20 knowledge base documents), a few cents at "
                    "typical `text-embedding-3-small` pricing. The result is cached, so this only "
                    "needs to run once."
                )
                if not key_missing and not missing_paths:
                    if st.button("Build knowledge base index", key="build_kb_index"):
                        with st.spinner("Embedding knowledge base documents (one-time)..."):
                            sys.path.insert(0, str(PROJECT_ROOT))
                            from src.knowledge.knowledge_base import KnowledgeBase

                            kb = KnowledgeBase()
                            documents = kb.load_documents(str(PROJECT_ROOT / "data" / "knowledge_base"))
                            kb.build_index(documents)
                            kb.save_index(str(index_path))
                        st.success(f"Built and cached an index over {len(documents)} chunks.")
                        st.rerun()
                else:
                    st.caption("Fix the API Key / Project Assets checks above first.")


# ---------------------------------------------------------------------------
# Page: Final Review
# ---------------------------------------------------------------------------

elif selected_page == "Final Review":
    st.markdown("""
    <div class="hero-banner">
        <p class="hero-title">Final Review</p>
        <p class="hero-subtitle">Review everything you've built, then run one final live demonstration</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
Review what you've built across all three phases:
- **Multi-Agent Coordination**: a Coordinator Agent routing each turn to exactly one specialized sub-agent (Phase 1)
- **Enterprise Tool Integration**: a Tool Registry, three mock enterprise services, and LLM-driven function calling for action selection (Phase 2)
- **Session Management, Resilience, and Validation**: customer context across turns, retry-with-backoff for a flaky service call, and response validation with a safe fallback (Phase 3)
""")

    if st.button("> Run Final Demo", type="primary"):
        with st.spinner("Running the complete platform end-to-end..."):
            result = run_snippet("""from src.agents.coordinator_agent import CoordinatorAgent

coordinator = CoordinatorAgent()
session_id = "final-demo"
customer_id = "CUST-1001"

conversation = [
    "What documents do I need to open a savings account?",
    "Can you pull up my account profile?",
    "And what about my recent transactions?",
]

try:
    for turn_query in conversation:
        result = coordinator.handle_turn(session_id, turn_query, customer_id=customer_id)
        print(f"{turn_query}")
        print(f"[{result['route']}] {result['response']}\\n")

    session = coordinator.session_manager.get_session(session_id)
    if session:
        print(f"Session has {len(session['conversation_history'])} recorded turns for customer {session['customer_id']}.")
    print("\\n✓ End-to-end platform execution complete.")
except NotImplementedError as e:
    print(f"[WARN] Not all activities are complete yet: {e}")
""")
        output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
        st.code(output.strip() or "(no output)", language="text")

    st.markdown("---")
    st.markdown("#### Key Takeaways")

    kt_col1, kt_col2, kt_col3 = st.columns(3)
    with kt_col1:
        st.markdown("""**What You Built**
- A Coordinator Agent that routes each customer turn to exactly one specialized sub-agent
- A Knowledge Agent wrapping your completed Bootcamp 1 agent, unchanged
- A Customer Service Agent driven by LLM native function calling to select and invoke enterprise actions
- A Tool Registry integrating three mock enterprise services behind a single name-based interface
- An Enterprise Decision Engine owning both routing and structured action selection
- Session management carrying customer context across conversation turns
- Retry-with-backoff error handling and response validation around enterprise service calls
- A live Enterprise Customer Service Operations Portal built entirely on top of these modules""")
    with kt_col2:
        st.markdown("""**Enterprise/Engineering Principles Applied**
- **Specialization over generalization**: a coordinator delegating to focused sub-agents, rather than one agent trying to do everything
- **Configuration-driven behaviour**: routing rules, tool definitions, retry policy, and required response fields all live in YAML, not hardcoded in Python
- **Reuse over rebuild**: the completed Bootcamp 1 agent and knowledge base are vendored and wrapped, never reimplemented
- **Graceful degradation**: every module in this platform, and the Streamlit portal built on top of it, fails informatively rather than silently when a capability isn't implemented yet
- **Resilience and validation as first-class concerns**: a transient service failure is retried automatically, and every response is checked before it reaches a customer""")
    with kt_col3:
        st.markdown("""**Skills Demonstrated**
- Multi-agent coordination pattern design and implementation
- LLM-driven routing and native function calling for structured action selection
- Enterprise service integration behind a tool registry abstraction
- Session/context management across multi-turn conversations
- Retry-with-backoff resilience patterns
- Response validation with safe fallback behaviour
- Extending an existing enterprise codebase using its own established conventions""")

    st.markdown("---")
    st.markdown("""
**Next Steps:** The Enterprise Customer Service Operations Platform you built in this lab is the coordination
layer for a growing enterprise AI programme; the same patterns (specialized sub-agents, a tool registry,
function-calling action selection, and validated, resilient responses) scale to additional sub-agents and
enterprise services well beyond the three this lab introduced.
""")


# ---------------------------------------------------------------------------
# Page: an individual activity
# ---------------------------------------------------------------------------

else:
    activity_id = selected_page.replace("Activity ", "").split(" · ")[0]
    activity = ACTIVITIES_BY_ID[activity_id]

    # Shown once per phase, right before that phase's first activity: the
    # same place the notebook's own phase-intro cell sits, immediately
    # before Activity X.1's cell. Not repeated on X.2/X.3 since you've
    # already seen it by then.
    if activity["id"].endswith(".1"):
        phase_intro = PHASE_INTRO[activity["phase"]]
        st.markdown(f"#### {PHASE_TITLES[activity['phase']]}")
        st.markdown(f"**Objective:** {phase_intro['objective']}")
        st.caption(phase_intro["outcome"])
        st.divider()

    st.markdown(f"""
    <div class="hero-banner">
        <p class="hero-title">Activity {activity['id']} · {activity['title']}</p>
        <p class="hero-subtitle">{activity['module']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"**What success looks like:** {activity['milestone']}")

    with st.container(border=True):
        st.markdown("#### Business Context")
        st.markdown(activity["business_context"])

    with st.container(border=True):
        st.markdown("#### Objective")
        st.markdown(activity["objective"])

    if activity.get("concept_overview"):
        with st.container(border=True):
            st.markdown("#### Concept Overview")
            st.markdown(activity["concept_overview"])

    with st.container(border=True):
        st.markdown("#### Implementation Instructions")
        st.markdown(activity["instructions"])
        if activity.get("ai_assist"):
            st.info(activity["ai_assist"])

    if activity.get("reference_only_files"):
        # Collapsed by default: a full config file dumped open on the page
        # is exactly the "wall of code" that makes a lab feel harder than it
        # is before anyone's read a word of the instructions above.
        with st.expander(f"Reference Files: {', '.join(activity['reference_only_files'])}"):
            tabs = st.tabs(activity["reference_only_files"])
            for tab, path in zip(tabs, activity["reference_only_files"]):
                with tab:
                    st.code(read_file(path), language="yaml")

    if activity["files"]:
        st.markdown("#### Files to Edit")
        st.info(
            "Open these in VS Code (or your preferred IDE) to write your implementation. This app runs "
            "whatever is currently saved on disk, it doesn't edit files itself."
        )
        target_methods = activity.get("target_methods", {})
        if len(activity["files"]) == 1:
            path = activity["files"][0]
            st.code(path, language="text")
            if path in target_methods:
                render_code_to_work_on(path, target_methods[path])
            render_file_hint(path)
        else:
            # Tab labels already name each file; an extra list above them
            # would just repeat the same names twice in a row.
            tabs = st.tabs(activity["files"])
            for tab, path in zip(tabs, activity["files"]):
                with tab:
                    if path in target_methods:
                        render_code_to_work_on(path, target_methods[path])
                    render_file_hint(path)

    st.divider()
    render_activity_runner(activity)

    st.divider()
    page_index = PAGES.index(selected_page)
    prev_col, next_col = st.columns(2)
    with prev_col:
        if page_index > 0:
            if st.button(f"< {PAGES[page_index - 1]}", use_container_width=True):
                st.session_state.pending_nav = PAGES[page_index - 1]
                st.rerun()
    with next_col:
        if page_index < len(PAGES) - 1:
            if st.button(f"{PAGES[page_index + 1]} >", use_container_width=True, type="primary"):
                st.session_state.pending_nav = PAGES[page_index + 1]
                st.rerun()
