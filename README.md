# OrchefAI

### Autonomous Multi-Agent Catering Operations Platform

**Built with Microsoft Azure AI + NVIDIA NIM | Multi-Agent Orchestration | RAG-Powered Intelligence**

---

## Problem

Catering operations is a **$320B global industry** still run on spreadsheets, WhatsApp groups, and phone calls. A single event requires coordinating menus, suppliers, pricing, dietary compliance, and risk management — typically taking **20+ hours of manual work per event**.

No production-grade AI system exists to orchestrate this end-to-end.

---

## Solution

OrchefAI is a **multi-agent AI system** where 5 specialized agents collaborate autonomously to convert a natural language catering request into a complete, costed, risk-validated plan — in under 30 seconds.

The system features **autonomous recovery**: when the Monitoring Agent detects a high-severity risk (ingredient shortage, budget conflict, dietary violation), it triggers an automatic re-planning loop without human intervention.

---

## Architecture

```
                        ┌─────────────────────────────┐
                        │     Streamlit UI Layer       │
                        │  (Voice + Text + PDF Export) │
                        └──────────────┬──────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │    Orchestrator Agent        │
                        │  (Workflow Graph Controller) │
                        └──────────────┬──────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
   ┌──────────▼──────────┐  ┌─────────▼─────────┐  ┌──────────▼──────────┐
   │    Intake Agent      │  │    Menu Agent      │  │  Inventory Agent    │
   │  (NLU → Structured)  │  │  (RAG + Planning)  │  │ (Procurement + QA)  │
   └──────────────────────┘  └────────────────────┘  └─────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                                                 │
   ┌──────────▼──────────┐                          ┌──────────▼──────────┐
   │   Pricing Agent      │                          │  Monitoring Agent   │
   │ (Cost Optimization)  │                          │ (Risk + Auto-Replan)│
   └──────────────────────┘                          └─────────────────────┘
                                       │
                              ┌─────────▼─────────┐
                              │  Recovery Loop     │
                              │ (Autonomous Replan)│
                              └───────────────────┘
```

---

## Agent Team

| Agent | Responsibility | Model |
|-------|---------------|-------|
| **Orchestrator** | Workflow coordination, state management, recovery triggers | NVIDIA Nemotron-4 340B |
| **Intake Agent** | Natural language understanding → structured event profile | Meta Llama 3.1 70B |
| **Menu Agent** | RAG-powered menu planning from Azure AI Search knowledge base | Meta Llama 3.1 70B |
| **Inventory Agent** | Ingredient calculation, supplier matching, shortage detection | Meta Llama 3.1 8B |
| **Pricing Agent** | Full cost breakdown, margin analysis, budget feasibility | Meta Llama 3.1 8B |
| **Monitoring Agent** | Risk audit across 9 dimensions, autonomous re-plan trigger | Meta Llama 3.1 70B |

---

## Microsoft Azure Integration

| Azure Service | Usage |
|---------------|-------|
| **Azure AI Search** | Semantic search over catering knowledge base (dishes, suppliers, dietary rules, event templates). Powers the Menu Agent's RAG pipeline with semantic ranking. |
| **Azure Cosmos DB** | Shared agent memory — all agents read/write a single `EventState` document. Provides the coordination layer for multi-agent state handoffs. |
| **Azure Identity** | Authentication layer for all Azure service connections. |

---

## NVIDIA NIM Integration

| Component | Usage |
|-----------|-------|
| **NVIDIA NIM API** | All LLM inference runs through NVIDIA NIM endpoints (OpenAI-compatible). Supports Nemotron-4 340B and Llama 3.1 family. |
| **NVIDIA Riva ASR** | Voice input via Parakeet streaming ASR model — users can speak their catering request instead of typing. |

---

## Key Features

- **Multi-Agent Orchestration** — 5 agents with distinct roles, structured JSON handoffs, shared state via Cosmos DB
- **RAG-Grounded Menu Planning** — Azure AI Search with semantic ranking over curated knowledge base (dishes, suppliers, dietary rules)
- **Autonomous Recovery Loop** — Monitoring Agent detects failures and triggers re-planning without human intervention
- **Voice-First Input** — NVIDIA Riva Parakeet ASR for natural speech-to-plan workflow
- **Region-Aware Pricing** — Automatic cost profile selection across 8 global regions (Singapore, US, UK, UAE, Australia, Europe, India, Southeast Asia)
- **Smart Budget Optimization** — Best adjusted to quotations under customer budget and also dynamically adjusts margins
- **PDF Export** — One-click professional catering plan generation for client sharing
- **Restaurant Profile** — Configurable business profile (capacity, certifications, cuisine types) that influences plan generation
- **Event History** — SQLite-backed event tracking with full plan persistence
- **Real-Time Agent Logs** — Live visibility into every agent decision and handoff
- **9-Dimension Risk Audit** — Budget, inventory, dietary, allergen, timeline, margin, portions, supplier reliability, halal compliance

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | **Microsoft AutoGen** (multi-agent orchestration) |
| LLM Inference | **NVIDIA NIM** (Nemotron-4 340B, Llama 3.1 70B/8B) |
| Knowledge Retrieval | **Azure AI Search** (semantic ranking, filtered queries) |
| Agent State Store | **Azure Cosmos DB** (shared EventState document) |
| Voice Input | **NVIDIA Riva ASR** (Parakeet streaming model) |
| Frontend | **Streamlit** (real-time updates, animated pipeline progress) |
| Data Validation | **Pydantic v2** (typed EventState schema) |
| PDF Generation | **FPDF2** (branded report export) |
| Language | **Python 3.11+** (fully async pipeline) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Azure account (AI Search + Cosmos DB)
- NVIDIA NIM API key

### Setup

```bash
git clone https://github.com/smilewithkhushi/orchefai
cd orchefai

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Configure:
#   NVIDIA_API_KEY
#   AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_API_KEY
#   COSMOS_ENDPOINT / COSMOS_KEY

# Index knowledge base into Azure AI Search
python setup/index_knowledge_base.py

# Launch
streamlit run app.py
```

---

## Demo Scenarios

### 1. Standard Flow
```
"We need a vegetarian corporate lunch for 150 people at our Raffles Place office next Thursday. Budget is around 8,000 SGD, must be halal certified."
```
Full pipeline executes → complete catering plan in ~25 seconds.

### 2. Autonomous Recovery (Key Differentiator)
```
"Halal dinner for 200 guests this Saturday in Delhi, budget ₹4,00,000"
```
- Inventory Agent detects lamb shortage (only 120 portions available from suppliers)
- Monitoring Agent flags HIGH RISK
- System **auto-replans** with chicken/tofu substitution
- Revised plan delivered with updated cost breakdown — zero human intervention

### 3. Voice Input
User speaks: *"I need a birthday party menu for 50 people, vegetarian, budget around two thousand dollars"*
- NVIDIA Riva transcribes speech → text
- Intake Agent structures the request
- Full pipeline executes autonomously

---

## Project Structure

```
orchefai/
├── app.py                     # Streamlit UI with real-time pipeline visualization
├── config.py                  # Agent models, cost profiles, staffing logic, API clients
├── agents/
│   ├── orchestrator.py        # Pipeline coordinator with recovery loop
│   ├── intake_agent.py        # NLU → structured event profile
│   ├── menu_agent.py          # RAG-powered menu planning
│   ├── inventory_agent.py     # Ingredient + procurement calculation
│   ├── pricing_agent.py       # Cost breakdown + budget feasibility
│   ├── monitoring_agent.py    # 9-dimension risk audit
│   └── prompts.py             # All agent system prompts
├── models/
│   ├── event_state.py         # Pydantic EventState schema (shared memory)
│   └── restaurant.py          # Restaurant profile model
├── tools/
│   ├── cosmos_tool.py         # Azure Cosmos DB read/write
│   ├── search_tool.py         # Azure AI Search queries
│   ├── pdf_export.py          # PDF catering plan generation
│   └── history_db.py          # Event history persistence
├── utils/
│   ├── transcribe.py          # NVIDIA Riva ASR integration
│   ├── currency.py            # Multi-currency conversion
│   └── audio_storage.py       # Audio recording handling
├── setup/
│   └── index_knowledge_base.py # Azure AI Search indexing script
├── data/                       # Local knowledge base (menus, suppliers, rules)
└── pages/                      # Streamlit multi-page app
    ├── 1_Restaurant_Profile.py
    └── 2_Event_History.py
```

---

## What Makes This Different

| Approach | Traditional Catering Software | OrchefAI |
|----------|------------------------------|----------|
| Input | Forms and dropdowns | Natural language (text + voice) |
| Planning | Manual by human staff | Autonomous multi-agent pipeline |
| Recovery | Manual escalation | Auto-replan on risk detection |
| Knowledge | Static database | RAG over semantic knowledge base |
| Pricing | Fixed price lists | Dynamic region-aware cost optimization |
| Risk | Post-hoc review | Real-time 9-dimension audit |

---

## Market Opportunity

- **$2.14B** catering software market (2024), growing at **13.2% CAGR**
- **20+ hours/week** saved per operations manager per event
- **$8 ROI** for every $1 invested in catering waste reduction (NRA)
- Zero production-grade multi-agent AI systems exist in this vertical

---

## License

MIT
