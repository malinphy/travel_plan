import os 
import sys
import uuid
import re
from dotenv import load_dotenv
from pydantic import BaseModel 
from typing import List, Optional
from openai import OpenAI
import pandas as pd
import numpy as np
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents import Agent, Runner, ModelSettings, trace, handoff, function_tool, TResponseInputItem
from helpers.helper_agents import recommender_agent, responsive_agent, query_rewrite, travel_info_agent
from helpers.travel_agents import f_agent, h_agent, y_agent
from helpers.function_tools import flight_search_2, hotels_search2, city_to_airport_code, yelp_search2, ticket_to_markdown
from helpers.helper_functions import assemble_conversation, text_maker
from agents.extensions.visualization import draw_graph
import nest_asyncio
nest_asyncio.apply()
from IPython.display import Markdown, display

from datetime import datetime  # Ensure correct import for datetime
from agents import Agent, RunContextWrapper, Runner, function_tool
from helpers.helper_prompts import GENERATE_SUBQUESTION_SYSTEM_PROMPT_TEMPLATE, GENERATE_SUBQUESTION_SYSTEM_PROMPT_TEMPLATE2
from helpers.suq_query_gen import SubQueryGen
from helpers.helper_agents import planner_agent
client = OpenAI(api_key=os.environ['OPENAI_API_KEY_MALI'])
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

class TravelChatbot:
    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.conversation_history = []
        self.current_res = None
        self.is_first_message = True
        
        # Initialize help agent
        self.help_agent = Agent(
            name='help desk agent', 
            instructions=f"""You are an experienced and kind help desk agent. Help users in terms of their needs, if the question about travel. 
            You may need to call multiple agents to get all answers.
            Today : {datetime.now().strftime("%Y-%m-%d")}""",
            model='gpt-4.1',
            tools=[
                f_agent.as_tool(
                    tool_name="flight_information_agent",
                    tool_description="Search the flight information"
                ),
                h_agent.as_tool(
                    tool_name="hotel_information_agent", 
                    tool_description="Search the hotel information"
                ),
                y_agent.as_tool(
                    tool_name="food_information_agent", 
                    tool_description="Search the restaurants and place for food information"
                ),
            ],
            model_settings=ModelSettings(temperature=0.0),
        )
        
        print(f"Chatbot initialized with UUID: {self.uuid}")
    
    def process_message(self, user_query: str):
        """Process a user message and return the response"""
        print(f"UUID: {self.uuid}")
        
        with trace(self.uuid):
            if self.is_first_message:
                # First message flow
                res_planner = Runner.run_sync(planner_agent, user_query)
                res = Runner.run_sync(
                    self.help_agent, 
                    assemble_conversation(res_planner, text_maker(res_planner))
                )
                
                # Store the result for future messages
                self.current_res = res
                self.is_first_message = False
                
            else:
                # Continuation flow
                res_planner = Runner.run_sync(
                    planner_agent, 
                    assemble_conversation(self.current_res, user_query)
                )
                res = Runner.run_sync(
                    self.help_agent, 
                    assemble_conversation(res_planner, text_maker(res_planner))
                )
                
                # Update the stored result
                self.current_res = res
            
            # Store conversation history
            self.conversation_history.append({
                'user_query': user_query,
                'response': res.final_output,
                'timestamp': datetime.now().isoformat()
            })
            
            print(res.final_output)
            return res.final_output
    
    def reset_conversation(self):
        """Reset the conversation to start fresh"""
        self.uuid = str(uuid.uuid4())
        self.conversation_history = []
        self.current_res = None
        self.is_first_message = True
        print(f"Conversation reset. New UUID: {self.uuid}")
    
    def get_conversation_history(self):
        """Get the full conversation history"""
        return self.conversation_history


# Usage examples:

# Option 1: Class-based approach (recommended)
def main_class_based():
    # Initialize chatbot
    chatbot = TravelChatbot()
    
    # First message
    response1 = chatbot.process_message("I want to travel from ankara to amsterdam")
    
    # Follow-up messages
    response2 = chatbot.process_message("The dates are 23-06-2025 and 28-06-2025")
    response3 = chatbot.process_message("I need a hotel near the airport")
    
    # Get conversation history
    history = chatbot.get_conversation_history()
    print(f"Total messages: {len(history)}")


# Option 2: Function-based approach (simpler)
def create_simple_chatbot():
    # Global variables to maintain state
    global myuuid, current_res, is_first_message
    
    myuuid = str(uuid.uuid4())
    current_res = None
    is_first_message = True
    
    # Initialize help agent
    help_agent = Agent(
        name='help desk agent', 
        instructions=f"""You are an experienced and kind help desk agent. Help users in terms of their needs, if the question about travel. 
        You may need to call multiple agents to get all answers.
        Today : {datetime.now().strftime("%Y-%m-%d")}""",
        model='gpt-4.1',
        tools=[
            f_agent.as_tool(
                tool_name="flight_information_agent",
                tool_description="Search the flight information"
            ),
            h_agent.as_tool(
                tool_name="hotel_information_agent", 
                tool_description="Search the hotel information"
            ),
            y_agent.as_tool(
                tool_name="food_information_agent", 
                tool_description="Search the restaurants and place for food information"
            ),
        ],
        model_settings=ModelSettings(temperature=0.0),
    )
    
    print(f"UUID: {myuuid}")
    return help_agent

def process_query(help_agent, user_query: str):
    global myuuid, current_res, is_first_message
    
    print(f"UUID: {myuuid}")
    
    with trace(myuuid):
        if is_first_message:
            # First message
            res_planner = Runner.run_sync(planner_agent, user_query)
            res = Runner.run_sync(help_agent, assemble_conversation(res_planner, text_maker(res_planner)))
            current_res = res
            is_first_message = False
        else:
            # Follow-up messages
            res_planner = Runner.run_sync(planner_agent, assemble_conversation(current_res, user_query))
            res = Runner.run_sync(help_agent, assemble_conversation(res_planner, text_maker(res_planner)))
            current_res = res
        
        print(res.final_output)
        return res.final_output

# Usage for function-based approach
def main_function_based():
    help_agent = create_simple_chatbot()
    
    # First message
    response1 = process_query(help_agent, "I want to travel from ankara to amsterdam")
    
    # Follow-up messages
    response2 = process_query(help_agent, "The dates are 23-06-2025 and 28-06-2025")
    response3 = process_query(help_agent, "I need a hotel near the airport")


# Option 3: Interactive loop
def interactive_chatbot():
    chatbot = TravelChatbot()
    
    print("Travel Chatbot started! Type 'quit' to exit, 'reset' to start over.")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        elif user_input.lower() == 'reset':
            chatbot.reset_conversation()
            print("Conversation reset!")
            continue
        elif user_input:
            try:
                response = chatbot.process_message(user_input)
                print(f"Bot: {response}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Please enter a message.")


if __name__ == "__main__":
    # Choose which approach to run
    print("Running class-based approach...")
    main_class_based()
    
    # Uncomment to run interactive chatbot
    # interactive_chatbot()