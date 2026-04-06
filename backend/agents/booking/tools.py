from typing import Dict, List, Optional
from agents import function_tool, RunContextWrapper
from backend.context.travel_context import TravelContext
from sqlalchemy.orm import Session
from database.schema import (
    engine,
    Basket, BasketItem,
    FlightOption, FlightSearch,
    HotelOption, HotelSearch,
    YelpOption,
)


def _latest_search_with_fallback(session: Session, model, user_id: Optional[str], thread_id: Optional[str]):
    """Get latest search for this user/thread; fallback to legacy rows with null IDs."""
    latest = (
        session.query(model)
        .filter(model.user_id == user_id, model.thread_id == thread_id)
        .order_by(model.created_at.desc())
        .first()
    )
    if latest:
        return latest

    # Backward compatibility for rows created before ctx IDs were persisted.
    return (
        session.query(model)
        .filter(model.user_id.is_(None), model.thread_id.is_(None))
        .order_by(model.created_at.desc())
        .first()
    )


def _update_basket_ctx(ctx: RunContextWrapper[TravelContext], basket_id: str, session: Session):
    """Helper to sync the database basket state with the TravelContext."""
    items = (
        session.query(BasketItem)
        .filter(BasketItem.basket_id == basket_id, BasketItem.status == "added")
        .all()
    )
    result = []
    for item in items:
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
        result.append(entry)
    ctx.context.basket_picts = result


@function_tool
def get_or_create_basket(ctx: RunContextWrapper[TravelContext]) -> Dict:
    """Get the active basket for this user session, or create one if none exists. Always call this first."""
    
    # Enforce IDs from context
    user_id = ctx.context.user_id
    thread_id = ctx.context.thread_id

    with Session(engine) as session:
        # Filter by user_id and thread_id for isolation
        basket = (
            session.query(Basket)
            .filter(
                Basket.user_id == user_id,
                Basket.thread_id == thread_id, 
                Basket.status == "active"
            )
            .first()
        )
        if basket is None:
            basket = Basket(user_id=user_id, thread_id=thread_id)
            session.add(basket)
            session.commit()
            session.refresh(basket)
            return {"basket_id": basket.id, "created": True, "message": f"New basket created (ID: {basket.id})"}
        return {"basket_id": basket.id, "created": False, "message": f"Active basket found (ID: {basket.id})"}


@function_tool
def view_basket(ctx: RunContextWrapper[TravelContext], basket_id: str) -> List[Dict]:
    """Return all active items in the basket with their basket_item_ids and a readable summary."""
    with Session(engine) as session:
        _update_basket_ctx(ctx, basket_id, session)
        if not ctx.context.basket_picts:
            return [{"message": "Basket is empty."}]
        return ctx.context.basket_picts


@function_tool
def get_latest_results(ctx: RunContextWrapper[TravelContext], item_type: str, limit: int = 10) -> List[Dict]:
    """
    Fetch the most recently searched options for the current user with their database IDs.
    Use this to resolve the user's choice (e.g. 'cheapest flight', 'that Marriott') to a concrete item_id.
    item_type must be one of: 'flight', 'hotel'.
    """
    
    # Enforce IDs from context
    user_id = ctx.context.user_id
    thread_id = ctx.context.thread_id

    with Session(engine) as session:
        if item_type == "flight":
            latest = _latest_search_with_fallback(session, FlightSearch, user_id, thread_id)
            if not latest:
                return [{"error": "No flight searches found. Ask the user to search for flights first."}]
            options = (
                session.query(FlightOption)
                .filter(FlightOption.flight_search_id == latest.id)
                .order_by(FlightOption.price.asc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": o.id,
                    "price": o.price,
                    "airline": o.primary_airline,
                    "stops": o.num_stops,
                    "duration_minutes": o.total_duration,
                    "is_best": o.is_best_flight,
                    "departure": o.departure_time.isoformat() if o.departure_time else None,
                }
                for o in options
            ]

        elif item_type == "hotel":
            latest = _latest_search_with_fallback(session, HotelSearch, user_id, thread_id)
            if not latest:
                return [{"error": "No hotel searches found. Ask the user to search for hotels first."}]
            options = (
                session.query(HotelOption)
                .filter(HotelOption.hotel_search_id == latest.id)
                .order_by(HotelOption.rate_per_night.asc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": o.id,
                    "name": o.name,
                    "rate_per_night": o.rate_per_night,
                    "total_rate": o.total_rate,
                    "rating": o.overall_rating,
                    "hotel_class": o.hotel_class,
                }
                for o in options
            ]

        else:
            return [{"error": f"Unknown item_type '{item_type}'. Must be 'flight' or 'hotel'."}]


@function_tool
def add_to_basket(ctx: RunContextWrapper[TravelContext], basket_id: str, item_type: str, item_id: str) -> Dict:
    """
    Add a flight or hotel to the basket.
    item_type: 'flight' | 'hotel'
    item_id: the database ID returned by get_latest_results.
    """
    with Session(engine) as session:
        basket = (
            session.query(Basket)
            .filter(
                Basket.id == basket_id,
                Basket.user_id == ctx.context.user_id,
                Basket.thread_id == ctx.context.thread_id,
            )
            .first()
        )
        if not basket:
            return {"error": f"Basket {basket_id} not found for this user/thread."}

        snapshot = None
        display_name = None

        if item_type == "flight":
            item = session.query(FlightOption).filter(FlightOption.id == item_id).first()
            if not item:
                return {"error": f"Flight option {item_id} not found."}
            snapshot = item.flight_data
            display_name = f"{item.primary_airline or 'Unknown airline'} flight (${item.price})"

        elif item_type == "hotel":
            item = session.query(HotelOption).filter(HotelOption.id == item_id).first()
            if not item:
                return {"error": f"Hotel option {item_id} not found."}
            snapshot = item.hotel_data
            display_name = f"{item.name} (${item.rate_per_night}/night)"

        else:
            return {"error": f"Unknown item_type '{item_type}'. Use 'flight' or 'hotel'."}

        basket_item = BasketItem(
            basket_id=basket_id,
            item_type=item_type,
            item_id=item_id,
            status="added",
            snapshot_data=snapshot,
        )
        session.add(basket_item)
        session.commit()
        session.refresh(basket_item)
        _update_basket_ctx(ctx, basket_id, session)

        return {"message": f"Added {display_name} to basket.", "basket_item_id": basket_item.id}


@function_tool
def remove_from_basket(ctx: RunContextWrapper[TravelContext], basket_id: str, basket_item_id: str) -> Dict:
    """Remove an item from the basket. The item is soft-deleted (status set to 'cancelled')."""
    with Session(engine) as session:
        item = (
            session.query(BasketItem)
            .filter(BasketItem.id == basket_item_id, BasketItem.basket_id == basket_id)
            .first()
        )
        if not item:
            return {"error": f"Basket item {basket_item_id} not found in basket {basket_id}."}
        if item.status == "cancelled":
            return {"message": "Item is already removed."}

        item.status = "cancelled"
        session.commit()
        _update_basket_ctx(ctx, basket_id, session)

        return {"message": f"Removed {item.item_type} item from basket.", "basket_item_id": basket_item_id}


@function_tool
def modify_basket_item(
    ctx: RunContextWrapper[TravelContext],
    basket_id: str,
    basket_item_id: str,
    new_item_id: str,
) -> Dict:
    """
    Swap a basket item for a different option of the same type.
    Marks the old item as 'modified' and adds the new one.
    new_item_id is the database ID from get_latest_results.
    """
    with Session(engine) as session:
        old_item = (
            session.query(BasketItem)
            .filter(BasketItem.id == basket_item_id, BasketItem.basket_id == basket_id)
            .first()
        )
        if not old_item:
            return {"error": f"Basket item {basket_item_id} not found in basket {basket_id}."}

        item_type = old_item.item_type
        old_item.status = "modified"

        snapshot = None
        display_name = None

        if item_type == "flight":
            new_item = session.query(FlightOption).filter(FlightOption.id == new_item_id).first()
            if not new_item:
                old_item.status = "added"
                return {"error": f"New flight option {new_item_id} not found."}
            snapshot = new_item.flight_data
            display_name = f"{new_item.primary_airline or 'Unknown airline'} flight (${new_item.price})"

        elif item_type == "hotel":
            new_item = session.query(HotelOption).filter(HotelOption.id == new_item_id).first()
            if not new_item:
                old_item.status = "added"
                return {"error": f"New hotel option {new_item_id} not found."}
            snapshot = new_item.hotel_data
            display_name = f"{new_item.name} (${new_item.rate_per_night}/night)"

        elif item_type == "restaurant":
            new_item = session.query(YelpOption).filter(YelpOption.id == new_item_id).first()
            if not new_item:
                old_item.status = "added"
                return {"error": f"New restaurant option {new_item_id} not found."}
            snapshot = new_item.yelp_data
            display_name = f"{new_item.title}"

        else:
            return {"error": f"Unknown item_type '{item_type}'."}

        new_basket_item = BasketItem(
            basket_id=basket_id,
            item_type=item_type,
            item_id=new_item_id,
            status="added",
            snapshot_data=snapshot,
        )
        session.add(new_basket_item)
        session.commit()
        session.refresh(new_basket_item)
        _update_basket_ctx(ctx, basket_id, session)

        return {
            "message": f"Changed to {display_name}.",
            "old_basket_item_id": basket_item_id,
            "new_basket_item_id": new_basket_item.id,
        }
