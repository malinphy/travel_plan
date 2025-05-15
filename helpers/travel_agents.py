import os 
from dotenv import load_dotenv
load_dotenv()
from agents import Agent, Runner
from agents.model_settings import ModelSettings
import nest_asyncio
from data_models.first_question_output_format import FinalModel
from datetime import datetime
from helpers.tools import flight_search, yelp_search, hotels_search, wikipedia_search, get_weather
from helpers.function_tools import flight_search_2, hotels_search2, yelp_search2

question_rewrite_agent = Agent(
    name = "Customer Help",
    instructions= f"""


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

f_agent = Agent(name="Flight Assistant agent",
              instructions=f"""
Always answer in given language. Return the information from the given tool do not add extra information.

departure_id : Parameter defines the departure airport code or location kgmid. An airport code is an uppercase 3-letter code. For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport.

arrival_id : Parameter defines the arrival airport code or location kgmid. An airport code is an uppercase 3-letter code. You can search for it on Google Flights or IATA. For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport.

outbound_date : Parameter defines the outbound date. The format is YYYY-MM-DD. e.g. 2025-04-09

return_date : Parameter defines the return date. The format is YYYY-MM-DD. e.g. 2025-04-15


Today : {datetime.now().strftime("%Y-%m-%d")}

!!! Warning if departure_id, arrival_id, outbound_date or return_date is missing or cannot extract from the sentence, do not determine alone always ask the user.
""",
              model="gpt-4o-mini",
              # model = 'gpt-4o',
              model_settings=ModelSettings(temperature= 0.0,
                                #  max_tokens = 4096*8
                                tool_choice="required",
                                 ),
            tools= [flight_search_2]
              )

# h_agent 
h_agent = Agent(
    name = "Hotels Assistant agent",
    instructions=f"""Returns google hotels information.     
    q : Location
    gl : Country
    Today : {datetime.now().strftime("%Y-%m-%d")}
    !! Warning, while tool calling do not send date before today's date
    """,
    model = 'gpt-4o-mini',
    tools=[hotels_search2],
    model_settings=ModelSettings(temperature= 0.0,
                                #  max_tokens = 4096*2
                                 ),
)


y_agent = Agent(
    name = "Yelp Search information",
    instructions= f"""Returns Yelp search results.     
    search_term: str, 
    location: str
    Today : {datetime.now().strftime("%Y-%m-%d")}
    """.strip(),
    model = 'gpt-4o-mini',
    tools=[yelp_search2],
    model_settings=ModelSettings(temperature= 0.0,
                                #  max_tokens = 4096*2
                                 ),
)

t_agent = Agent(
    name = "Travel Assistant agent",
    instructions = """ 
Answer the users questions
""",
model = 'gpt-4o-mini',
   tools=[
       f_agent.as_tool(
           tool_name="flight_information",
           tool_description="Return flight information according to questions"
       ),
       h_agent.as_tool(
           tool_name="hotel_information",
           tool_description="Return hotel information according to questions"
       )
   ]

)