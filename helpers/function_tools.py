from agents import function_tool
import wikipedia
import requests
import os 
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.environ['OPENAI_API_KEY_MALI']
from serpapi import GoogleSearch
api_key = os.getenv("SERPAPI_API_KEY")
import openmeteo_requests
from data_models.flight_data_models import FlightSearchResults, OtherFlight, BestFlight

import nest_asyncio
nest_asyncio.apply()

from agents.model_settings import ModelSettings
from agents import Agent, Runner,function_tool,trace, ItemHelpers, MessageOutputItem
from data_models.hotel_data_models import Property
from data_models.yelp_data_models import Category, Business
from helpers.helper_functions import assemble_conversation




def flight_to_string(response: dict, flight_key: str) -> str:
    """
    Converts flight information to a human-readable string.

    Args:
        response (dict): The response from the API.
        flight_key (str): Key to select 'best_flights' or 'other_flights'.

    Returns:
        str: A string summary of the flight data.
    """
    text_summary = ""

    for i, flight_data in enumerate(response.get(flight_key, [])):
        flight = OtherFlight(**flight_data)

        text_summary += f"\n***** Flight {i + 1} *****\n"
        text_summary += (
            f"Flight Summary:\n"
            f"Type: {flight.type}\n"
            f"Total Duration: {flight.total_duration} minutes\n"
            f"Price: ${flight.price}\n"
        )

        for j, segment in enumerate(flight.flights):
            text_summary += (
                f"--- Segment {j + 1} ---\n"
                f"Airline: {segment.airline or 'N/A'} ({segment.flight_number})\n"
                f"From: {segment.departure_airport.name} ({segment.departure_airport.id}) at {segment.departure_airport.time}\n"
                f"To: {segment.arrival_airport.name} ({segment.arrival_airport.id}) at {segment.arrival_airport.time}\n"
                f"Duration: {segment.duration} minutes\n"
                f"Class: {segment.travel_class}\n"
            )

            if flight.layovers and j < len(flight.layovers):
                layover = flight.layovers[j]
                text_summary += (
                    f"Layover at {layover.name} ({layover.id}) - {layover.duration} minutes\n"
                )

    return text_summary

@function_tool
def flight_search_2(departure_id: str, arrival_id: str, outbound_data: str, return_data: str) -> str:
    """
    Searches flights using SerpAPI's Google Flights engine.

    Args:
        departure_id (str): IATA code of departure airport.
        arrival_id (str): IATA code of arrival airport.
        outbound_data (str): Date of departure (YYYY-MM-DD).
        return_data (str): Date of return (YYYY-MM-DD).

    Returns:
        str: Formatted flight summary string.
    """
    params = {
        "api_key": api_key,
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_data,
        "return_date": return_data,
        "currency": "USD",
        "hl": "en",
        "deep_search": True,
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return f"API request failed: {e}"
    except ValueError:
        return "Failed to parse response as JSON."

    best_flights = flight_to_string(data, flight_key='best_flights')
    other_flights = flight_to_string(data, flight_key='other_flights')

    return (
        f"<BEST FLIGHTS>\n{best_flights}\n</BEST FLIGHTS>\n"
        f"<OTHER FLIGHTS>\n{other_flights}\n</OTHER FLIGHTS>\n"
    )

@function_tool
def hotels_search2(q:str, check_in_date:str, check_out_date:str, gl:str):
    """
    Google hotels information from SERPAPI. Returns json structure
    q : Location
    gl : Country
    """
    params = {
            "engine": "google_hotels",
            "q": q,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "adults": "2",
            "currency": "USD",
            "gl": gl,
            "hl": "en",
            "api_key": api_key
            }

    search = GoogleSearch(params)
    results = search.get_dict()

    hotels_info = ""
    for i in range(len(results['properties'])):
        test_output = Property(**results['properties'][i])
        t_data = f"""

    {i+1}
    Name : {test_output.name}
    check-in : {test_output.check_in_time}
    check-out : {test_output.check_out_time}
    lowest price per night : {test_output.rate_per_night.lowest}
    overall_rating : {test_output.overall_rating}
    amenities : {test_output.amenities}"""
        hotels_info += t_data

    return hotels_info

@function_tool
def yelp_search2(search_term: str, location: str) -> list:
    """
    Performs a Yelp search using the SerpAPI to find businesses based on a search term and location.

    Args:
        search_term: The term to search for on Yelp (e.g., "restaurants", "coffee shops").
        location: The location to search within (e.g., "New York, NY", "London").

    Returns:
        A list of dictionaries, where each dictionary represents a Yelp search result.
        Each dictionary typically includes information such as the title of the business,
        a link to its Yelp page, and sometimes additional details like ratings,
        review counts, and address.
    """
    params = {
        "engine": "yelp",
        "find_desc": search_term,
        "find_loc": location,
        "api_key": api_key  # Assumes 'api_key' is a globally defined variable containing the SerpAPI key.
    }

    search = GoogleSearch(params)  # Assumes 'GoogleSearch' is a class from the 'google-search-results' library.
    results = search.get_dict()
    organic_results = results["organic_results"]
    # return organic_results

    yelp_search_res = ""
    for i in range(len(organic_results)):
        # print(x[i])
        yelp_search_res += f"\n{i+1}"
        yelp_search_res += f"""
    Title : {Category(**organic_results[i]).title}
    Category : {Business(**organic_results[i]).categories[0].title}
    Rating : {Business(**organic_results[i]).rating}
    Neighborhoods : {Business(**organic_results[i]).neighborhoods}
    Price : {Business(**organic_results[i]).price}
    """
    return yelp_search_res