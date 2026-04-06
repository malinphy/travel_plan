from typing import Optional, Sequence, Any
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv
from openai import OpenAI
from agents.items import ToolCallItem, ToolCallOutputItem, MessageOutputItem
from backend.agents.prompts import REFLECTION_INSTRUCTIONS, REVISE_INSTRUCTIONS, THINKING_PROMPT, REACT_ZERO_SHOT, REACT_LOOP_2
from agents import trace
import uuid

load_dotenv()


class BaseAgent:
    def __init__(
        self,
        agent_name: str,
        inst: str,
        functions: Optional[Sequence[Any]] = None,
        self_reflect: Optional[bool] = False,
        model_name: str = "gpt-4o-mini",
        temperature: Optional[float] = 0.0,
        trace_id: Optional[str] = None,
        max_reflections: Optional[int] = None,
        thinking: Optional[bool] = False,
        react_zero: Optional[bool] = False,
    ) -> None:
        self.agent_name = agent_name
        self.instruction = inst
        self.model_name = model_name
        self.temperature = temperature
        self.trace_id = trace_id if trace_id is not None else str(uuid.uuid4())

        self.functions = list(functions) if functions else []
        self.reflect = bool(self_reflect)
        self.max_reflections = max_reflections
        self.thinking = thinking    
        self.react_zero = react_zero
        self.client = OpenAI()

        self.agent = self._build_agent(
            name=self.agent_name,
            instructions=self.instruction,
            tools=self.functions,
        )
        self.reflect_agent = self._build_agent(
            name=f"{self.agent_name}_critic",
            instructions=REFLECTION_INSTRUCTIONS,
        )
        self.revise_agent = self._build_agent(
            name=f"{self.agent_name}_reviser",
            instructions=REVISE_INSTRUCTIONS,
        )
        self.deepthink_agent = self._build_agent(
            name=f"{self.agent_name}_deepthink",
            instructions=THINKING_PROMPT,
        )

        self.react_zero_agent = self._build_agent(
            name=f"{self.agent_name}_deepthink",
            instructions=REACT_ZERO_SHOT,
        )


    def _build_agent(
        self,
        name: str,
        instructions: str,
        tools: Optional[Sequence[Any]] = None,
    ) -> Agent:
        kwargs = {
            "name": name,
            "instructions": instructions,
            "model": self.model_name,
            # "temperature": self.temperature,
        }
        if tools:
            kwargs["tools"] = list(tools)
        return Agent(**kwargs)

    def _reflect(self, query: str, answer: str) -> str:
        print("Criticizing...")
        critique = Runner.run_sync(
            self.reflect_agent,
            f"QUESTION:\n{query}\n\nANSWER:\n{answer}\n",
        ).final_output
        print("Revising...")
        revised = Runner.run_sync(
            self.revise_agent,
            f"QUESTION:\n{query}\n\nANSWER:\n{answer}\n\nCRITIQUE:\n{critique}\n",
        ).final_output
        return revised

    def _deepthink(self, query:str):
        print("Thinking...")
        thinking = Runner.run_sync(
            self.deepthink_agent, 
            f"QUESTION:\n{query}"
        ).final_output
        return thinking

    def _react_zero(self, query:str):
        print("Planning...")
        thinking = Runner.run_sync(
            self.react_zero_agent, 
            f"QUESTION:\n{query}"
        ).final_output
        return thinking

    def run(self, query: str) -> str:
        with trace(self.trace_id):
            res = Runner.run_sync(self.agent, query)
            answer = res.final_output

            used_tools = []
            for item in res.new_items:
                if isinstance(item, ToolCallItem):
                    raw = item.raw_item
                    used_tools.append(raw)
            tool_names = []
            for tool in used_tools:
                tool_names.append(tool.name)                

            if self.reflect and self.max_reflections > 0:
                for _ in range(self.max_reflections):
                    answer = self._reflect(query, answer)

            elif self.thinking:
                answer = self._deepthink(query)

            elif self.react_zero:
                answer = self._react_zero(query)

            if used_tools:
                return {"answer": answer, "used_tools":tool_names, "trace_id": self.trace_id}
            return {"answer": answer, "trace_id": self.trace_id}





# Example usage
# tools = [get_weather, web_search]
# res = BaseAgent(
#     agent_name=name,
#     inst=instruction,
#     functions=tools,
#     self_reflect=False,
#     max_reflections=1,
# ).run(query="make websearch find the olimpic city. tell me how is weather in olympic city")
# print(res["used_tools"])


