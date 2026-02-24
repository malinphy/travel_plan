# Project Summary: Travel Plan - Multi-Agent Travel Assistant

## Overview
The `travel_plan` repository is a sophisticated **Multi-Agent Travel Assistant** designed to handle complex travel queries. It leverages a combination of planning agents and specialized tool-using agents to provide flight, hotel, and restaurant recommendations, moving beyond simple single-turn responses to multi-step execution.

---

## Core System Architecture

### 1. Orchestration (`main.py`)
- **`TravelChatbot` Class**: The central controller managing conversation state and history.
- **Workflow**:
    1. **Planning**: A `planner_agent` analyzes the user's query and generates a step-by-step execution plan as a JSON object.
    2. **Execution**: The `help_desk_agent` follows the plan, calling specialized sub-agents.

### 2. Specialized Agents (`helpers/`)
- **`planner_agent`**: Breaks down complex requests into logical sequences (e.g., flight search -> hotel search -> price comparison).
- **`f_agent` (Flight Assistant)**: Specialized in finding real-time tickets using Google Flights.
- **`h_agent` (Hotels Assistant)**: Specialized in lodging search via Google Hotels.
- **`y_agent` (Yelp Search)**: Recommends restaurants and local activities.
- **`query_rewrite`**: Decomposes intricate queries into simpler sub-questions to ensure all user constraints are addressed.

### 3. Built-in Tools (`helpers/function_tools.py`)
- **External API Integrations**: Powered by **SerpAPI** for live access to travel data.
- **Local Data**: Includes a CSV-based mapping system to resolve city names to IATA airport codes.
- **Visual Utilities**: `ticket_to_markdown` generates simulated boarding passes for a better user experience in notebook environments.

---

## Data & Reliability (`data_models/`)
The project maintains high reliability through **Pydantic Data Models**. Every interaction, from planning (`ChainOfThought`) to API responses (`FlightSearchResults`, `Property`), is structured and validated, ensuring the system can handle errors and inconsistent API outputs gracefully.

---

## Interfaces

### Web Frontend (`fe/`)
- **Technology Stack**: HTML, CSS, Vanilla JavaScript.
- **Features**: A modern, clean chat interface with a dual-pane layout for displaying chat and visual results.
- **Backend Bridge**: A **FastAPI** server that facilitates communication between the UI and the LLM (specifically configured for Google's **Gemini 2.0 Flash**).

### Developer Tools
- **Benchmark Suite**: The `README.md` acts as a testing ground with 20 categorized user queries (Simple vs. Complex).
- **Interactive CLI**: `main.py` provides a direct interactive loop for testing agents in the terminal.

---

## Dependencies & Setup
- **Keys Required**: OpenAI, Gemini (for FE), and SerpAPI.
- **Key Libraries**: `openai-agents`, `fastapi`, `pydantic`, `serpapi`, `google-genai`.
