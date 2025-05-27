from pydantic import BaseModel
from typing import Optional, List
class Step(BaseModel):
    '''Required individual step to answer the question.'''
    explanation: str

class SubAgents(BaseModel):
    '''Required tool to answer the question.'''
    name: str 

class StepWithAgents(BaseModel):
    '''A step and the agents required for that specific step.'''
    step: Step
    agents: Optional[List[SubAgents]] = None

class ChainOfThought(BaseModel):
    '''Final answer with a sequence of steps, each with its associated agents.'''
    sequence: List[StepWithAgents]