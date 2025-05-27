from pydantic import BaseModel, Field
from typing import List,Optional


class Flight(BaseModel):
    departure_id: Optional[List[str]] = Field(
        None, description="List of departure airport or city, IDs."
    )
    arrival_id: Optional[List[str]] = Field(
        None, description="List of arrival airport or city, IDs."
    )
    outbound_date: Optional[List[str]] = Field(
        None, description="List of outbound (departure) dates in YYYY-MM-DD format."
    )
    return_date: Optional[List[str]] = Field(
        None, description="List of return dates in YYYY-MM-DD format."
    )


class Hotel(BaseModel):
    q: Optional[List[str]] = Field(
        None, description="List of hotel search queries or names."
    )
    check_in_date: Optional[List[str]] = Field(
        None, description="List of check-in dates in YYYY-MM-DD format."
    )
    check_out_date: Optional[List[str]] = Field(
        None, description="List of check-out dates in YYYY-MM-DD format."
    )
    gl: Optional[List[str]] = Field(
        None, description="List of country codes.  It's a two-letter country code. (e.g., us for the United States, uk for United Kingdom, or fr for France."
    )    


class Yelp(BaseModel):
    search_term: Optional[List[str]] = Field(
        None, description="List of search terms for restaurants or businesses."
    )
    location: Optional[List[str]] = Field(
        None, description="List of locations for the Yelp search."
    )

class TotalModel(BaseModel):
    hotel: Optional[Hotel] = None
    flight: Optional[Flight] = None
    restaurant : Optional[Yelp] = None        