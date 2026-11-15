# 🌍 WanderWise: Agentic AI-Based Travel Planning Assistant Using LangChain

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-1C3C3C?style=flat)](https://www.langchain.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Qwen%202.5%207B-000000?style=flat)](https://ollama.com/)
[![PostgreSQL](https://img.shields.io/badge/Neon_Tech-PostgreSQL_18-00E599?style=flat&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)

An autonomous, multi-tool **Agentic AI Travel Assistant** built with **LangChain**, local open-source LLMs (**Qwen 2.5 7B** via Ollama), **Neon Tech PostgreSQL**, and a responsive **Streamlit** dashboard.

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

## 🚀 5. Getting Started & Installation

### Prerequisites
* **Python 3.11+**
* **Ollama** installed with `qwen2.5:7b`:
  ```bash
  ollama run qwen2.5:7b
  ```

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

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Update your `.env` with your Neon Tech PostgreSQL connection URL:
```env
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql://username:password@ep-xyz.region.aws.neon.tech/neondb?sslmode=require
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
```

### Step 4: Seed the Neon PostgreSQL Database
Run the idempotent seeding migration script to populate flights, hotels, and places into Neon Tech:
```bash
python -m src.database.seed_data
```

### Step 5: Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🧪 6. Testing & Persona Validation

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

## 📂 7. Project Structure

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

## 🏆 8. Evaluation Criteria Checklist

- [x] **Clear Problem Statement & Business Use Cases:** Documented in README and project brief.
- [x] **Agentic AI Workflow:** Autonomous decision-making using LangChain ReAct agent graph.
- [x] **Tool Integration:** 5 custom tools (Flights, Hotels, Places, Open-Meteo Weather, Budget).
- [x] **SQL Database Best Practices:** Normalized tables, B-tree composite indexing, and SQLAlchemy pooling with **Neon Tech PostgreSQL**.
- [x] **Anti-Hallucination Guardrails:** Deterministic Python budget computation preventing LLM math errors.
- [x] **Streamlit Web Application:** Interactive dashboard, real-time step visualizer (`st.status`), Dark Mode styling, and offline downloads.
- [x] **Code Quality & Documentation:** PEP 8 compliance, comprehensive type annotations, modular architecture, and automated test suites.
