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