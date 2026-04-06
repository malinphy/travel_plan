import os
from typing import Optional, List, Dict
from pydantic import Field
from serpapi import GoogleSearch
from dotenv import load_dotenv
from agents import function_tool, RunContextWrapper
from sqlalchemy.orm import Session

from backend.models.hotel import HotelSearchResponse
from database.schema import engine, HotelSearch, HotelOption
from backend.context.travel_context import HotelContext

load_dotenv(override=True)


@function_tool
def search_hotels(
    ctx: RunContextWrapper[HotelContext],
    check_in_date: str = Field(description="Check-in date.", examples=["2026-04-20"]),
    check_out_date: str = Field(description="Check-out date.", examples=["2026-04-25"]),
    query: str = Field(
        description="Search query.",
        examples=["Miami hotel", "amsterdam accommodation", "paris bnb"],
    ),
    adults: Optional[str] = Field(default=None, description="Number of adults.", examples=["1"]),
    children: Optional[str] = Field(default=None, description="Number of children.", examples=["0"]),
    destination_country: Optional[str] = Field(
        default="us",
        description="Two-letter country code for the Google Hotels search.",
        examples=["us"],
    ),
    user_id: Optional[str] = Field(default=None, description="User id.", examples=["1"]),
    thread_id: Optional[str] = Field(default=None, description="Thread id.", examples=["1"]),
):
    """Run a simple hotel search according to the given parameters.
    `destination_country` MUST be a 2-letter country code (e.g., 'us', 'uk', 'tr')."""
    params = {
        "engine": "google_hotels",
        "q": query,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": adults,
        "children": children,
        "gl": destination_country,
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        return f"API Error: {results['error']}"

    try:
        hotel_results = HotelSearchResponse.model_validate(results)
    except Exception as e:
        return f"Error parsing results: {e}"

    search_params = hotel_results.search_parameters
    
    import uuid
    search_id = str(uuid.uuid4())

    resolved_user_id = user_id or ctx.context.user_id
    resolved_thread_id = thread_id or ctx.context.thread_id

    with Session(engine) as session:
        search_record = HotelSearch(
            id=search_id,
            user_id=resolved_user_id,
            thread_id=resolved_thread_id,
            q=query,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=int(adults) if adults else None,
            raw_parameters=search_params.model_dump(),
        )
        session.add(search_record)

        for prop in hotel_results.properties:
            rate_per_night = prop.rate_per_night.extracted_lowest if prop.rate_per_night else None
            total_rate = prop.total_rate.extracted_lowest if prop.total_rate else None
            overall_rating = int(prop.overall_rating) if prop.overall_rating is not None else None
            images_list = [str(img.original_image) for img in (prop.images or [])] if prop.images else None

            free_cancellation = False
            if prop.prices:
                for price_option in prop.prices:
                    if price_option.free_cancellation:
                        free_cancellation = True
                        break

            session.add(HotelOption(
                hotel_search_id=search_id,
                name=prop.name,
                rate_per_night=rate_per_night,
                total_rate=total_rate,
                overall_rating=overall_rating,
                reviews=prop.reviews,
                hotel_class=prop.extracted_hotel_class,
                images=images_list,
                free_cancellation=free_cancellation,
                amenities=prop.amenities,
                hotel_data=prop.model_dump(mode="json"),
            ))

        session.commit()

    return {
        "message": f"Search successful! Results saved to the database. The 'hotel_search_id' to query for this data is: {search_id}",
        "hotel_search_id": search_id,
    }


@function_tool
def query_hotel_options(
    ctx: RunContextWrapper[HotelContext],
    hotel_search_id: str = Field(description="The hotel search id.", examples=["abc123"]),
    max_rate_per_night: Optional[int] = Field(default=None, description="Max rate per night.", examples=[114]),
    min_overall_rating: Optional[float] = Field(default=None, description="Min overall rating.", examples=[4.5]),
    min_hotel_class: Optional[int] = Field(default=None, description="Min hotel class.", examples=[4]),
    order_by: str = Field(default="rate_asc", description="Sort order: rate_asc, rating_desc, reviews_desc."),
    limit: int = Field(default=5, description="Number of results to return."),
) -> List[Dict]:
    """Query the database for hotel options for a specific hotel search ID."""
    with Session(engine) as session:
        query = session.query(HotelOption).filter(HotelOption.hotel_search_id == hotel_search_id)

        if max_rate_per_night is not None:
            query = query.filter(HotelOption.rate_per_night <= max_rate_per_night)
        if min_overall_rating is not None:
            query = query.filter(HotelOption.overall_rating >= min_overall_rating)
        if min_hotel_class is not None:
            query = query.filter(HotelOption.hotel_class >= min_hotel_class)

        if order_by == "rate_asc":
            query = query.order_by(HotelOption.rate_per_night.asc())
        elif order_by == "rating_desc":
            query = query.order_by(HotelOption.overall_rating.desc())
        elif order_by == "reviews_desc":
            query = query.order_by(HotelOption.reviews.desc())

        query = query.limit(limit)

        results = []
        pict_entries = []
        for hotel in query.all():
            results.append({
                "name": hotel.name,
                "rate_per_night": hotel.rate_per_night,
                "total_rate": hotel.total_rate,
                "overall_rating": hotel.overall_rating,
                "reviews": hotel.reviews,
                "hotel_class": hotel.hotel_class,
                "free_cancellation": hotel.free_cancellation,
                "amenities": hotel.amenities,
            })
            pict_entries.append({
                "name": hotel.name,
                "rate_per_night": hotel.rate_per_night,
                "overall_rating": hotel.overall_rating,
                "hotel_class": hotel.hotel_class,
                "free_cancellation": hotel.free_cancellation,
            })

        ctx.context.hotel_picts[hotel_search_id] = pict_entries
        return results
