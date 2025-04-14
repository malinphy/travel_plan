from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field

class Category(BaseModel):
    """Model for business categories"""
    title: str
    link: HttpUrl

class Business(BaseModel):
    """Main model for Yelp business listings with all optional fields accounted for"""
    position: int
    place_ids: List[str]
    title: str
    link: HttpUrl
    reviews_link: HttpUrl
    categories: List[Category]
    
    # Made optional based on error
    price: Optional[str] = Field(None, description="Price indicator like '££'")  
    rating: Optional[float] = None
    reviews: Optional[int] = None
    neighborhoods: Optional[str] = None
    phone: Optional[str] = None
    snippet: Optional[str] = None
    thumbnail: Optional[HttpUrl] = None
    
    # Already optional
    highlights: Optional[List[str]] = None

class YelpSearchResults(BaseModel):
    """Container for the top-level list"""
    businesses: List[Business]