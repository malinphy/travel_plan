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