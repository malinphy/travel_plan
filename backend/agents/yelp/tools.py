import os
import uuid
from typing import Optional, List, Dict
from pydantic import Field
from serpapi import GoogleSearch
from dotenv import load_dotenv
from agents import function_tool, RunContextWrapper
from sqlalchemy.orm import Session

from backend.models.yelp import YelpSearchResults
from database.schema import engine, YelpSearch, YelpOption
from backend.context.travel_context import YelpContext

load_dotenv(override=True)


@function_tool
def search_yelp(
    ctx: RunContextWrapper[YelpContext],
    query: str = Field(
        description="Search query. Strictly related to restaurants, cafes, bars, etc. Do not include hotel or flight info.",
        examples=["new york restaurants", "amsterdam cafes", "pizza", "burgers"],
    ),
    find_loc: str = Field(
        description="Location.",
        examples=["706 Mission St, San Francisco, CA", "San Francisco, CA", "94103"],
    ),
    user_id: Optional[str] = Field(default=None, description="User id.", examples=["1"]),
    thread_id: Optional[str] = Field(default=None, description="Thread id.", examples=["1"]),
):
    """Run a Yelp search and store the results in the database, returning the specific search_id."""
    params = {
        "engine": "yelp",
        "find_desc": query,
        "find_loc": find_loc,
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    if "error" in results:
        return f"API Error: {results['error']}"

    try:
        yelp_results = YelpSearchResults.model_validate({"businesses": organic_results})
    except Exception as e:
        return f"Error parsing results: {e}"

    search_id = str(uuid.uuid4())

    resolved_user_id = user_id or ctx.context.user_id
    resolved_thread_id = thread_id or ctx.context.thread_id

    with Session(engine) as session:
        search_record = YelpSearch(
            id=search_id,
            user_id=resolved_user_id,
            thread_id=resolved_thread_id,
            query=query,
            location=find_loc,
        )
        session.merge(search_record)

        for business in yelp_results.businesses:
            session.add(YelpOption(
                yelp_search_id=search_id,
                title=business.title,
                rating=business.rating,
                reviews=business.reviews,
                price=business.price,
                phone=business.phone,
                thumbnail=str(business.thumbnail) if business.thumbnail else None,
                neighborhoods=business.neighborhoods,
                yelp_data=business.model_dump(mode="json"),
            ))
        session.commit()

    return {
        "message": f"Search successful! Results saved to the database. The 'yelp_search_id' to query for this data is: {search_id}",
        "yelp_search_id": search_id,
    }


@function_tool
def query_yelp_options(
    ctx: RunContextWrapper[YelpContext],
    yelp_search_id: str = Field(description="The yelp search id.", examples=["uuid-string"]),
    min_rating: Optional[float] = None,
    max_price: Optional[str] = None,
    order_by: str = "rating_desc",
    limit: int = 5,
) -> List[Dict]:
    """Query the database for yelp options for a specific yelp search ID."""
    with Session(engine) as session:
        query = session.query(YelpOption).filter(YelpOption.yelp_search_id == yelp_search_id)

        if min_rating is not None:
            query = query.filter(YelpOption.rating >= min_rating)

        if order_by == "rating_desc":
            query = query.order_by(YelpOption.rating.desc())
        elif order_by == "reviews_desc":
            query = query.order_by(YelpOption.reviews.desc())

        query = query.limit(limit)

        results = []
        pict_entries = []
        for yelp_biz in query.all():
            if max_price is not None and yelp_biz.price is not None:
                if len(yelp_biz.price) > len(max_price):
                    continue

            results.append({
                "title": yelp_biz.title,
                "rating": yelp_biz.rating,
                "reviews": yelp_biz.reviews,
                "price": yelp_biz.price,
                "phone": yelp_biz.phone,
                "neighborhoods": yelp_biz.neighborhoods,
            })
            pict_entries.append({
                "title": yelp_biz.title,
                "rating": yelp_biz.rating,
                "reviews": yelp_biz.reviews,
                "price": yelp_biz.price,
                "neighborhoods": yelp_biz.neighborhoods,
                "thumbnail": yelp_biz.thumbnail,
            })

        ctx.context.yelp_picts[yelp_search_id] = pict_entries
        return results
