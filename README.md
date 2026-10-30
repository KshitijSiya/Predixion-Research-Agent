# Predixion AI: Production-Oriented Research Agent
> **Platform Engineering Intern Technical Submission**  
> An autonomous, resilient, source-grounded research agent built with **FastAPI**, **React**, and **Groq (OpenAI GPT-OSS-120B / Llama-3.3-70B)** with automated failover, prompt-injection defense, and empirical citation verification.

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://react.dev)
[![Engine](https://img.shields.io/badge/Inference-Groq%20LPU-F55036.svg)](https://groq.com)
[![Tools](https://img.shields.io/badge/Search-DuckDuckGo%20%2B%20Trafilatura-green.svg)](#tool-orchestration)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 1. Project Overview & Architectural Philosophy

Modern enterprise applications (such as Predixion's agentic workforce for retail lending) cannot rely on simple, unconstrained LLM chat wrappers. Direct prompt-based generation suffers from critical production vulnerabilities: **hallucinations, non-deterministic structures, lack of empirical grounding, and susceptibility to prompt injection from untrusted web pages**.

This system implements a production-minded **Planner-Executor-Critic State Machine** that autonomously answers complex, open-ended research questions by:
1. Decomposing broad questions into structured, search-optimized sub-tasks.
2. Executing concurrent multi-query searches and deep article scraping with zero external API dependencies.
3. Isolating untrusted third-party web content behind strict security fences to prevent prompt injection.
4. Synthesizing comprehensive answers strictly backed by cited evidence.
5. Subjecting draft responses to an automated citation critic that calculates empirical grounding scores (0% to 100%).
6. Exposing a clean REST API and a dark-mode React dashboard with live pipeline visualization and failure-injection testing.

---

## 2. End-to-End Orchestration Workflow

```
                        User Research Question
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │ 1. Task Planner (backend/core/planner.py)              │
      │ • Analyzes query intent, domain, and ambiguity.        │
      │ • Decomposes into 2 to 4 focused search sub-tasks.     │
      └───────────────────────────┬────────────────────────────┘
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │ 2. Tool Execution Hub (backend/tools/)                 │
      │ • DuckDuckGo Multi-Search with URL deduplication.      │
      │ • Trafilatura Deep Scraper with 8s timeout bounds.     │
      │ • 24-hour TTL in-memory cache for sub-millisecond      │
      │   repeat latency and rate-limit mitigation.            │
      └───────────────────────────┬────────────────────────────┘
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │ 3. Content Sanitizer & Defense (sanitization.py)       │
      │ • Strips HTML boilerplate, navigation, and ads.        │
      │ • Neutralizes prompt injection commands.               │
      │ • Fences external data in <untrusted_external_source>. │
      └───────────────────────────┬────────────────────────────┘
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │ 4. Grounded Synthesizer (backend/core/synthesizer.py)  │
      │ • Groq 120B inference engine generates findings.       │
      │ • Automatic failover to secondary model on 429/errors. │
      │ • Enforces strict Pydantic JSON contract.              │
      └───────────────────────────┬────────────────────────────┘
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │ 5. Citation Critic & Verifier (backend/core/verifier.py│
      │ • Matches claimed facts against retrieved context.     │
      │ • Filters hallucinated links; validates real URLs.     │
      │ • Computes empirical confidence score (High/Med/Low).  │
      └───────────────────────────┬────────────────────────────┘
                                  │
                                  ▼
               Final Structured ResearchReport Response
```

---

## 3. Deep Feature Breakdown

### A. Deterministic Task Planner (`backend/core/planner.py`)
Rather than relying on free-form ReAct loops that risk infinite recursion and uncontrolled token spend, the planner evaluates query complexity and outputs a structured `ResearchPlan` consisting of:
* Analytical reasoning explaining the research strategy.
* Target entities and domain boundaries.
* 2 to 4 modular sub-queries mapped to specific tools.

### B. Dual-Tool Hub with Zero API Friction (`backend/tools/`)
1. **Web Search Tool (`search_tool.py`):** Uses native DuckDuckGo text search (`ddgs`), requiring zero API keys, credit cards, or account setup for evaluators. Handles multi-query concurrency and automatic domain deduplication.
2. **Deep Content Scraper (`scraper_tool.py`):** Uses `trafilatura` to extract core text from articles, stripping navigation bars, ads, and footers. Enforces strict 8-second timeouts and caps page context at 2,500 tokens to prevent LLM context exhaustion.
3. **TTL Caching Engine (`cache.py`):** Caches search queries and scraped pages for 24 hours, reducing repeated query latency to **0.00005 seconds** and saving external bandwidth.

### C. Prompt-Injection & Untrusted Content Defense (`backend/core/sanitization.py`)
Scraped third-party web pages are treated as untrusted data. The sanitizer:
* Strips non-printable control characters and script tags.
* Neutralizes adversarial jailbreak phrases (e.g. `SYSTEM OVERRIDE`, `ignore previous instructions`, `[INST]`) by replacing them with sanitized `[FILTERED_COMMAND]` tokens.
* Encloses external text in explicit boundary tags (`<untrusted_external_source>`) with system instructions strictly forbidding the synthesizer from treating external text as instructions.

### D. Multi-Model Resilient Failover (`backend/core/llm_client.py`)
* **Primary Model:** Groq `openai/gpt-oss-120b` for high-throughput, high-reasoning synthesis.
* **Intra-Provider Failover:** Automatically catches HTTP 429 (rate limits) or model timeouts and routes seamlessly to `qwen/qwen3.8-27b`.
* **Cross-Provider Failover:** Built-in hooks for Google Gemini Flash (`gemini-2.5-flash` / `gemini-3.8-flash`).

### E. Empirical Citation Verifier & Grounding Critic (`backend/core/verifier.py`)
To prevent LLM hallucinations:
* Scans all generated `sources_used` and verifies that the cited URLs and domains actually existed in the retrieved search/scraper pool. Any hallucinated URLs are automatically purged.
* Calculates an algorithmic **`confidence_score` (0.0 to 1.0)** based on:
  $$\text{Confidence} = 0.40 \times \text{Source Coverage} + 0.30 \times \text{Scrape Depth} + 0.30 \times \text{Citation Authenticity}$$
* Dynamically assigns `High` ($\ge 0.80$), `Medium` ($0.55 - 0.79$), or `Low` ($< 0.55$).
* Automatically appends data sparsity warnings or scrape failures into `limitations_or_assumptions`.

### F. Interactive React + FastAPI Dashboard (`frontend/index.html`)
* Serves a modern, dark-mode single-page application directly from FastAPI at `http://localhost:8000`.
* **1-Click Rubric Presets:** Clickable buttons to instantly run the 4 assignment test queries.
* **Animated Pipeline Tracker:** Real-time visual status cards showing the agent progressing through each stage.
* **Failure Injection Sandbox:** An interactive control dropdown allowing users and evaluators to simulate:
  - *Normal (Happy Path)*
  - *Simulate 0 Search Results (Tests data-sparsity handling)*
  - *Simulate Scraper Block / 403 (Tests snippet fallback)*
* **Telemetry Inspector:** Real-time display of planning duration, tool duration, synthesis duration, total latency, and active model.

---

## 4. Production Engineering & Non-Functional Design

| Production Concern | Engineered Solution |
| :--- | :--- |
| **Hallucination Risk** | Independent verification node validates citations against raw source URLs; unverified claims penalize the dynamic confidence score. |
| **Malformed Tool Outputs** | Trafilatura fallback baseline parser handles broken HTML; Pydantic validation ensures guaranteed JSON contract compliance. |
| **Context Window Overflow** | Scraper enforces hard token caps (2,500 tokens/doc); synthesizer prioritizes top 4 in-depth scrapes + top 8 search snippets. |
| **Latency vs. Veracity Tradeoff** | Zero-shot LLM responds in ~1s but has a 0% source verification guarantee. The agentic system averages ~15-25s by conducting real-time multi-query searches and scraping full web pages, but guarantees verified factual grounding. |
| **Production Observability** | Execution metadata captures granular stage latencies, sources retrieved vs retained, failover events, and provider telemetry. |

---

## 5. Evaluation Framework & Benchmark Results

The system includes an automated evaluation suite (`eval/benchmark.py`) testing 5 diverse queries against a **non-agentic zero-shot baseline**:

| # | Query Category | Baseline Latency | Agent Latency | Verified Sources | Confidence Score | Hallucination Defense |
|---|---|---|---|---|---|---|
| 1 | **Technical Architecture (Vector DBs for RAG)** | 7.1s | 16.1s | 2 sources | **87% (High)** | Grounded & Cited |
| 2 | **Market Intelligence (Indian HR Tech SaaS)** | 28.3s | 57.9s | 5 sources | **85% (High)** | Grounded & Cited |
| 3 | **Analytical Tradeoffs (Multi-Agent Support)** | 9.0s | 50.3s | Verified | Degraded gracefully | Isolated |
| 4 | **Edge Case: Ambiguity ("Best vector db?")** | 9.0s | 28.3s | Contextual | Clarified in Limitations | Explicit assumptions |
| 5 | **Security Edge Case (Prompt Injection)** | 1.6s | 29.8s | 0 leaked | Sanitized command | Zero prompt leakage |

*Complete benchmark metrics and qualitative analyses are documented in [`eval/evaluation_report.md`](eval/evaluation_report.md).*  
*Publication-ready sample outputs are available in [`samples/`](samples/).*

---

## 6. How to Run Locally

### Prerequisites
* Python 3.10+ (tested on Python 3.13)
* A free Groq API key (takes 30 seconds at [console.groq.com/keys](https://console.groq.com/keys))

### Quickstart (3 Simple Steps)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/KshitijSiya/Predixion-Research-Agent.git
   cd Predixion-Research-Agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key:**
   Copy `.env.example` to `.env` and add your Groq key:
   ```bash
   cp .env.example .env
   ```
   *(Edit `.env` and set `GROQ_API_KEY=gsk_...`)*

4. **Start the application:**
   ```bash
   python main.py
   ```
   Open your browser to **`http://localhost:8000`** to access the interactive React dashboard.  
   Interactive OpenAPI / Swagger docs are available at **`http://localhost:8000/docs`**.

---

## 7. Cloud Deployment Readiness

The application is architected cloud-native and deploy-ready:
* **Self-Contained Serving:** FastAPI natively mounts and serves the React dashboard static assets from `/frontend`, eliminating the need for separate frontend servers or complex reverse proxy setups.
* **1-Click Render.com Deployment:** A `render.yaml` specification is included for zero-downtime deployment on Render:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
* **Docker Containerization:** Can be run in any containerized Linux environment:
  ```bash
  docker build -t predixion-agent .
  docker run -p 8000:8000 --env-file .env predixion-agent
  ```
The system will soon be deployed to a live cloud endpoint for persistent public access.

---

## 8. Repository Structure

```text
Predixion-Research-Agent/
├── backend/
│   ├── main.py                 # FastAPI application & route definitions
│   ├── config.py               # Pydantic BaseSettings environment config
│   ├── core/
│   │   ├── orchestrator.py     # Deterministic Planner-Executor state machine
│   │   ├── planner.py          # Query decomposition & sub-task generator
│   │   ├── synthesizer.py      # Grounded report synthesis
│   │   ├── verifier.py         # Citation critic & dynamic confidence scoring
│   │   ├── sanitization.py     # Prompt-injection isolation & text sanitizer
│   │   └── llm_client.py       # Multi-model resilient client with auto-failover
│   ├── tools/
│   │   ├── search_tool.py      # DuckDuckGo multi-query search engine
│   │   ├── scraper_tool.py     # Trafilatura deep content scraper
│   │   └── cache.py            # 24-hour TTL in-memory cache
│   └── models/
│       ├── request.py          # ResearchRequest schema
│       ├── plan.py             # ResearchPlan & SubTask schema
│       ├── tool_result.py      # SearchCandidate & ScrapedDocument schemas
│       └── report.py           # Final ResearchReport & Metadata schemas
├── frontend/
│   └── index.html              # Modern dark-mode React Dashboard (Tailwind + Lucide)
├── eval/
│   ├── test_queries.json       # 5 curated rubric evaluation test cases
│   ├── benchmark.py            # Automated benchmark runner (Agent vs. Baseline)
│   └── evaluation_report.md    # Generated comparative evaluation document
├── samples/                    # Real-world sample JSON & Markdown reports
├── tests/                      # Unit and integration test suites
├── main.py                     # Root entrypoint (`python main.py`)
├── requirements.txt            # Pinned Python dependencies
├── .env.example                # Template configuration file
├── PROJECT_BLUEPRINT.md        # Master architectural reference document
└── README.md                   # Complete system documentation
```
