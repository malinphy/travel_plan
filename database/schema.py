import os
import uuid
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    searches = relationship("FlightSearch", back_populates="user")
    hotel_searches = relationship("HotelSearch", back_populates="user")
    yelp_searches = relationship("YelpSearch", back_populates="user")
    baskets = relationship("Basket", back_populates="user")
    conversation_states = relationship("ConversationState", back_populates="user")


class FlightSearch(Base):
    __tablename__ = 'flight_searches'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    thread_id = Column(String, index=True)
    departure_id = Column(String, nullable=False, index=True)
    arrival_id = Column(String, nullable=False, index=True)
    outbound_date = Column(String, nullable=False)
    return_date = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_parameters = Column(JSON)
    user = relationship("User", back_populates="searches")
    options = relationship("FlightOption", back_populates="search")


class FlightOption(Base):
    __tablename__ = 'flight_options'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_search_id = Column(String, ForeignKey('flight_searches.id'), nullable=False)
    price = Column(Integer, index=True)
    total_duration = Column(Integer, index=True)
    departure_time = Column(DateTime, index=True)
    arrival_time = Column(DateTime, index=True)
    num_stops = Column(Integer, index=True)
    primary_airline = Column(String, index=True)
    is_best_flight = Column(Boolean, default=False, index=True)
    trip_type = Column(String)
    travel_class = Column(String)
    airline_logo = Column(String)
    legroom = Column(String)
    extensions = Column(JSON)
    flight_number = Column(String)
    flight_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    search = relationship("FlightSearch", back_populates="options")


class ConversationState(Base):
    __tablename__ = 'conversation_state'
    thread_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    active_search_id = Column(String, ForeignKey('flight_searches.id'), nullable=True, index=True)
    last_params = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="conversation_states")
    active_search = relationship("FlightSearch")


class HotelSearch(Base):
    __tablename__ = 'hotel_searches'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    thread_id = Column(String, index=True)
    q = Column(String, nullable=False, index=True)
    check_in_date = Column(String, nullable=False, index=True)
    check_out_date = Column(String, nullable=False, index=True)
    adults = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_parameters = Column(JSON)
    user = relationship("User", back_populates="hotel_searches")
    options = relationship("HotelOption", back_populates="search")


class HotelOption(Base):
    __tablename__ = 'hotel_options'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_search_id = Column(String, ForeignKey('hotel_searches.id'), nullable=False)
    name = Column(String, index=True)
    rate_per_night = Column(Integer, index=True)
    total_rate = Column(Integer, index=True)
    overall_rating = Column(Integer, index=True)
    reviews = Column(Integer, index=True)
    hotel_class = Column(Integer, index=True)
    images = Column(JSON)
    free_cancellation = Column(Boolean)
    amenities = Column(JSON)
    hotel_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    search = relationship("HotelSearch", back_populates="options")


class YelpSearch(Base):
    __tablename__ = 'yelp_searches'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), index=True)
    thread_id = Column(String, index=True)
    query = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="yelp_searches")
    options = relationship("YelpOption", back_populates="search")


class YelpOption(Base):
    __tablename__ = 'yelp_options'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    yelp_search_id = Column(String, ForeignKey('yelp_searches.id'), nullable=False)
    title = Column(String, index=True)
    rating = Column(Integer, index=True)
    reviews = Column(Integer, index=True)
    price = Column(String, index=True)
    phone = Column(String)
    thumbnail = Column(String)
    neighborhoods = Column(String)
    yelp_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    search = relationship("YelpSearch", back_populates="options")


class Basket(Base):
    __tablename__ = 'baskets'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), index=True)
    thread_id = Column(String, nullable=False, index=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="baskets")
    items = relationship("BasketItem", back_populates="basket")


class BasketItem(Base):
    __tablename__ = 'basket_items'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    basket_id = Column(String, ForeignKey('baskets.id'), nullable=False)
    item_type = Column(String, nullable=False)
    item_id = Column(String, nullable=False)
    status = Column(String, default="added")
    snapshot_data = Column(JSON, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    basket = relationship("Basket", back_populates="items")


# Database path — stored in database/data/
_db_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(_db_dir, exist_ok=True)
db_path = os.path.join(_db_dir, 'flights_agent.db')
engine = create_engine(f"sqlite:///{db_path}", echo=False)

# Always ensure tables exist when this module is imported
Base.metadata.create_all(engine)

if __name__ == "__main__":
    print(f"Database tables ensured successfully in {db_path}!")
