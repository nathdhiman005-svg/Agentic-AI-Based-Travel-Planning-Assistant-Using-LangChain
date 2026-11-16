# 🌍 WanderWise: Agentic AI-Based Travel Planning Assistant Using LangChain

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-1C3C3C?style=flat)](https://www.langchain.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Qwen%202.5%207B-000000?style=flat)](https://ollama.com/)
[![PostgreSQL](https://img.shields.io/badge/Neon_Tech-PostgreSQL_18-00E599?style=flat&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)

An autonomous, multi-tool **Agentic AI Travel Assistant** built with **LangChain**, local open-source LLMs (**Qwen 2.5 7B** via Ollama), **Neon Tech PostgreSQL**, and a responsive **Streamlit** dashboard.

---

### ⚠️ CRITICAL NOTICE: Local LLM Required (Please Read Before Testing)

[![Deployment Notice: Local LLM Required](https://img.shields.io/badge/%E2%9A%A0%EF%B8%8F%20DEPLOYMENT%20NOTICE-LOCAL%20LLM%20REQUIRED%20(OLLAMA)-critical?style=for-the-badge&logo=ollama&logoColor=white)](#-5-ollama-installation--local-model-setup)


> **Cloud Deployments (Streamlit Community Cloud / Render) will NOT generate itineraries out of the box.**  
> WanderWise is powered by a **local open-source LLM (`qwen2.5:7b` via Ollama on `localhost:11434`)** for 100% data privacy and zero API costs, rather than a commercial cloud API. Because cloud servers cannot connect to your personal PC's `localhost`, a cloud deployment cannot invoke the local agent.  
>  
> 💻 **To test and experience the full agentic AI workflow, please run WanderWise locally on your computer:**  
> - 🦙 **Step 1:** Follow the [**Ollama Installation & Model Setup Guide**](#-5-ollama-installation--local-model-setup) to start Ollama and pull `qwen2.5:7b`.  
> - 🚀 **Step 2:** Follow the [**Project Setup & Quick Start Guide**](#-6-project-setup--quick-start-guide) to launch the Streamlit dashboard on `localhost:8501`.

| 🚨 Alert | **Local LLM Configuration Details** |
| :--- | :--- |
| **Why Cloud Fails** | Cloud hosting instances cannot reach `localhost:11434` on your local PC. |
| **How to Run** | Clone this repository, start Ollama with `qwen2.5:7b`, and run `streamlit run app.py`. See [**Setup Guide**](#-6-project-setup--quick-start-guide). |

---

## 📌 1. Project Overview & Problem Statement

Planning a trip requires coordinating flights, accommodations, sightseeing agendas, and daily budgets while navigating real-world constraints such as changing weather, transit times, and financial ceilings. Travelers often juggle multiple aggregators, leading to suboptimal or fragmented plans.

**WanderWise** solves this through an autonomous ReAct tool-calling agent that acts like an expert travel consultant:
1. Gathers live weather forecasts from **Open-Meteo**.
2. Searches and ranks direct flights from a normalized database.
3. Selects top-rated accommodations adhering to nightly price caps.
4. Curates day-by-day sightseeing agendas logically distributed across mornings, afternoons, and evenings.
5. Computes mathematically verified budgets and evaluates feasibility against user financial ceilings.
6. Allows interactive, multi-turn plan refinement via conversational memory.

---

## 🏗️ 2. System Architecture

```mermaid
flowchart TD
    User([Traveler / User]) --> UI[Streamlit Interactive Application]
    UI --> Controller[Travel Planner Controller]

    subgraph Agent_Core [LangChain Agentic Reasoning Core]
        Controller --> Agent[LangChain ReAct / Tool-Calling Agent]
        Agent <--> LLM[Local Qwen 2.5 7B via Ollama]
        Agent <--> Prompt[System Prompt & Explainability Rules]
        Agent <--> Memory[Session-Keyed Conversation Memory]
    end

    subgraph Tools_Layer [Specialized Agent Tools]
        Agent --> T_Weather[🌦️ get_weather_forecast]
        Agent --> T_Flight[✈️ search_flights]
        Agent --> T_Hotel[🏨 recommend_hotels]
        Agent --> T_Places[🏛️ discover_places]
        Agent --> T_Budget[💰 calculate_budget]
    end

    subgraph Data_Layer [Data & Cloud Persistence]
        T_Weather --> API_W[Open-Meteo Live API - Keyless]
        T_Flight --> DB_F[(Neon PostgreSQL - flights)]
        T_Hotel --> DB_H[(Neon PostgreSQL - hotels)]
        T_Places --> DB_P[(Neon PostgreSQL - places)]
        Controller -.-> DB_S[(Neon PostgreSQL - saved_itineraries & query_logs)]
    end

    Agent --> Parser[Resilient Pydantic Itinerary Parser]
    Parser --> UI
```

---

## 🗄️ 3. Database Schema & Indexing (Neon Tech PostgreSQL)

The project leverages **Neon Tech Serverless PostgreSQL** for both relational catalog inventory and application persistence:

* **`flights` table:** Indexed on `(from_city, to_city, price)` for sub-millisecond route matching.
* **`hotels` table:** Indexed on `(city, stars, price_per_night)` for instant star and budget filtering.
* **`places` table:** Indexed on `(city, rating)` for descending popularity ordering.
* **`saved_itineraries` table:** Stores finalized user trip plans with session UUIDs and JSON payloads.
* **`query_logs` table:** Records agent execution telemetry, tools invoked, latency, and status.

---

## 🛠️ 4. Specialized Agent Tools

| Tool | Purpose | Source | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **`get_weather_forecast`** | Live climate lookup | Open-Meteo API | Geocoding lookup, WMO weather interpretation, rain advisories |
| **`search_flights`** | Route search & ranking | Neon PostgreSQL | Dual-mode sorting: `cheapest` vs. `fastest`, highlight badges |
| **`recommend_hotels`** | Lodging recommendations | Neon PostgreSQL | Star filter ($\ge 3, 4, 5$), budget limits, amenity matching |
| **`discover_places`** | Sightseeing discovery | Neon PostgreSQL | Category filtering (*temple*, *fort*, *museum*), rating ranking |
| **`calculate_budget`** | Deterministic arithmetic | Python Math Engine | Room scaling, multi-passenger math, budget surplus/deficit |

---

## 🦙 5. Ollama Installation & Local Model Setup

This project is powered by **Qwen 2.5 7B** running 100% locally on your machine via **Ollama** (free, private, fast inference, and zero cloud API fees).

### 5.1 Download & Install Ollama
* **Windows:** Download and run [`OllamaSetup.exe`](https://ollama.com/download/windows). Follow the guided installer. After setup, Ollama automatically runs in the background system tray.
* **macOS:** Download the installer from [`ollama.com/download/mac`](https://ollama.com/download/mac) or install via Homebrew:
  ```bash
  brew install ollama
  ```
* **Linux:** Install via the official one-line script:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

### 5.2 Verify Ollama Installation
Open your terminal (PowerShell, Command Prompt, or bash) and verify the installation:
```bash
ollama --version
```
*(Ollama automatically initializes its local REST server at `http://localhost:11434`)*

### 5.3 Download / Pull the Qwen 2.5 7B Model
Download the 4-bit quantized model weights (~4.7 GB), which are optimized for 8 GB VRAM GPUs like the RTX 4060:
```bash
ollama pull qwen2.5:7b
```
To confirm the model has downloaded successfully:
```bash
ollama list
```
*(You will see `qwen2.5:7b` listed with size ~4.7 GB)*

### 5.4 Test Run the Model Locally
Run an interactive session in your terminal to ensure the model responds:
```bash
ollama run qwen2.5:7b
```
Type any prompt (e.g. `Hello! Ready to plan travel?`), confirm the response, and exit by typing `/bye`.

### 5.5 Verify GPU Acceleration (NVIDIA CUDA)
While Ollama is running or when generating an itinerary, check that the model is loaded directly into GPU VRAM:
```bash
ollama ps
```
You will observe:
```
NAME          ID              SIZE      PROCESSOR    CONTEXT
qwen2.5:7b    845dbda0ea48    4.8 GB    100% GPU     8192
```
`100% GPU` confirms that inference is running purely on your GPU (e.g. NVIDIA RTX 4060) with sub-second token generation.

---

## 🚀 6. Project Setup & Quick Start Guide

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone <your-repo-url>
cd "Agentic AI-Based Travel Planning Assistant Using LangChain"

python -m venv .venv
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Ensure your `.env` contains:
```env
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql://username:password@ep-xyz.region.aws.neon.tech/neondb?sslmode=require
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
```

### Step 4: Seed the Neon PostgreSQL Database
Run the idempotent seeding migration script to populate initial flights, hotels, and attractions into Neon Tech:
```bash
python -m src.database.seed_data
```

### Step 5: Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser to start planning trips!

---

## 🧪 7. Testing & Persona Validation

### Run Edge-Case Unit Tests
Validates route unavailability, weather fallbacks, strict hotel filters, and parser resilience:
```bash
python -m unittest tests/test_fallbacks.py
```

### Run End-to-End Persona Validation Suite
Simulates 3 diverse real-world traveler personas against the live agent:
```bash
python -m tests.validate_personas
```

| Persona | Origin $\rightarrow$ Destination | Travelers | Target Budget | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Solo Budget Traveler** | Hyderabad $\rightarrow$ Delhi (3 Days) | 1 Pax | ₹12,000 | **PASSED** (Total: ₹8,500) |
| **Family Vacation** | Delhi $\rightarrow$ Kolkata (4 Days) | 3 Pax | ₹40,000 | **PASSED** (Scaled 2 rooms) |
| **Cultural Explorer** | Delhi $\rightarrow$ Jaipur (3 Days) | 2 Pax | ₹20,000 | **PASSED** (Cultural agenda) |

---

## 📂 8. Project Structure

```
.
├── data sources/                 # Initial mock catalog data
│   ├── flights.json
│   ├── hotels.json
│   └── places.json
├── src/
│   ├── agents/                   # Agent orchestration & schemas
│   │   ├── prompts.py            # WanderWise persona & decision rules
│   │   ├── schemas.py            # Pydantic structured output models
│   │   └── travel_agent.py       # LangChain agent graph & memory
│   ├── database/                 # Database & ORM models
│   │   ├── db_connection.py      # SQLAlchemy connection pool
│   │   ├── db_service.py         # Unified query & fallback service
│   │   ├── models.py             # Neon Tech PostgreSQL ORM models
│   │   ├── schemas.py            # Pydantic data models
│   │   └── seed_data.py          # Database seeding migration script
│   ├── tools/                    # Specialized LangChain tools
│   │   ├── budget_tool.py        # Arithmetic & budget calculation
│   │   ├── flight_tool.py        # Flight search & ranking
│   │   ├── hotel_tool.py         # Hotel recommendation
│   │   ├── places_tool.py        # Points of interest discovery
│   │   └── weather_tool.py       # Open-Meteo live API client
│   ├── ui/                       # Streamlit component library
│   │   └── components.py         # Modular cards, timeline & budget chart
│   └── utils/                    # Utility & configuration helpers
│       └── config.py             # Settings manager
├── tests/                        # Automated unit & persona tests
│   ├── test_fallbacks.py         # Edge case unit test suite
│   └── validate_personas.py      # Multi-scenario persona test suite
├── app.py                        # Streamlit web application entry point
├── requirements.txt              # Pinned Python package dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # Comprehensive project documentation
```

---

## 🏆 9. Evaluation Criteria Checklist

* ✅ **Clear Problem Statement & Business Use Cases:** Thoroughly documented in README and project brief.
* ✅ **Agentic AI Workflow:** Autonomous decision-making using LangChain ReAct agent graph with tool calling.
* ✅ **Tool Integration:** 5 custom tools (Flights, Hotels, Places, Open-Meteo Weather, Budget).
* ✅ **SQL Database Best Practices:** Normalized relational tables, B-tree composite indexing, and SQLAlchemy pooling with **Neon Tech PostgreSQL**.
* ✅ **Anti-Hallucination Guardrails:** Deterministic Python budget computation preventing LLM math errors.
* ✅ **Streamlit Web Application:** Interactive dashboard, real-time step visualizer (`st.status`), Dark Mode styling, and offline exports.
* ✅ **Code Quality & Documentation:** PEP 8 compliance, comprehensive type annotations, modular architecture, and automated test suites.
