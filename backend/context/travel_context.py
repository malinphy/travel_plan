from dataclasses import dataclass, field
from typing import List, Dict, Optional
from agents import RunContextWrapper

@dataclass
class TravelContext:
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    flight_picts: Dict[str, List[Dict]] = field(default_factory=dict)
    hotel_picts: Dict[str, List[Dict]] = field(default_factory=dict)
    yelp_picts: Dict[str, List[Dict]] = field(default_factory=dict)
    basket_picts: List[Dict] = field(default_factory=list)

# Aliases for backward compatibility in specialized scripts
FlightContext = TravelContext
HotelContext = TravelContext
YelpContext = TravelContext
