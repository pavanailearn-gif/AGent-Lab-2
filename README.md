# Enterprise Customer Service Operations Platform

## Bootcamp 2: Building an Enterprise Customer Service Operations Platform

A guided project for extending the Bootcamp 1 Customer Operations Agent into a coordinated, multi-agent platform that integrates enterprise services alongside knowledge retrieval.

**Prerequisite:** Bootcamp 1 (Enterprise AI Customer Operations Agent) completed. This bootcamp extends that agent into a multi-agent platform and reuses its knowledge base directly.

---

## 🎯 Overview

This project simulates Phase 2 of a retail bank's Enterprise AI programme: transforming the single Bootcamp 1 agent into a Customer Service Operations Platform that coordinates specialized agents instead of one agent trying to do everything. You'll build:

- A **Coordinator Agent** that routes each customer turn to exactly one specialized sub-agent
- A **Knowledge Agent** that wraps your completed Bootcamp 1 agent as a black box
- A **Customer Service Agent** that uses the LLM's native function calling to select and invoke enterprise service tools
- A **Tool Registry** integrating three mock enterprise services (customer profile, transactions, service requests)
- An **Enterprise Decision Engine** handling both query routing and structured action selection
- **Session management** that carries customer context across conversation turns
- **Retry-with-backoff** error handling and **response validation** around enterprise service calls

---

## 🏗️ Project Structure

```
AgenticAI-EnterpriseDelivery-Bootcamp2-GP_Solution/
│
├── src/                        # Source code (INCOMPLETE - Starter)
│   ├── agents/                 # Coordinator, Knowledge, Customer Service agents
│   ├── core/                   # Decision engine, session manager
│   ├── tools/                  # Tool registry
│   ├── services/               # Mock enterprise services
│   ├── bootcamp1_agent/        # Vendored, COMPLETE Bootcamp 1 agent (do not edit)
│   ├── llm/                    # LLM client and prompt management (complete)
│   ├── knowledge/              # RAG components, reused from Bootcamp 1 (complete)
│   └── utils/                  # Logging, config, validation, retry, response validation
│
├── app/                        # Streamlit UI (complete)
│   ├── customer_portal.py      # Enterprise Customer Service Operations Portal
│   └── workbook_app.py         # Guided lab: 9 activities, live code hints, per-activity validation
│
├── config/                     # Configuration files
│   ├── agent_config.yaml       # Coordination, retry, and validation settings
│   ├── llm_config.yaml         # LLM provider and model parameters (OpenRouter)
│   ├── prompts.yaml            # System prompts (routing, action selection, etc.)
│   └── tools_config.yaml       # Registered enterprise service tool definitions
│
├── data/                       # Data assets
│   ├── knowledge_base/         # Banking policy documents (20 docs, reused)
│   ├── business_data/          # Bootcamp 1 data + customer profiles / transactions
│   └── validation/             # Test scenarios for the full platform
│
├── reference_solution/         # Complete implementation (instructor only)
│   └── src/                    # Completed source code
│
├── requirements.txt            # Python dependencies
├── .env.example                # Copy to .env, then add your API key
├── Githubguide                 # Git / GitHub how-to (PDF)
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Bootcamp 1 completed
- An OpenRouter API key - on your lab desktop, double-click the **Lab Details** icon; it opens a page with your OpenRouter account's API key and a copy button

### Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and paste the API key from the Lab Details icon into OPENAI_API_KEY
   ```

3. **Start the guided lab**
   ```bash
   streamlit run app/workbook_app.py
   ```
   Work through the 9 activities here. To see the finished platform in the
   customer-facing UI, also run the portal (it shows a demo placeholder until
   the modules are implemented):
   ```bash
   streamlit run app/customer_portal.py
   ```

---

## 📚 Getting Started with the Guided Lab

👉 **Start here:** the interactive workbook app

```bash
streamlit run app/workbook_app.py
```

[`app/workbook_app.py`](app/workbook_app.py) walks through 9 hands-on activities across 3 phases. For each one it gives you the business context and learning objective, the exact method(s) to implement highlighted live from your own file, step-by-step instructions, a one-click **Run & Validate**, and the reference solution one click away when you're stuck.

**Estimated completion time:** 3 hours

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| LLM access | `openai` Python SDK (2.x), calling an OpenAI-compatible Chat Completions API |
| LLM provider | OpenRouter, model `openai/gpt-4` via `LLM_BASE_URL=https://openrouter.ai/api/v1` (a direct OpenAI key with no base URL also works) |
| Embeddings | `openai/text-embedding-3-small`, same endpoint |
| Structured outputs | OpenAI-native function calling (`tools=[…]`, `tool_choice="auto"`) |
| Multi-agent coordination | Plain Python: Coordinator Agent plus Decision Engine, no agent framework |
| Workflow engine | LangGraph 1.1, only inside the vendored Bootcamp 1 agent (`src/bootcamp1_agent/`) |
| Vector store | FAISS (`faiss-cpu`), knowledge base reused from Bootcamp 1 |
| Resilience | Hand-rolled retry-with-backoff (`src/utils/retry.py`) |
| UI | Streamlit, for the customer portal and the guided workbook app |
| Configuration | YAML (`config/*.yaml`) plus `.env` via `python-dotenv` |

> No LangChain: `langchain` / `langchain-openai` were removed. The platform talks to the LLM directly through the `openai` SDK. LangGraph remains only because the vendored Bootcamp 1 agent is built on it.

---

## 📖 Documentation

- **[Guided workbook app](app/workbook_app.py)** - `streamlit run app/workbook_app.py`; the 9 activities with live code hints and per-activity validation

---

## 🎓 Learning Objectives

By completing this bootcamp, you will:

1. ✅ Design a coordinated multi-agent workflow, routing each turn to exactly one specialized sub-agent
2. ✅ Implement a simple agent coordination pattern, distinct from a single monolithic agent
3. ✅ Integrate multiple enterprise services behind a single Tool Registry
4. ✅ Implement function calling and structured outputs for LLM-driven action selection
5. ✅ Maintain customer session context across multiple conversation turns
6. ✅ Build an enterprise decision engine owning both routing and action selection
7. ✅ Handle enterprise service failures gracefully with retry-with-backoff
8. ✅ Validate platform responses against a minimum required shape
9. ✅ Extend an existing enterprise application using its own modular, config-driven conventions

---

## 🔍 What You'll Build

### Phase 1: Multi-Agent Foundation
- A Coordinator Agent routing each turn to one sub-agent
- A Knowledge Agent wrapping the completed Bootcamp 1 agent
- An Enterprise Decision Engine performing LLM-driven query routing

### Phase 2: Enterprise Tools and Actions
- A Tool Registry integrating three mock enterprise services
- A Customer Service Agent invoking enterprise actions
- Function calling and structured outputs for action selection

### Phase 3: Session Management, Resilience, and Validation
- Customer session context carried across conversation turns
- Retry-with-backoff for enterprise service failures
- Response validation with a safe fallback, plus a full end-to-end scenario suite

---

## 🧪 Testing

This project has no pytest suite. The primary validation for this lab is Activity 3.3's scenario suite inside the workbook itself (`data/validation/test_scenarios.json`), which exercises the complete platform end to end.

---

## 📝 Project Status

**Current Status:** Complete Starter Solution

- ✅ Project structure created
- ✅ Bootcamp 1 infrastructure reused (`src/llm/`, `src/knowledge/`, `src/utils/`) and its completed agent vendored into `src/bootcamp1_agent/`
- ✅ TODO-stubbed starter modules for `src/agents/*`, `src/core/*`, `src/tools/tool_registry.py`, `src/services/*`, `src/utils/retry.py`, `src/utils/response_validator.py`
- ✅ Reference solution implemented and verified (`reference_solution/src/`)
- ✅ Guided Project Workbook built and validated (zero unhandled errors against the unimplemented starter)
- ✅ `app/customer_portal.py`, the Enterprise Customer Service Operations Portal
- ✅ Documentation complete

---

## 🤝 Support

- Reference solution available in `reference_solution/` for comparison

---

## 📄 License

This is an educational project for the Agentic AI for Enterprise Delivery Bootcamp.

---

## 🎯 Next Steps

1. Follow the Quick Start above to configure your environment
2. Run `streamlit run app/workbook_app.py` to work through the 9 activities in an interactive UI, starting with Activity 1.1
3. Run `streamlit run app/customer_portal.py` to see the starter portal (it shows a demo placeholder until the platform is implemented)
4. Begin implementing the multi-agent platform!

**Good luck and happy coding! 🚀**
