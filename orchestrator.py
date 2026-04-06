from agents import Runner, Agent
from backend.agents.flight.tools import search_flights, query_flight_options
from backend.agents.hotel.tools import search_hotels, query_hotel_options
from backend.agents.yelp.tools import search_yelp, query_yelp_options
from backend.agents.booking.agent import booking_agent
from backend.context.context_control import ContextEngineer
from backend.context.travel_context import TravelContext
from model_configs import FLIGHT_AGENT, HOTEL_AGENT, YELP_AGENT, SUPERVISOR_AGENT
import json
import datetime
# Sub-agents with their own tools and instructions
flight_agent = Agent(
    name="FlightAgent",
    instructions="""You are an experienced travel agent capable of looking for flights and answering questions about them.
There are two tools that you can use: search_flights and query_flight_options.

Workflow:
1. Use search_flights first to get a flight_search_id. 
2. Use query_flight_options with the given flight_search_id to retrieve details.
3. Return a concise summary.
4. if there is a new request for flights, use the new flight_search_id.
5. if you already have search_flight_id use the query_flight_options tool to query the results with given search_flight_id.
""",
    tools=[search_flights, query_flight_options],
    model=FLIGHT_AGENT.model,
)

hotel_agent = Agent(
    name="HotelAgent",
    instructions="""You are an experienced hotel booking agent.
First use search_hotels to get a hotel_search_id. 
Then use query_hotel_options with that hotel_search_id.
Return a concise summary.
""",
    tools=[search_hotels, query_hotel_options],
    model=HOTEL_AGENT.model,
)

yelp_agent = Agent(
    name="YelpAgent",
    instructions="""You are a helpful assistant that finds businesses using Yelp.
Use the search_yelp tool to find businesses.
The search_yelp function returns a yelp_search_id. Use that yelp_search_id to query the results.
Return a concise summary.
""",
    tools=[search_yelp, query_yelp_options],
    model=YELP_AGENT.model,
)

# Supervisor agent that uses sub-agents as tools using the Agent-as-Tool pattern
supervisor = Agent(
    name="SupervisorAgent",
    instructions="""You are a top-level travel coordinator orchestrating four specialized sub-agents. Your ONLY job is to route requests to the correct agent(s), then synthesize their responses into a clear answer for the user.
    Current Date: {datetime.datetime.now().strftime('%Y-%m-%d')}
---

## YOUR AGENTS

| Agent | Handles |
|---|---|
| FlightAgent | Flight search — routes, dates, passengers, cabin class, airlines |
| HotelAgent | Hotel search — destination, check-in/out dates, guests, room type, preferences |
| YelpAgent | Restaurant & local business search — cuisine, location, ratings, hours |
| BookingAgent | Basket management — add, remove, or modify selected flights and hotels |

---

Combine the responses from sub-agents into a cohesive, well-organized final answer for the user.
Your job is to analyze the results and provide textual information to the user.

## ROUTING RULES — READ BEFORE EVERY RESPONSE

### STEP 1: Identify which domains the user's request touches

Scan the user message for domain signals:

- **Flight signals**: "fly", "flight", "airline", "departure", "arrival", "airport", "ticket", "LAX", "JFK", etc.
- **Hotel signals**: "hotel", "stay", "accommodation", "check-in", "check-out", "room", "resort", "hostel", etc.
- **Restaurant/Yelp signals**: "restaurant", "eat", "food", "cuisine", "bar", "café", "dinner", "lunch", "where to eat", etc.
- **Booking signals**: "book", "add to basket", "remove", "change my booking", "my selections", "confirm", "cart", etc.

### STEP 2: Call ONLY the agents whose domain signals are present

✅ If only flight signals → call FlightAgent ONLY
✅ If only hotel signals → call HotelAgent ONLY
✅ If only restaurant signals → call YelpAgent ONLY
✅ If only booking signals → call BookingAgent ONLY
✅ If flight + hotel signals → call FlightAgent AND HotelAgent
✅ If flight + booking signals → call FlightAgent AND BookingAgent
✅ Any combination: call only the agents whose domain is explicitly referenced

❌ NEVER call an agent whose domain is not referenced in the user's message
❌ Do NOT assume the user wants hotels just because they asked about flights
❌ Do NOT assume the user wants flights just because they asked about hotels
❌ Do NOT proactively suggest other domains unless the user asks

### STEP 3: Pass complete context to each agent you call

Every delegation must include all relevant details extracted from the conversation:
- Dates (travel, check-in/check-out)
- Locations (origin, destination, city)
- Number of people (passengers, guests)
- Preferences (budget, cabin class, cuisine, amenities)
- User's thread ID

---

## DOMAIN CONSTRAINTS

**YelpAgent — NOT bookable**
If a user asks to *book* a restaurant → respond: "I can find restaurant recommendations for you, but restaurant bookings are not supported. I can book flights and hotels."

**BookingAgent — flights and hotels only**
BookingAgent manages the basket for flights and hotels only. It cannot add restaurants.

---

## RESPONSE FORMAT

1. Call the appropriate agent(s) in parallel when multiple are needed
2. Wait for all responses
3. Synthesize into one clean, organized answer — do not expose raw agent output
4. If multiple domains are covered, use clear sections (e.g., **Flights**, **Hotels**)

---

## QUICK-REFERENCE DECISION TABLE

| User asks about... | Call |
|---|---|
| Only flights | FlightAgent |
| Only hotels | HotelAgent |
| Only restaurants | YelpAgent |
| Only basket/bookings | BookingAgent |
| Flights + hotels | FlightAgent + HotelAgent |
| Flights + restaurants | FlightAgent + YelpAgent |
| Hotels + restaurants | HotelAgent + YelpAgent |
| Flights + hotels + basket | FlightAgent + HotelAgent + BookingAgent |
| Book a restaurant | YelpAgent (search only) + inform user booking is unavailable |

---

The user's thread ID is provided in brackets at the start of their message, e.g. [thread_abc123].
""",
    tools=[
        flight_agent.as_tool("consult_flight_agent", "Delegate flight-related queries to the Flight Agent. Provide complete context including departure/arrival airports, dates and passengers."),
        hotel_agent.as_tool("consult_hotel_agent", "Delegate hotel-related queries to the Hotel Agent. Provide complete context including location and check-in/out dates."),
        yelp_agent.as_tool("consult_yelp_agent", "Delegate restaurant/business queries to the Yelp Agent. Provide complete context including cuisine type and location."),
        booking_agent.as_tool("consult_booking_agent", "Delegate basket operations to the Booking Agent. Use for: adding a flight/hotel to the basket, removing an item, or viewing the basket."),
    ],
    model=SUPERVISOR_AGENT.model,
    
)

if __name__ == "__main__":
    import time

    user_input = "I'm planning a trip to ankara(ESB) from LA(LAX) from 2026-04-20 to 2026-04-25 for one person with no kids. I need a flight"

    print("Starting orchestrator with Agent-as-Tool pattern...")

    travel_ctx = TravelContext(user_id="test_user", thread_id="test_thread_123")
    print("0.flight_picts:", travel_ctx.flight_picts)
    res = Runner.run_sync(supervisor, input=user_input, context=travel_ctx)

    print("-------  OUTPUT --------")
    print(res.final_output)
    print("1.flight_picts:", travel_ctx.flight_picts)
    history_list = res.to_input_list()
    engineer = ContextEngineer(history_list)
    clean_history = (
        engineer
        .delete_failed_function_calls()
        .refresh_crucial_data()
        .get_history()
    )
    clean_history.append({
        "role": "user",
        "content": "check for the hotels."
    })

    res = Runner.run_sync(supervisor, input=clean_history, context=travel_ctx)
    print("-------  OUTPUT 2 --------")
    print(res.final_output)
    print("2.hotel_picts:", travel_ctx.hotel_picts)
    history_list = res.to_input_list()
    engineer = ContextEngineer(history_list)
    clean_history = (
        engineer
        .delete_failed_function_calls()
        .refresh_crucial_data()
        .get_history()
    )
    clean_history.append({
        "role": "user",
        "content": "recommend me a pizza place"
    })

    res = Runner.run_sync(supervisor, input=clean_history, context=travel_ctx)
    print("-------  OUTPUT 3 --------")
    print(res.final_output)
    print("3.yelp_picts:", travel_ctx.yelp_picts)

    history_list = res.to_input_list()
    engineer = ContextEngineer(history_list)
    clean_history = (
        engineer
        .delete_failed_function_calls()
        .refresh_crucial_data()
        .get_history()
    )
    clean_history.append({
        "role": "user",
        "content": "I have changed plans, I want to go from Berlin(BER) to Munich(MUC) from 2026-04-20 to 2026-04-25 for one person with no kids. look for the flights"
    })

    res = Runner.run_sync(supervisor, input=clean_history, context=travel_ctx)
    print("-------  OUTPUT 4 --------")

    print("4.flight_picts:", travel_ctx.flight_picts)
    print(res.final_output)
    # with open("flight_ctx.json", "w") as f:
    #     json.dump(res.to_input_list(), f)
