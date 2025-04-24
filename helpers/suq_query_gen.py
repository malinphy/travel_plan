import os 
import sys

from dotenv import load_dotenv
from pydantic import BaseModel 
from typing import List,Optional
from openai import OpenAI

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))
from helpers.helper_prompts import GENERATE_SUBQUESTION_SYSTEM_PROMPT_TEMPLATE

client = OpenAI(api_key=os.environ['OPENAI_API_KEY_MALI'])


class SubQuestion(BaseModel):
    id : int 
    sub_question : str 
    depends_on : List[int]

class QuestionGroup(BaseModel):
    modified_question : Optional[str] = None
    subquestions : List[SubQuestion]


class SubQueryGen:
    def __init__(
        self,
        output_model:QuestionGroup,
        system_prompt:str,
        max_completion_tokens : int = 1024*2,
        model : str = 'gpt-4o-mini',
        temperature :float = 0.0,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.output_model = output_model
        self.system_prompt
        self.history = []
        self.max_completion_tokens = max_completion_tokens
        self.history.append({"role": "system", "content": self.system_prompt})

    def sub_to_str(self, event):
        total_sub_questions = ""
        for sub_q in event.subquestions:
            total_sub_questions += f"sub_question {sub_q.id} : {sub_q.sub_question}\n"

        return total_sub_questions
    def run(self,query):
        self.history.append({"role": "user", "content": query})
        completion = client.beta.chat.completions.parse(
            model=self.model,
            messages=self.history,
            response_format=self.output_model,
            temperature=0.0,
            max_completion_tokens= self.max_completion_tokens
        )
        print(completion)
        event = completion.choices[0].message.parsed
        total_subs = self.sub_to_str(event)
        self.history.append({"role": "assistant", "content": total_subs})
        return event, self.history
