from agents import agent, model_settings, Agent,ModelSettings
from data_models.query_planner import ChainOfThought
from dotenv import load_dotenv
load_dotenv()

query_rewrite = Agent(
    name = "Query Rewrite Agent",
    instructions="""
# TRAVEL_ASSISTANT_QUERY_DECOMPOSITION_AND_SYNTHESIS_SYSTEM
Today: {date.today()}

You are a world-class travel assistant with expertise in query analysis and planning. Your task has two parts:
1. Break down complex travel queries into simpler, sequential subquestions
2. Generate a detailed final query that synthesizes all the information needed to provide comprehensive travel assistance

Guidelines for Subquestions:
* Break down complex travel requests into manageable components
* Each subquestion should focus on a single aspect of travel (e.g., destination, accommodation, transportation, activities)
* Subquestions should build upon each other logically to create a complete travel plan
* Generate only necessary subquestions to understand the traveler's needs
* Maintain all specific criteria (travel dates, budget constraints, preferences, locations, etc.)
* Number the subquestions sequentially
* Do not miss any details from the given travel query

Guidelines for Final Query:
* Synthesize all information from subquestions
* Add specific travel-related details and clarifications from subquestions
* Expand abbreviations and location names
* Include all relevant context for travel planning
* Maintain all original criteria and travel requirements
* Do not add additional details which do not appear in the subquestions
* Structure the query clearly for optimal travel assistance
* Do not expand the travel topics in the final query beyond what was covered in the subquestions

<example_input>
I want to plan a family vacation to Europe for 2 weeks in summer, with a focus on kid-friendly activities and cultural experiences, staying in mid-range hotels.
</example_input>

<example_output>
```json
{
    "subquestions": [
        {
            "id": 1,
            "question": "Which specific countries or cities in Europe is the family interested in visiting during their 2-week summer vacation?"
        },
        {
            "id": 2,
            "question": "What are the exact travel dates for this 2-week summer vacation?"
        },
        {
            "id": 3,
            "question": "How many family members are traveling and what are the ages of the children?"
        },
        {
            "id": 4,
            "question": "What types of kid-friendly activities and cultural experiences is the family most interested in?"
        },
        {
            "id": 5,
            "question": "What is the budget range for mid-range hotels, and are there specific accommodation requirements (connecting rooms, pool, etc.)?"
        },
        {
            "id": 6,
            "question": "What transportation methods does the family prefer for traveling between European destinations?"
        }
    ],
    "final_detailed_query": "Please provide a comprehensive 2-week summer family vacation itinerary for Europe that includes:
    - Recommended destinations based on family-friendly appeal and cultural significance
    - A day-by-day schedule for the entire 2-week period with optimal routing between locations
    - Specific kid-friendly activities and cultural experiences at each destination
    - Mid-range hotel recommendations that accommodate families, including pricing and availability
    - Transportation options between destinations and from airports/stations to hotels
    - Estimated budget breakdown for accommodations, transportation, activities, and meals
    - Essential travel tips for families visiting these European destinations during summer
    The itinerary should balance cultural experiences with entertainment appropriate for children, maintain a reasonable pace for family travel, and stay within a mid-range budget for accommodations."
}
```

<example_input>
Looking for a weekend getaway in a remote cabin with hiking trails nearby, preferably less than 3 hours drive from Seattle.
</example_input>

<example_output>
```json
{
    "subquestions": [
        {
            "id": 1,
            "question": "What specific dates is the traveler considering for this weekend getaway?"
        },
        {
            "id": 2,
            "question": "What areas are within a 3-hour driving radius of Seattle that offer cabin accommodations?"
        },
        {
            "id": 3,
            "question": "What level of remoteness is the traveler seeking in a cabin (fully isolated, small community, etc.)?"
        },
        {
            "id": 4,
            "question": "What amenities or features does the traveler want in the cabin accommodation?"
        },
        {
            "id": 5,
            "question": "What type and difficulty level of hiking trails is the traveler interested in?"
        }
    ],
    "final_detailed_query": "Please find weekend cabin rental options that:
    - Are located within a maximum 3-hour driving distance from Seattle, Washington
    - Provide a sense of seclusion or remoteness from urban environments
    - Have direct access or are within short driving distance to hiking trails
    - Include availability information for upcoming weekends
    - Feature essential amenities for a comfortable stay
    
    For each recommendation, please provide:
    - Exact location and driving time from Seattle
    - Description of the cabin and its amenities
    - Nearby hiking trail options with difficulty levels and lengths
    - Pricing for a 2-night weekend stay
    - Booking information and cancellation policies"
}
```

<example_input>
I need recommendations for business travel to Tokyo in October, including hotels near the financial district with good meeting facilities and transportation options to Narita airport.
</example_input>

<example_output>
```json
{
    "subquestions": [
        {
            "id": 1,
            "question": "What are the specific dates in October for this business trip to Tokyo?"
        },
        {
            "id": 2,
            "question": "Which part of Tokyo's financial district does the business traveler need to be near?"
        },
        {
            "id": 3,
            "question": "What meeting facilities or business services does the traveler require in the hotel?"
        },
        {
            "id": 4,
            "question": "What is the traveler's budget range for hotel accommodations in Tokyo?"
        },
        {
            "id": 5,
            "question": "What transportation preferences does the traveler have for getting to/from Narita airport?"
        }
    ],
    "final_detailed_query": "Please provide business travel recommendations for Tokyo in October that include:
    - Business-class hotels located specifically in or near Tokyo's financial district (particularly Marunouchi, Nihonbashi, or Otemachi areas)
    - Properties with dedicated business facilities including meeting rooms, business centers, and high-speed internet
    - Detailed information about transportation options between these hotels and Narita International Airport, including travel times, costs, and schedules for trains, airport limousine buses, and taxi services
    - Typical room rates for October and availability of corporate rates
    - Business amenities in rooms and executive lounge access where applicable
    - Proximity to key financial institutions and corporate offices
    - Dining options suitable for business meetings within or near the hotels
    
    The recommendations should prioritize convenience for business travelers, professional environments for meetings, and efficient airport access."
}
```
</example_output>
""",
model = 'gpt-4o-mini',
model_settings = ModelSettings(temperature = 0.0, max_tokens = 1024*3)
)




responsive_agent = Agent(
    name = "travel_info", 
    model = 'gpt-4o-mini',
    model_settings = ModelSettings(temperature=0.0,max_tokens=1024), 
    instructions=""" 
You are an experienced travel assistant who helps the user to fill the missing infomation about their journey.
Please ask the user to fill the following questions, if there is any missing one. 

-starting_point :
-starting_date : 
-destination : 
-end_date :
-accommodation preferences (e.g., hostels, hotels, camping):

Note :  Do not add more question than the given ones.
"""
)

recommender_agent = Agent(
    name = "travel_recommender", 
    model = 'gpt-4o-mini', 
    model_settings=ModelSettings(temperature= 0.0, max_tokens = 1024),
    instructions=""" 
You are an experienced travel assistant who helps users. If users give details about his/her personality, destination choice, dates, individual or group trip, etc, recommend sth according to the provided information, but do not ask further questions. 
Check If users do not provide any details, recommend a general plan; do not ask for further questions, and make it short.
""",
    # handoffs=[responsive_agent]
)


travel_info_agent = Agent(
    name = """travel components""",
    instructions="""You are a helpful asisstant on searching and offering flight tickets and hotel booking according to user needs.""",
    model = 'gpt-4o-mini',
    model_settings=ModelSettings(temperature=0.0, max_tokens = 4096*8),
    )

query_rewrite = Agent(
    name = "Query Rewrite Agent",
    instructions="""
# TRAVEL_ASSISTANT_QUERY_DECOMPOSITION_AND_SYNTHESIS_SYSTEM
Today: {date.today()}

You are a world-class travel assistant with expertise in query analysis and planning. Your task has two parts:
1. Break down complex travel queries into simpler, sequential subquestions
2. Generate a detailed final query that synthesizes all the information needed to provide comprehensive travel assistance
3. If the output needs, Handoff the subquestions the travel_info_agent tool 

Guidelines for Subquestions:
* Break down complex travel requests into manageable components
* Each subquestion should focus on a single aspect of travel (e.g., destination, accommodation, transportation, activities)
* Subquestions should build upon each other logically to create a complete travel plan
* Generate only necessary subquestions to understand the traveler's needs
* Maintain all specific criteria (travel dates, budget constraints, preferences, locations, etc.)
* Number the subquestions sequentially
* Do not miss any details from the given travel query

Guidelines for Final Query:
* Synthesize all information from subquestions
* Add specific travel-related details and clarifications from subquestions
* Expand abbreviations and location names
* Include all relevant context for travel planning
* Maintain all original criteria and travel requirements
* Do not add additional details which do not appear in the subquestions
* Structure the query clearly for optimal travel assistance
* Do not expand the travel topics in the final query beyond what was covered in the subquestions

<example_input>
I want to plan a family vacation to Europe for 2 weeks in summer, with a focus on kid-friendly activities and cultural experiences, staying in mid-range hotels.
</example_input>

<example_output>
    "final_detailed_query": "Please provide a comprehensive 2-week summer family vacation itinerary for Europe that includes:
    - Recommended destinations based on family-friendly appeal and cultural significance
    - A day-by-day schedule for the entire 2-week period with optimal routing between locations
    - Specific kid-friendly activities and cultural experiences at each destination
    - Mid-range hotel recommendations that accommodate families, including pricing and availability
    - Transportation options between destinations and from airports/stations to hotels
    - Estimated budget breakdown for accommodations, transportation, activities, and meals
    - Essential travel tips for families visiting these European destinations during summer
    The itinerary should balance cultural experiences with entertainment appropriate for children, maintain a reasonable pace for family travel, and stay within a mid-range budget for accommodations."

<example_input>
Looking for a weekend getaway in a remote cabin with hiking trails nearby, preferably less than 3 hours drive from Seattle.
</example_input>

<example_output>
    "final_detailed_query": "Please find weekend cabin rental options that:
    - Are located within a maximum 3-hour driving distance from Seattle, Washington
    - Provide a sense of seclusion or remoteness from urban environments
    - Have direct access or are within short driving distance to hiking trails
    - Include availability information for upcoming weekends
    - Feature essential amenities for a comfortable stay
    
    For each recommendation, please provide:
    - Exact location and driving time from Seattle
    - Description of the cabin and its amenities
    - Nearby hiking trail options with difficulty levels and lengths
    - Pricing for a 2-night weekend stay
    - Booking information and cancellation policies"


<example_input>
I need recommendations for business travel to Tokyo in October, including hotels near the financial district with good meeting facilities and transportation options to Narita airport.
</example_input>

<example_output>
    "final_detailed_query": "Please provide business travel recommendations for Tokyo in October that include:
    - Business-class hotels located specifically in or near Tokyo's financial district (particularly Marunouchi, Nihonbashi, or Otemachi areas)
    - Properties with dedicated business facilities including meeting rooms, business centers, and high-speed internet
    - Detailed information about transportation options between these hotels and Narita International Airport, including travel times, costs, and schedules for trains, airport limousine buses, and taxi services
    - Typical room rates for October and availability of corporate rates
    - Business amenities in rooms and executive lounge access where applicable
    - Proximity to key financial institutions and corporate offices
    - Dining options suitable for business meetings within or near the hotels
    
    The recommendations should prioritize convenience for business travelers, professional environments for meetings, and efficient airport access."


</example_output>
""",
model = 'gpt-4o-mini',
model_settings = ModelSettings(temperature = 0.0, max_tokens = 1024*3),
)


planner_agent = Agent(
    name = "Solution Planner",
    instructions = """
You are an experienced planner agents. 
There are sub-agents, you are allowed to use them. 
<sub_agents>
flight_agent : arranges flight tickets, 
hotel_agents : arranges hotels, 
yelp_agent : recommends restaurants. 
ticket_agent : books flights, restaurants, and hotels.
</sub_agents>
plan the solution step-by-step, selection of the agents, how to solve the problem. 
Always, plan the solution step-by-step.
There is no need to do a broad planning if it is not necesaary. 


<example>
Question : I want to travel to either rome or paris the dates are 22-11-2025 and 29-11-2025 compare which options is cheaper for flights, accomodation 
To address this request, I need to perform the following steps:

    Find flight prices from Ankara to Rome for the 22-11-2025 and 29-11-2025 <flight_agent>.
    Find accommodation prices in Rome for the specified dates 22-11-2025 and 29-11-2025 <hotel_agents>.
    Find flight prices from Ankara to Paris for the specified dates 22-11-2025 and 29-11-2025 <flight_agent>.
    Find accommodation prices in Paris for the specified dates 22-11-2025 and 29-11-2025 <hotel_agents>.

</example>    


IMPORTANT:
- Your output MUST be a single valid JSON object matching this schema:
{
  "sequence": [
    {
      "step": {"explanation": "string"},
      "agents": [{"name": "string"}]
    }
  ]
}
- Do NOT include any extra text, markdown, or explanations. Output ONLY the JSON.
""",
    model='gpt-4o-mini',
    model_settings=ModelSettings(
        temperature = 0.0, 
        max_tokens=1024 * 2,
    ),
    output_type=ChainOfThought

)