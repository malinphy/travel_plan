from typing import List, Optional, Dict, Union
from pydantic import BaseModel, HttpUrl


class Transportation(BaseModel):
    type: str
    duration: str


class NearbyPlace(BaseModel):
    name: str
    transportations: List[Transportation]


class Rate(BaseModel):
    lowest: str
    extracted_lowest: int
    before_taxes_fees: Optional[str] = None
    extracted_before_taxes_fees: Optional[int] = None


class Price(BaseModel):
    source: str
    logo: HttpUrl
    num_guests: int
    rate_per_night: Rate
    free_cancellation: Optional[bool] = None  # Made optional
    free_cancellation_until_date: Optional[str] = None
    free_cancellation_until_time: Optional[str] = None


class Image(BaseModel):
    thumbnail: HttpUrl
    original_image: HttpUrl


class Rating(BaseModel):
    stars: int
    count: int


class ReviewsBreakdown(BaseModel):
    name: str
    description: str
    total_mentioned: int
    positive: int
    negative: int
    neutral: int


class GPSCoordinates(BaseModel):
    latitude: float
    longitude: float


class Property(BaseModel):
    type: str
    name: str
    description: Optional[str] = None
    link: Optional[HttpUrl] = None  # Made optional
    property_token: str
    serpapi_property_details_link: HttpUrl
    gps_coordinates: GPSCoordinates
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    rate_per_night: Rate
    total_rate: Rate
    deal: Optional[str] = None
    deal_description: Optional[str] = None
    nearby_places: List[NearbyPlace]
    hotel_class: Optional[str] = None
    extracted_hotel_class: Optional[int] = None
    images: List[Image]
    overall_rating: Optional[Union[float, int]] = None  # Made optional
    reviews: Optional[int] = None  # Made optional
    ratings: Optional[List[Rating]] = None  # Made optional
    location_rating: Union[float, int]
    reviews_breakdown: Optional[List[ReviewsBreakdown]] = None
    amenities: List[str]
    eco_certified: Optional[bool] = False
    excluded_amenities: Optional[List[str]] = None
    essential_info: Optional[List[str]] = None
    prices: Optional[List[Price]] = None


class BrandChild(BaseModel):
    id: int
    name: str


class Brand(BaseModel):
    id: int
    name: str
    children: List[BrandChild] = []


class SearchMetadata(BaseModel):
    id: str
    status: str
    json_endpoint: HttpUrl
    created_at: str
    processed_at: str
    google_hotels_url: HttpUrl
    raw_html_file: HttpUrl
    prettify_html_file: HttpUrl
    total_time_taken: float


class SearchParameters(BaseModel):
    engine: str
    q: str
    gl: str
    hl: str
    currency: str
    check_in_date: str
    check_out_date: str
    adults: int
    children: int


class SearchInformation(BaseModel):
    total_results: int


class SerpapiPagination(BaseModel):
    current_from: int
    current_to: int
    next_page_token: str
    next: HttpUrl


class HotelSearchResponse(BaseModel):
    search_metadata: SearchMetadata
    search_parameters: SearchParameters
    search_information: SearchInformation
    brands: List[Brand]
    properties: List[Property]
    serpapi_pagination: SerpapiPagination