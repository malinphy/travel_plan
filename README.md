# Agentic Trip Planner

This repository contains a travel planning chatbot built using Python. The chatbot leverages the `agents` library and integrates with external APIs through tools to provide flight and hotel information.

## Features

*   **Conversational Interface:** Interact with the chatbot through a text-based interface.
*   **Flight Search:** Find flight options based on departure and arrival locations, and dates.
*   **Hotel Search:** Discover hotel accommodations with details on pricing, ratings, and amenities.
*   **Itinerary Planning:** The system can help in planning travel itineraries by breaking down complex requests into smaller steps.

## Project Structure

*   `malinphy-travel_plan/`
    *   `README.md`: This file.
    *   `main.py`: The main script for running the chatbot.
    *   `notes.txt`: Developer notes.
    *   `requirements.txt`: Lists project dependencies.
    *   `TEST8.ipynb`: A Jupyter notebook for testing specific functionalities.
    *   `data_models/`: Contains Pydantic models for structuring data.
        *   `context_models.py`
        *   `first_agent_output.py`
        *   `first_question_output_format.py`
        *   `flight_data_models.py`
        *   `hotel_data_models.py`
        *   `query_planner.py`
        *   `yelp_data_models.py`
    *   `fe/`: Frontend files for a basic chat interface.
        *   `index.html`
        *   `main.py`: FastAPI backend for the frontend.
        *   `script.js`
        *   `style.css`
    *   `helpers/`: Contains utility functions and agent definitions.
        *   `api_functions.py`: Direct API interaction functions.
        *   `flight_insights.py`: For analyzing flight price trends.
        *   `function_tools.py`: Definitions of tools used by agents.
        *   `helper_agents.py`: Definitions of various helper agents.
        *   `helper_functions.py`: General helper functions.
        *   `helper_prompts.py`: Prompts used for agent instructions.
        *   `suq_query_gen.py`: Sub-query generation utility.
        *   `tools.py`: Additional tool definitions.
        *   `travel_agents.py`: Specific agents for travel-related tasks.

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd malinphy-travel_plan
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up API Keys:**
    *   Ensure you have the necessary API keys (e.g., for OpenAI, SerpAPI) and set them as environment variables. The `main.py` and `helpers/tools.py` files reference `OPENAI_API_KEY_MALI` and `SERPAPI_API_KEY`.
4.  **Run the chatbot:**
    *   Execute the `main.py` script:
        ```bash
        python main.py
        ```
    *   For the interactive web interface, you may need to run the FastAPI backend and serve the frontend files separately. Refer to the `fe/` directory for details.

## Usage

The `main.py` script provides different ways to interact with the chatbot:

*   **Class-based approach:** Demonstrates initializing and using the `TravelChatbot` class for a conversational flow.
*   **Function-based approach:** A simpler approach for processing queries.
*   **Interactive loop:** Allows for real-time chat interaction in the console.

You can choose which approach to run by uncommenting the relevant section in the `if __name__ == "__main__":` block of `main.py`.
