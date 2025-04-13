from datetime import datetime
from typing import List, Optional, Dict, Union
from pydantic import BaseModel
from pydantic import parse_obj_as
from typing import List, Optional, Dict, Union
from pydantic import BaseModel

class AirportInfo(BaseModel):
    name: str
    id: str
    time: Optional[str] = None

class Flight(BaseModel):
    departure_airport: AirportInfo
    arrival_airport: AirportInfo
    duration: int
    airplane: Optional[str] = None
    airline: Optional[str] = None
    airline_logo: Optional[str] = None
    travel_class: Optional[str] = None
    flight_number: Optional[str] = None
    legroom: Optional[str] = None
    extensions: Optional[List[str]] = None
    overnight: Optional[bool] = None
    ticket_also_sold_by: Optional[List[str]] = None
    plane_and_crew_by: Optional[str] = None

class Layover(BaseModel):
    duration: int
    name: str
    id: str
    overnight: Optional[bool] = None

class CarbonEmissions(BaseModel):
    this_flight: int
    typical_for_this_route: int
    difference_percent: int

class BestFlight(BaseModel):
    flights: List[Flight]
    layovers: List[Layover]
    total_duration: int
    carbon_emissions: CarbonEmissions
    price: int  # Required for best flights
    type: str
    airline_logo: Optional[str] = None
    departure_token: str

class OtherFlight(BaseModel):
    flights: List[Flight]
    layovers: List[Layover]
    total_duration: int
    carbon_emissions: CarbonEmissions
    price: Optional[int] = None  # Made optional for other flights
    type: str
    airline_logo: Optional[str] = None
    departure_token: str

class PriceInsights(BaseModel):
    lowest_price: int
    price_level: str
    typical_price_range: List[int]
    price_history: List[List[Union[int, float]]]

class AirportLocation(BaseModel):
    airport: AirportInfo
    city: str
    country: str
    country_code: str
    image: Optional[str] = None
    thumbnail: Optional[str] = None

class Airports(BaseModel):
    departure: List[AirportLocation]
    arrival: List[AirportLocation]

class SearchMetadata(BaseModel):
    id: str
    status: str
    json_endpoint: str
    created_at: str
    processed_at: str
    google_flights_url: str
    raw_html_file: str
    prettify_html_file: str
    total_time_taken: float

class SearchParameters(BaseModel):
    engine: str
    hl: str
    gl: str
    departure_id: str
    arrival_id: str
    outbound_date: str
    return_date: str
    currency: str
    deep_search: bool

class FlightSearchResults(BaseModel):
    search_metadata: SearchMetadata
    search_parameters: SearchParameters
    best_flights: List[BestFlight]
    other_flights: List[OtherFlight]
    price_insights: PriceInsights
    airports: List[Airports]