import os
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import Field
from serpapi import GoogleSearch
from dotenv import load_dotenv
from agents import function_tool, RunContextWrapper
from sqlalchemy.orm import Session

from backend.models.flight import FlightSearchResults
from database.schema import engine, FlightSearch, FlightOption
from backend.context.travel_context import FlightContext

load_dotenv(override=True)


def _parse_time(time_str: str) -> Optional[datetime]:
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


@function_tool
def search_flights(
    ctx: RunContextWrapper[FlightContext],
    departure_id: str = Field(
        description="Parameter defines the departure airport code or location kgmid. An airport code is an uppercase 3-letter code.",
        examples=["Ankara Esenboga airport is ESB"],
    ),
    arrival_id: str = Field(
        description="Parameter defines the arrival airport code or location kgmid. An airport code is an uppercase 3-letter code.",
        examples=["Istanbul Sabiha Gokcen airport is SAW"],
    ),
    outbound_date: Optional[str] = Field(default=None, description="Outbound date.", examples=["2026-04-20"]),
    return_date: Optional[str] = Field(default=None, description="Return date.", examples=["2026-04-25"]),
    flight_type: Optional[str] = Field(
        default="1",
        description="Type of flight.",
        examples=["1 : Round trip (default), 2 : One way, 3 : Multi-city"],
    ),
    adults: Optional[str] = Field(default="1", description="Number of adults.", examples=["1"]),
    children: Optional[str] = Field(default="0", description="Number of children.", examples=["0"]),
    user_id: Optional[str] = Field(default=None, description="User id.", examples=["1"]),
    thread_id: Optional[str] = Field(default=None, description="Thread id.", examples=["1"]),
) -> str:
    """Run a simple flight search, store results in the database, and return the unique search_id."""
    if flight_type not in ["1", "2", "3"]:
        return "Invalid flight type. Please use 1 for round trip, 2 for one way, or 3 for multi-city."

    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "currency": "USD",
        "type": flight_type,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "adults": adults,
        "children": children,
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        flight_results = FlightSearchResults.model_validate(results)
    except Exception as e:
        return f"Error running search or parsing results: {e}"

    import uuid
    search_id = str(uuid.uuid4())

    resolved_user_id = user_id or ctx.context.user_id
    resolved_thread_id = thread_id or ctx.context.thread_id

    with Session(engine) as session:
        search_record = FlightSearch(
            id=search_id,
            user_id=resolved_user_id,
            thread_id=resolved_thread_id,
            departure_id=departure_id,
            arrival_id=arrival_id,
            outbound_date=outbound_date or "",
            return_date=return_date,
            raw_parameters=flight_results.search_parameters.model_dump(),
        )
        session.add(search_record)

        for option in (flight_results.best_flights or []):
            first_flight = option.flights[0] if option.flights else None
            dep_time = _parse_time(first_flight.departure_airport.time) if first_flight else None
            arr_time = _parse_time(option.flights[-1].arrival_airport.time) if option.flights else None
            session.add(FlightOption(
                flight_search_id=search_record.id,
                price=option.price,
                total_duration=option.total_duration,
                departure_time=dep_time,
                arrival_time=arr_time,
                num_stops=len(option.layovers) if option.layovers else 0,
                primary_airline=first_flight.airline if first_flight else None,
                is_best_flight=True,
                trip_type=option.type,
                travel_class=first_flight.travel_class if first_flight else None,
                airline_logo=option.airline_logo,
                legroom=first_flight.legroom if first_flight else None,
                extensions=first_flight.extensions if first_flight else None,
                flight_number=first_flight.flight_number if first_flight else None,
                flight_data=option.model_dump(mode="json"),
            ))

        for option in (flight_results.other_flights or []):
            first_flight = option.flights[0] if option.flights else None
            dep_time = _parse_time(first_flight.departure_airport.time) if first_flight else None
            arr_time = _parse_time(option.flights[-1].arrival_airport.time) if option.flights else None
            session.add(FlightOption(
                # flight_search_id=search_record.id,
                flight_search_id=search_id,
                price=option.price,
                total_duration=option.total_duration,
                departure_time=dep_time,
                arrival_time=arr_time,
                num_stops=len(option.layovers) if option.layovers else 0,
                primary_airline=first_flight.airline if first_flight else None,
                is_best_flight=False,
                trip_type=option.type,
                travel_class=first_flight.travel_class if first_flight else None,
                airline_logo=option.airline_logo,
                legroom=first_flight.legroom if first_flight else None,
                extensions=first_flight.extensions if first_flight else None,
                flight_number=first_flight.flight_number if first_flight else None,
                flight_data=option.model_dump(mode="json"),
            ))

        session.commit()
    return{
        "message": f"Search successful! Results saved to the database. The 'flight_search_id' to query for this data is: {search_id}",
        "flight_search_id": search_id,
    }


@function_tool
def query_flight_options(
    ctx: RunContextWrapper[FlightContext],
    flight_search_id: str = Field(description="The flight search id.", examples=["69bd9e69a7d7840980622b74"]),
    max_price: Optional[int] = Field(default=None, description="Maximum price.", examples=[500]),
    max_stops: Optional[int] = Field(default=None, description="Maximum stops.", examples=[1]),
    max_duration: Optional[int] = Field(default=None, description="Maximum duration (minutes).", examples=[300]),
    order_by: str = Field(default="price_asc", description="Sort order: price_asc, duration_asc, departure_asc."),
    limit: int = 5,
) -> List[Dict]:
    """Query the database for flight options for a specific flight search ID."""

    with Session(engine) as session:
        query = session.query(FlightOption).filter(FlightOption.flight_search_id == flight_search_id)

        if max_price is not None:
            query = query.filter(FlightOption.price <= max_price)
        if max_stops is not None:
            query = query.filter(FlightOption.num_stops <= max_stops)
        if max_duration is not None:
            query = query.filter(FlightOption.total_duration <= max_duration)

        if order_by == "price_asc":
            query = query.order_by(FlightOption.price.asc())
        elif order_by == "duration_asc":
            query = query.order_by(FlightOption.total_duration.asc())
        elif order_by == "departure_asc":
            query = query.order_by(FlightOption.departure_time.asc())

        query = query.limit(limit)

        results = []
        pict_entries = []
        for flight in query.all():
            results.append({
                "price": flight.price,
                "num_stops": flight.num_stops,
                "total_duration": flight.total_duration,
                "primary_airline": flight.primary_airline,
                "is_best_flight": flight.is_best_flight,
                "travel_class": flight.travel_class,
                "legroom": flight.legroom,
                "extensions": flight.extensions,
                "flight_number": flight.flight_number,
            })
            pict_entries.append({
                "price": flight.price,
                "airline_logo": flight.airline_logo,
                "primary_airline": flight.primary_airline,
                "is_best_flight": flight.is_best_flight,
                "flight_number": flight.flight_number,
            })

        ctx.context.flight_picts[flight_search_id] = pict_entries
        return results
