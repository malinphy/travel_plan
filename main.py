from collections import OrderedDict
from typing import Any, Dict, List, Optional

from agents import Runner
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uvicorn

from backend.context.travel_context import TravelContext
from database.history import ContextMessage, add_to_history
from database.schema import (
    engine,
    Basket,
    BasketItem,
    ConversationState,
    FlightOption,
    FlightSearch,
    HotelOption,
    HotelSearch,
    User,
    YelpOption,
    YelpSearch,
)
from orchestrator import supervisor

app = FastAPI(title="Multi-User Travel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Short-lived in-memory cache keyed by user/thread. Persistence lives in SQLite.
user_sessions: Dict[str, Dict[str, Any]] = {}


class QueryRequest(BaseModel):
    query: str
    user_id: str
    thread_id: str


def _session_key(user_id: str, thread_id: str) -> str:
    return f"{user_id}:{thread_id}"


def _ensure_user(session: Session, user_id: str) -> None:
    if not user_id:
        return
    if session.query(User).filter(User.id == user_id).first() is None:
        session.add(User(id=user_id, name=user_id))
        session.commit()


def _load_persisted_history(user_id: str, thread_id: str) -> List[Dict[str, Any]]:
    with Session(engine) as db:
        _ensure_user(db, user_id)
        state = (
            db.query(ConversationState)
            .filter(
                ConversationState.user_id == user_id,
                ConversationState.thread_id == thread_id,
            )
            .first()
        )
        if state and isinstance(state.last_params, list):
            return state.last_params
    return []


def _persist_session_history(user_id: str, thread_id: str, history: List[Dict[str, Any]]) -> None:
    with Session(engine) as db:
        _ensure_user(db, user_id)
        state = (
            db.query(ConversationState)
            .filter(
                ConversationState.user_id == user_id,
                ConversationState.thread_id == thread_id,
            )
            .first()
        )
        if state is None:
            state = ConversationState(user_id=user_id, thread_id=thread_id, last_params=history)
            db.add(state)
        else:
            state.last_params = history
        db.commit()


def get_or_create_session(user_id: str, thread_id: str) -> Dict[str, Any]:
    session_key = _session_key(user_id, thread_id)
    if session_key not in user_sessions:
        user_sessions[session_key] = {
            "context": TravelContext(user_id=user_id, thread_id=thread_id),
            "history": _load_persisted_history(user_id, thread_id),
        }
    return user_sessions[session_key]


def _serialize_flight_option(option: FlightOption) -> Dict[str, Any]:
    return {
        "price": option.price,
        "total_duration": option.total_duration,
        "num_stops": option.num_stops,
        "primary_airline": option.primary_airline,
        "is_best_flight": option.is_best_flight,
        "travel_class": option.travel_class,
        "airline_logo": option.airline_logo,
        "legroom": option.legroom,
        "extensions": option.extensions,
        "flight_number": option.flight_number,
    }


def _serialize_hotel_option(option: HotelOption) -> Dict[str, Any]:
    return {
        "name": option.name,
        "rate_per_night": option.rate_per_night,
        "total_rate": option.total_rate,
        "overall_rating": option.overall_rating,
        "reviews": option.reviews,
        "hotel_class": option.hotel_class,
        "images": option.images,
        "free_cancellation": option.free_cancellation,
        "amenities": option.amenities,
    }


def _serialize_yelp_option(option: YelpOption) -> Dict[str, Any]:
    return {
        "title": option.title,
        "rating": option.rating,
        "reviews": option.reviews,
        "price": option.price,
        "phone": option.phone,
        "thumbnail": option.thumbnail,
        "neighborhoods": option.neighborhoods,
    }


def _basket_summary(item: BasketItem) -> Dict[str, Any]:
    snap = item.snapshot_data or {}
    entry = {
        "basket_item_id": item.id,
        "item_type": item.item_type,
        "item_id": item.item_id,
        "added_at": item.added_at.isoformat() if item.added_at else None,
    }
    if item.item_type == "flight":
        flights = snap.get("flights", [])
        entry["summary"] = {
            "airline": flights[0].get("airline") if flights else None,
            "price": snap.get("price"),
            "total_duration_min": snap.get("total_duration"),
            "trip_type": snap.get("type"),
        }
    elif item.item_type == "hotel":
        rate = snap.get("rate_per_night") or {}
        entry["summary"] = {
            "name": snap.get("name"),
            "rate_per_night": rate.get("extracted_lowest") if isinstance(rate, dict) else None,
            "rating": snap.get("overall_rating"),
            "hotel_class": snap.get("extracted_hotel_class"),
        }
    elif item.item_type == "restaurant":
        entry["summary"] = {
            "name": snap.get("title"),
            "rating": snap.get("rating"),
            "price": snap.get("price"),
        }
    return entry


def _get_thread_messages(user_id: str, thread_id: str) -> List[Dict[str, Any]]:
    with Session(engine) as db:
        rows = (
            db.query(ContextMessage)
            .filter(
                ContextMessage.user_id == user_id,
                ContextMessage.thread_id == thread_id,
            )
            .order_by(ContextMessage.created_at.asc())
            .all()
        )
        return [
            {
                "role": row.role,
                "content": row.content,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


def _get_thread_summaries(user_id: str) -> List[Dict[str, Any]]:
    with Session(engine) as db:
        rows = (
            db.query(ContextMessage)
            .filter(ContextMessage.user_id == user_id)
            .order_by(ContextMessage.created_at.desc())
            .all()
        )

    threads: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    for row in rows:
        if row.thread_id in threads:
            continue
        latest_user_text = next(
            (
                msg.content
                for msg in rows
                if msg.thread_id == row.thread_id and msg.role == "user"
            ),
            row.content,
        )
        threads[row.thread_id] = {
            "thread_id": row.thread_id,
            "title": latest_user_text[:80],
            "updated_at": row.created_at.isoformat(),
        }
    return list(threads.values())


def _load_flights_from_db(user_id: str, thread_id: str) -> List[Dict[str, Any]]:
    with Session(engine) as db:
        searches = (
            db.query(FlightSearch)
            .filter(FlightSearch.user_id == user_id, FlightSearch.thread_id == thread_id)
            .order_by(FlightSearch.created_at.desc())
            .all()
        )
        results: List[Dict[str, Any]] = []
        for search in searches:
            options = (
                db.query(FlightOption)
                .filter(FlightOption.flight_search_id == search.id)
                .order_by(FlightOption.is_best_flight.desc(), FlightOption.price.asc())
                .all()
            )
            results.extend(_serialize_flight_option(option) for option in options)
        return results


def _load_hotels_from_db(user_id: str, thread_id: str) -> List[Dict[str, Any]]:
    with Session(engine) as db:
        searches = (
            db.query(HotelSearch)
            .filter(HotelSearch.user_id == user_id, HotelSearch.thread_id == thread_id)
            .order_by(HotelSearch.created_at.desc())
            .all()
        )
        results: List[Dict[str, Any]] = []
        for search in searches:
            options = (
                db.query(HotelOption)
                .filter(HotelOption.hotel_search_id == search.id)
                .order_by(HotelOption.rate_per_night.asc())
                .all()
            )
            results.extend(_serialize_hotel_option(option) for option in options)
        return results


def _load_yelp_from_db(user_id: str, thread_id: str) -> List[Dict[str, Any]]:
    with Session(engine) as db:
        searches = (
            db.query(YelpSearch)
            .filter(YelpSearch.user_id == user_id, YelpSearch.thread_id == thread_id)
            .order_by(YelpSearch.created_at.desc())
            .all()
        )
        results: List[Dict[str, Any]] = []
        for search in searches:
            options = (
                db.query(YelpOption)
                .filter(YelpOption.yelp_search_id == search.id)
                .order_by(YelpOption.rating.desc(), YelpOption.reviews.desc())
                .all()
            )
            results.extend(_serialize_yelp_option(option) for option in options)
        return results


def _load_basket_from_db(user_id: str, thread_id: str) -> List[Dict[str, Any]]:
    with Session(engine) as db:
        basket = (
            db.query(Basket)
            .filter(
                Basket.user_id == user_id,
                Basket.thread_id == thread_id,
                Basket.status == "active",
            )
            .order_by(Basket.updated_at.desc())
            .first()
        )
        if basket is None:
            return []

        items = (
            db.query(BasketItem)
            .filter(BasketItem.basket_id == basket.id, BasketItem.status == "added")
            .order_by(BasketItem.added_at.asc())
            .all()
        )
        return [_basket_summary(item) for item in items]


@app.post("/query")
async def query_supervisor(request: QueryRequest):
    session = get_or_create_session(request.user_id, request.thread_id)
    history = list(session["history"])
    context = session["context"]

    user_message = {
        "role": "user",
        "content": f"[user_id: {request.user_id}] [thread_id: {request.thread_id}] {request.query}",
    }
    history.append(user_message)

    add_to_history(
        thread_id=request.thread_id,
        role="user",
        content=request.query,
        user_id=request.user_id,
    )

    res = await Runner.run(supervisor, input=history, context=context)

    updated_history = res.to_input_list()
    session["history"] = updated_history
    _persist_session_history(request.user_id, request.thread_id, updated_history)

    add_to_history(
        thread_id=request.thread_id,
        role="assistant",
        content=str(res.final_output),
        user_id=request.user_id,
    )

    return {"response": res.final_output}


@app.get("/threads")
async def list_threads(user_id: str):
    return {"threads": _get_thread_summaries(user_id)}


@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str, user_id: str):
    messages = _get_thread_messages(user_id, thread_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"thread_id": thread_id, "messages": messages}


@app.get("/flights")
async def get_flights(user_id: str, thread_id: str):
    session = get_or_create_session(user_id, thread_id)
    ctx = session["context"]

    all_flights = []
    for sid in reversed(list(ctx.flight_picts.keys())):
        all_flights.extend(ctx.flight_picts[sid])

    if not all_flights:
        all_flights = _load_flights_from_db(user_id, thread_id)

    return {"result": all_flights}


@app.get("/hotels")
async def get_hotels(user_id: str, thread_id: str):
    session = get_or_create_session(user_id, thread_id)
    ctx = session["context"]

    all_hotels = []
    for sid in reversed(list(ctx.hotel_picts.keys())):
        all_hotels.extend(ctx.hotel_picts[sid])

    if not all_hotels:
        all_hotels = _load_hotels_from_db(user_id, thread_id)

    return {"result": all_hotels}


@app.get("/yelp")
async def get_yelp(user_id: str, thread_id: str):
    session = get_or_create_session(user_id, thread_id)
    ctx = session["context"]

    all_yelp = []
    for sid in reversed(list(ctx.yelp_picts.keys())):
        all_yelp.extend(ctx.yelp_picts[sid])

    if not all_yelp:
        all_yelp = _load_yelp_from_db(user_id, thread_id)

    return {"result": all_yelp}


@app.get("/basket")
async def get_basket(user_id: str, thread_id: str):
    session = get_or_create_session(user_id, thread_id)
    ctx = session["context"]
    items = ctx.basket_picts or _load_basket_from_db(user_id, thread_id)
    return {"items": items}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
