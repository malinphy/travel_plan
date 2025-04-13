import os 
from dotenv import load_dotenv
load_dotenv()
from agents import Agent, Runner
from agents.model_settings import ModelSettings
import nest_asyncio
from data_models.first_question_output_format import FinalModel
import datetime
from tools import flight_search, yelp_search, hotels_search, wikipedia_search, get_weather


question_rewrite_agent = Agent(
    name = "Customer Help",
    instructions= f"""
Today : {datetime.datetime.now().date()}

You are a helpful help desk agent at the travel company. Basically, your task it to understand the customers request, needs, demands. 
I want to you to learn and fill necessary fields to offer a reasonable travel to our customer. 

Try to extract the search terms from the question
    
""",
    model = 'gpt-4o-mini',
    # tools=[yelp_search],
    model_settings=ModelSettings(temperature= 0.0,
                                 max_tokens = 4096*2),
    output_type = FinalModel
)


flight_agent = Agent(
    name = "Google flight information",
    instructions= """
Always answer in Turkish language. Return all the given flight information

departure_id : Parameter defines the departure airport code or location kgmid. An airport code is an uppercase 3-letter code. For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport.

arrival_id : Parameter defines the arrival airport code or location kgmid. An airport code is an uppercase 3-letter code. You can search for it on Google Flights or IATA. For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport.

outbound_date : Parameter defines the outbound date. The format is YYYY-MM-DD. e.g. 2025-04-09

return_date : Parameter defines the return date. The format is YYYY-MM-DD. e.g. 2025-04-15
""",
    model = 'gpt-4o-mini',
    tools=[flight_search],
    # model_settings={"temperature": 0.0}
    # output_type = first_agent_output
    model_settings=ModelSettings(temperature= 0.0,
                                 max_tokens = 4096*2)
)
