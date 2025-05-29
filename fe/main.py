# import os
# from fastapi import FastAPI
# from pydantic import BaseModel
# import uvicorn

# app = FastAPI()

# class Message(BaseModel):
#     message: str

# @app.post("/generate")
# async def generate_text(message: Message):
#     """
#     Endpoint to receive a message and generate text using the LLM script.
#     """
#     user_message = message.message
#     # Placeholder for calling the LLM script and returning the response
#     return {"response": f"Received message: {user_message}. LLM response placeholder."}

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

import os
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()
app = FastAPI()

origins = [
    "http://localhost:8000",  # Your FastAPI origin
    "http://127.0.0.1:8000", # Your FastAPI origin
    # Add the origin of your frontend if it's running on a different server
    "http://127.0.0.1:8001", # Example if you're serving frontend on port 8001
    "http://localhost:8001", # Example if you're serving frontend on port 8001
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class Message(BaseModel):
    message: str

def generate_text_from_llm(user_message: str) -> str:
    """
    Generates text using the Gemini LLM.

    Args:
        user_message: The message from the user.

    Returns:
        The generated text from the LLM.
    """
    try:
        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"],
        )

        model = "gemini-2.0-flash"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="""hey"""),],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""Hi there! How can I help you today?
"""),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_message),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
        )

        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text

        return response_text

    except Exception as e:
        print(f"Error generating text: {e}")
        return f"Error: {e}"


@app.post("/generate")
async def generate_text(message: Message):
    """
    Endpoint to receive a message and generate text using the LLM script.
    """
    user_message = message.message
    llm_response = generate_text_from_llm(user_message)
    return {"response": llm_response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))