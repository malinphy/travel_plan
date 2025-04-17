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
## tools
@function_tool
def flight_search(departure_id:str, arrival_id:str, outbound_data:str, return_date:str):
    """
    Google flight information from SERPAPI. Returns json structure
    """
    params = {
    "api_key" : api_key,
    "engine" : "google_flights",
    "departure_id": departure_id,
    "arrival_id": arrival_id,
    "outbound_date": outbound_data,
    "return_date": return_date,
    "currency": "USD",
    "hl": "en",
    "deep_search" : True
    }

    search = requests.get("https://serpapi.com/search", params=params)
    response = search.json()

    return response

@function_tool
def yelp_search(search_term:str, location:str ):
    params = {
    "engine": "yelp",
    "find_desc": search_term,
    "find_loc": location,
    "api_key": api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results["organic_results"]
    return organic_results

@function_tool
def hotels_search(q:str, check_in_date:str, check_out_date:str, gl:str):
    """
    Google hotels information from SERPAPI. Returns json structure
    q : Search Query
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

    return results

@function_tool
def wikipedia_search(location:str)->str:
    """Returns the wikipedia page content for the given location"""
    wikipedia_page = wikipedia.search(location)
    page_content = wikipedia_page.content

    return page_content

@function_tool
def get_weather(latitude: float, longitude: float) -> float:
    """Get the current temperature for a given location.
    
    Args:
        latitude: Latitude of the location (float)
        longitude: Longitude of the location (float)
    
    Returns:
        Current temperature in Celsius (float)
    """
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    return data['current']['temperature_2m']



print('END OF THE SCRIPT')