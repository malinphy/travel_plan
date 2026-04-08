# AI Travel Agent

A conversational travel planning assistant powered by a multi-agent AI system. Search for flights, hotels, and restaurants through a natural chat interface — with a basket to collect your picks before booking.

### Demo
<video src="https://raw.githubusercontent.com/malinphy/travel_plan/main/assets/travel_agent.mp4" type="video/mp4" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

---

## Features

- **Multi-agent architecture** — a Supervisor routes requests to specialized sub-agents (Flight, Hotel, Yelp, Booking) and synthesizes their responses
- **Flight search** — real-time results via Google Flights (SerpAPI), filterable by price, stops, and duration
- **Hotel search** — real-time results via Google Hotels with ratings, amenities, and cancellation info
- **Restaurant search** — Yelp-powered local business discovery
- **Basket management** — add/remove/modify flights and hotels across a conversation
- **Multi-thread conversations** — multiple independent chat sessions per user, with full history
- **Persistent sessions** — conversations survive page reloads, backed by SQLite
- **ChatGPT-style UI** — sidebar thread list, rich result carousels, dark/light theme

---

## Architecture

```
User Message
     │
     ▼
SupervisorAgent  (gpt-4.1)
     │
     ├──► FlightAgent   (gpt-4.1)    → search_flights, query_flight_options   → SerpAPI Google Flights
     ├──► HotelAgent    (gpt-4o-mini) → search_hotels, query_hotel_options     → SerpAPI Google Hotels
     ├──► YelpAgent     (gpt-4.1)    → search_yelp, query_yelp_options         → SerpAPI Yelp
     └──► BookingAgent  (gpt-4o-mini) → get/view/add/remove basket items
```

The Supervisor analyses each message for domain signals and calls only the relevant agents — it never assumes the user wants hotels just because they asked about flights.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Uvicorn |
| AI Agents | OpenAI Agents SDK (`openai-agents`) |
| LLM Models | GPT-4.1, GPT-4o-mini |
| External Data | SerpAPI (Google Flights, Google Hotels, Yelp) |
| Database | SQLAlchemy + SQLite |
| Frontend | Vanilla JavaScript + Tailwind CSS |

---

## Project Structure

```
.
├── main.py                  # FastAPI app — endpoints, session management
├── orchestrator.py          # Agent definitions and supervisor setup
├── requirements.txt
│
├── backend/
│   ├── agents/
│   │   ├── flight/          # Flight search tools
│   │   ├── hotel/           # Hotel search tools
│   │   ├── yelp/            # Restaurant search tools
│   │   └── booking/         # Basket management tools
│   └── context/
│       ├── travel_context.py    # TravelContext dataclass (per-session state)
│       └── context_control.py   # Conversation history utilities
│
├── database/
│   ├── schema.py            # SQLAlchemy models (8 tables)
│   └── history.py           # Conversation message persistence
│
├── model_configs/
│   └── agent_configs.py     # Model and temperature config per agent
│
└── frontend/
    ├── index.html
    └── app.js               # Chat UI, carousels, basket modal
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- API keys for [OpenAI](https://platform.openai.com) and [SerpAPI](https://serpapi.com)

### 1. Clone and install

```bash
git clone https://github.com/your-username/adtech.git
cd adtech
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=your_openai_key
SERPAPI_API_KEY=your_serpapi_key
```

### 3. Start the backend

```bash
python main.py
```

API runs at `http://localhost:8001`. Interactive docs at `http://localhost:8001/docs`.

### 4. Serve the frontend

```bash
cd frontend
python -m http.server 3000
```

Open `http://localhost:3000` in your browser.

---

## Example Queries

```
"Find me flights from Istanbul to Paris on April 20th, returning April 27th"
"Show hotels in Paris for those dates under $200 a night"
"Find a good pizza place near the Eiffel Tower"
"Add the cheapest flight to my basket"
"What's in my basket?"
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/query` | Send a message to the travel agent |
| `GET` | `/threads` | List all conversation threads for a user |
| `GET` | `/threads/{thread_id}` | Get messages in a thread |
| `GET` | `/flights` | Get flight results for a session |
| `GET` | `/hotels` | Get hotel results for a session |
| `GET` | `/yelp` | Get restaurant results for a session |
| `GET` | `/basket` | Get basket contents for a session |

All endpoints are scoped by `user_id` and `thread_id` query parameters — no data leaks between users or conversations.

---

## Database Schema

Eight tables with full user and thread isolation:

```
User ──< ConversationState
     ──< ContextMessage
     ──< FlightSearch ──< FlightOption
     ──< HotelSearch  ──< HotelOption
     ──< YelpSearch   ──< YelpOption
     ──< Basket       ──< BasketItem
```

---

## Known Limitations

- **No authentication** — user identity is a client-generated ID stored in `localStorage`. Suitable for demos; not for production.
- **SQLite** — single-writer limitation under concurrent load. Swap for PostgreSQL for production use.
- **In-memory session cache** — sessions are lost on server restart (history is recovered from DB, but in-flight context is not).
