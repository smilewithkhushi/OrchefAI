# 🍽️ OrchefAI
### AI-Powered Multi-Agent System for Smart Catering Operations

---

## What is OrchefAI?

OrchefAI is a production-grade multi-agent AI system that transforms catering operations from a manual, fragmented process into a fully orchestrated workflow.

A team of **5 specialized AI agents** collaborate in real-time to convert a customer's natural language request into a complete, costed, and risk-validated catering plan — in under 60 seconds.

> *"Catering managers currently spend 20+ hours/week on manual coordination across spreadsheets, WhatsApp, and phone calls. OrchefAI eliminates that entirely."*

---

## The Agent Team

| Agent | Role | Model |
|---|---|---|
| 🎯 **Orchestrator** | Coordinates all agents, manages workflow graph | Nemotron-4 340B |
| 📋 **Intake Agent** | Converts natural language → structured event profile | Llama 3.1 70B |
| 🍽️ **Menu Agent** | RAG-powered menu planning from knowledge base | Llama 3.1 70B |
| 📦 **Inventory Agent** | Ingredient mapping, shortage detection, procurement | Llama 3.1 8B |
| 💰 **Pricing Agent** | Cost calculation, margin analysis, budget feasibility | Llama 3.1 8B |
| 🔍 **Monitoring Agent** | Risk detection, autonomous re-planning trigger | Llama 3.1 70B |

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | **Microsoft Agent Framework (MAF) v1.0** |
| LLM Inference | **NVIDIA NIM API** (OpenAI-compatible) |
| RAG / Knowledge Base | **Azure AI Search** (semantic ranking) |
| Shared Agent Memory | **Azure Cosmos DB** |
| UI | **Streamlit** |
| Language | **Python 3.11+** |

---

## Key Features

- ✅ **True multi-agent orchestration** — 5 agents with distinct roles, structured JSON handoffs
- ✅ **RAG-grounded outputs** — Menu Agent queries Azure AI Search knowledge base (25 dishes, 12 suppliers, 8 dietary rules, 6 event templates)
- ✅ **Shared memory** — All agents read/write a single EventState document in Cosmos DB
- ✅ **Autonomous recovery** — Monitoring Agent detects failures (shortages, budget conflicts) and triggers automatic re-planning
- ✅ **Live agent log** — Every agent action is visible in real-time in the UI
- ✅ **Model-agnostic** — Swap NVIDIA NIM for Azure OpenAI in one config line

---

## Quick Start

### Prerequisites
- Python 3.11+
- Azure account (free tier sufficient for AI Search + Cosmos DB)
- NVIDIA NIM API key (free tier available at build.nvidia.com)

### Setup

```bash
# 1. Clone and install
git clone https://github.com/smilewithkhushi/orchefai
cd orchefai
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Index knowledge base into Azure AI Search
python setup/index_knowledge_base.py

# 4. Run the app
streamlit run app.py
```

---

## Demo Scenarios

### Scenario 1 — Happy Path
```
"Plan a halal vegetarian lunch for 150 guests at our office next Thursday, budget $6,000"
```
→ Full pipeline runs, complete catering plan generated

### Scenario 2 — Recovery Loop (The Wow Moment)
```
"Halal dinner for 200 guests this Saturday, $12,000 budget"
```
→ Inventory Agent detects lamb shortage (only 120 portions available)
→ Monitoring Agent flags HIGH RISK
→ System auto-replans with chicken/tofu substitution
→ New plan delivered with updated cost breakdown

### Scenario 3 — Budget Conflict
```
"Premium gala dinner for 100 guests, budget $10,000"
```
→ Pricing Agent calculates actual cost: $15,000
→ Monitoring Agent flags budget shortfall
→ System suggests either budget revision or simplified menu options

---

## Market Context

- **$2.14B** catering software market (2024), growing at **13.2% CAGR**
- **20 hours/week** saved per catering operations manager
- **$8 ROI** for every $1 invested in catering waste reduction (NRA)
- **Zero** production-grade multi-agent AI systems exist for this space today

---

## Architecture

```
User Input (NL)
      ↓
 IntakeAgent → EventState.customer (Cosmos DB)
      ↓
 [MenuAgent ║ InventoryAgent] → Parallel execution
      ↓
 PricingAgent → Cost breakdown + margin
      ↓
 MonitoringAgent → Risk check
      ↓ (if HIGH risk)
 [Recovery Loop] → Re-run Menu + Inventory with constraints
      ↓
 Final Catering Plan (JSON + human-readable)
```

---

## Team
Built for CWB Hackathon 2026 — iNextLabs Problem Statement