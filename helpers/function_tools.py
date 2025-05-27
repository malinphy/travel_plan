from typing import Optional
from agents import function_tool
import wikipedia
import requests
import os 
import numpy as np 
import pandas as pd
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
from IPython.display import Markdown, display
from datetime import datetime



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
def flight_search_2(
    departure_id: Optional[str] = None, 
    arrival_id: Optional[str] = None, 
    outbound_date: Optional[str] = None, 
    return_date: Optional[str] = None
) -> str:
    
    if departure_id == None and arrival_id == None and outbound_date == None:
        return "If you can inform about departure city, destination city and outbound_data, I can look for the flight tickets"
    
    elif departure_id == None and arrival_id == None : 
        return "If you can inform about departure city and destination city, I can look for the flight tickets"
    
    elif departure_id == None  : 
        return "If you can inform about departure city, I can look for the flight tickets"
    
    elif arrival_id == None  : 
        return "If you can inform about destination city, I can look for the flight tickets"
    
    elif outbound_date == None  : 
        return "If you can inform about departure date, I can look for the flight tickets"

    f"""
    Today : {datetime.now().strftime("%Y-%m-%d")}
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
        "outbound_date": outbound_date,
        "return_date": return_date,
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
def hotels_search2(
    q:Optional[str] = None, 
    check_in_date:Optional[str] = None, 
    check_out_date:Optional[str] = None, 
    gl:Optional[str] = None
    ):
    """
    Searches for hotels using Google Hotels via SerpAPI.

    Args:
        q (Optional[str]): Location or query string for the hotel search (e.g., city or hotel name).
        check_in_date (Optional[str]): Check-in date in 'YYYY-MM-DD' format.
        check_out_date (Optional[str]): Check-out date in 'YYYY-MM-DD' format.
        gl (Optional[str]): . It's a two-letter country code. (e.g., us for the United States, uk for United Kingdom, or fr for France.

    Returns:
        str: A formatted string with hotel information or a message if required fields are missing.
    """

    if check_in_date == None and check_out_date == None: 
        return "please identify the check-in and check-out date for more information"
    
    elif check_in_date == None:
        return "please inform me about check-in date"
    
    elif check_out_date == None:
        return "please inform me about check-out date"
    
    f"""
    
    Google hotels information from SERPAPI. Returns json structure
    q : Location
    gl : Country
    Today : {datetime.now().strftime("%Y-%m-%d")}
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

@function_tool
def city_to_airport_code(city:str)->str:
    """
    This function takes the city name and returns the IATA code of the airport in the given city.
    An IATA code is a three-letter identifier, also known as an IATA location identifier, used to designate airports and some non-airport locations like train or ferry stations
    """
    df = pd.read_csv(r"E:\PERSONAL_PROJ\travel_plan\airport_data\airports.csv")
    con1 = df['city'] == city
    con2 = ~pd.isna(df['iata'])
    return df[con1 & con2]['iata']

@function_tool
def ticket_to_markdown(departure_city : str, destination_city:str, inbound_date: str, outbound_date:str, price:str)->None:
    """ 
    
    """

    ticket = f"""# ✈️ Boarding Pass

**Flight:** ABC1285  
**Boarding Time:** 10:20  
**Gate:** 15  
**Seat:** 11A  
**Class:** Economy  

---

**Passenger Name:** John / Doe  
**From:** {departure_city}  
**To:** {destination_city}  
**inbound_date:** {inbound_date} 
**outbound_date:** {outbound_date} 

**Price:** {price}
---

**E-Ticket:** 220-1408858707
""".strip()
    display(Markdown(ticket.format(departure_city= departure_city, destination_city=destination_city, inbound_date=inbound_date, outbound_date=outbound_date, price=price)))