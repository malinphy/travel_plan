
import os
import requests
from serpapi import GoogleSearch
from dotenv import load_dotenv
from abc import ABC, abstractmethod

load_dotenv()

class SearchProvider(ABC):
    """
    Abstract base class for a search provider.
    """
    @abstractmethod
    def search(self, **kwargs):
        """
        Performs a search with the given parameters.
        """
        pass

class FlightsProvider(SearchProvider):
    """
    Provider for searching flights using SerpAPI.
    """
    def search(self, **kwargs) -> dict:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            raise ValueError("SERPAPI_API_KEY environment variable not set.")

        params = {
            "engine": "google_flights",
            "api_key": api_key,
            "departure_id": kwargs.get("departure_id"),
            "arrival_id": kwargs.get("arrival_id"),
            "outbound_date": kwargs.get("outbound_date"),
            "type": "2",
        }

        if "return_date" in kwargs:
            params["return_date"] = kwargs.get("return_date")

        search = GoogleSearch(params)
        return search.get_dict()

class HotelsProvider(SearchProvider):
    """
    Provider for searching hotels using SerpAPI.
    """
    def search(self, **kwargs) -> dict:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            raise ValueError("SERPAPI_API_KEY environment variable not set.")

        params = {
            "engine": "google_hotels",
            "api_key": api_key,
            "q": kwargs.get("query"),
            "check_in_date": kwargs.get("check_in_date"),
            "check_out_date": kwargs.get("check_out_date"),
            "currency": "USD",
            "hl": "en"
        }

        search = GoogleSearch(params)
        return search.get_dict()

class YelpProvider(SearchProvider):
    """
    Provider for searching businesses using Yelp Fusion API.
    """
    YELP_API_BASE_URL = "https://api.yelp.com/v3/businesses/search"

    def search(self, **kwargs) -> dict:
        api_key = os.getenv("YELP_API_KEY")
        if not api_key:
            raise ValueError("YELP_API_KEY environment variable not set.")

        headers = {"Authorization": f"Bearer {api_key}"}
        params = {
            "term": kwargs.get("term"),
            "location": kwargs.get("location"),
            "categories": kwargs.get("categories", "restaurants,bars"),
            "sort_by": "best_match",
            "limit": 10
        }

        response = requests.get(self.YELP_API_BASE_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

class SearchProviderFactory:
    """
    Factory for creating search providers.
    """
    _providers = {
        "flights": FlightsProvider,
        "hotels": HotelsProvider,
        "yelp": YelpProvider,
    }

    @staticmethod
    def get_provider(service_name: str) -> SearchProvider:
        provider = SearchProviderFactory._providers.get(service_name.lower())
        if not provider:
            raise ValueError(f"Invalid service name: {service_name}")
        return provider()

if __name__ == '__main__':
    # Example usage:
    try:
        # Flights
        flights_factory = SearchProviderFactory.get_provider("flights")
        flight_results = flights_factory.search(
            departure_id="JFK",
            arrival_id="SFO",
            outbound_date="2024-09-10",
            return_date="2024-09-24"
        )
        print("Flight Results:", flight_results.get('best_flights', [])[:1])

        # Hotels
        hotels_factory = SearchProviderFactory.get_provider("hotels")
        hotel_results = hotels_factory.search(
            query="Hotels in New York City",
            check_in_date="2024-09-10",
            check_out_date="2024-09-17"
        )
        print("Hotel Results:", hotel_results.get('properties', [])[:1])

        # Yelp
        yelp_factory = SearchProviderFactory.get_provider("yelp")
        yelp_results = yelp_factory.search(
            term="Italian",
            location="San Francisco, CA",
            categories="restaurants"
        )
        print("Yelp Results:", yelp_results.get('businesses', [])[:1])

    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"An error occurred: {e}")
