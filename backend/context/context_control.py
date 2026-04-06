from agents.items import TResponseInputItem  # dict-like item
from typing import List
import copy

class ContextEngineer:
    def __init__(self, history: List[TResponseInputItem] | None = None):
        """
        Initializes the ContextEngineer with an existing history.
        Uses a deepcopy to avoid mutating the original history list.
        """
        self.history: List[TResponseInputItem] = copy.deepcopy(history) if history else []

    def get_history(self) -> List[TResponseInputItem]:
        """Returns the current state of the engineered history."""
        return self.history

    def append_user_message(self, text: str):
        """Adds a new user message to the end of the context."""
        self.history.append({
            "role": "user",
            "content": text
        })
        return self

    def insert_system_message(self, text: str, index: int = 0):
        """
        Inserts a system/developer message at a specific point in the context.
        Helpful if you want to silently change the agent's instructions mid-conversation.
        """
        self.history.insert(index, {
            "role": "system",
            "content": text
        })
        return self

    def remove_last_turn(self):
        """
        Removes the very last item in the history (useful for 'undo' functionality
        if the agent gave a bad response).
        """
        if self.history:
            self.history.pop()
        return self

    def delete_tool_calls_and_outputs(self, target_tool_name: str | None = None):
        """
        Removes all tool calls and their corresponding outputs from the history.
        If `target_tool_name` is provided, only deletes calls for that specific tool.
        This forces the agent to 'forget' that it already searched the database.
        """
        engineered_history = []
        skip_call_ids = set()

        # First pass to find the function calls we want to delete
        for item in self.history:
            if item.get("type") == "function_call":
                if target_tool_name is None or item.get("name") == target_tool_name:
                    skip_call_ids.add(item.get("call_id"))

        # Second pass to build the new history without those calls/outputs
        for item in self.history:
            if item.get("type") == "function_call" and item.get("call_id") in skip_call_ids:
                continue
            if item.get("type") == "function_call_output" and item.get("call_id") in skip_call_ids:
                continue
            engineered_history.append(item)

        self.history = engineered_history
        return self

    def delete_failed_function_calls(self, error_keyword: str = "Error"):
        """
        Scans for function call outputs that contain an error message.
        If found, it removes BOTH the tool call output and the original tool call,
        effectively acting as if the agent never made the mistake.
        """
        failed_call_ids = set()

        for item in self.history:
            if item.get("type") == "function_call_output":
                output_text = str(item.get("output", ""))
                if error_keyword in output_text or "Exception" in output_text or "validation errors" in output_text:
                    failed_call_ids.add(item.get("call_id"))

        engineered_history = []
        for item in self.history:
            if item.get("type") == "function_call" and item.get("call_id") in failed_call_ids:
                continue
            if item.get("type") == "function_call_output" and item.get("call_id") in failed_call_ids:
                continue
            engineered_history.append(item)

        self.history = engineered_history
        return self

    def override_last_assistant_message(self, new_text: str):
        """
        Replaces the text of the last thing the assistant said.
        You can use this to 'force' the agent to have concluded something else.
        """
        for i in reversed(range(len(self.history))):
            if self.history[i].get("role") == "assistant" and self.history[i].get("type") == "message":
                self.history[i]["content"] = [
                    {
                        "type": "output_text",
                        "text": new_text
                    }
                ]
                return self
        return self

    def refresh_crucial_data(self):
        """
        Scans past tool outputs for important data (like search_id)
        and appends a system message reminding the agent of it.
        """
        extracted_search_id = None

        for item in self.history:
            if item.get("type") == "function_call_output":
                output_str = str(item.get("output", ""))

                for id_key in ["flight_search_id", "hotel_search_id", "yelp_search_id"]:
                    if id_key in output_str:
                        try:
                            import json
                            output_dict = json.loads(output_str.replace("'", '"'))
                            extracted_search_id = output_dict.get(id_key)
                        except Exception:
                            if "is: " in output_str:
                                extracted_search_id = output_str.split("is: ")[-1].strip()

                        if extracted_search_id:
                            query_tool_name = (
                                id_key
                                .replace("search_id", "options")
                                .replace("flight_options", "query_flight_options")
                                .replace("hotel_options", "query_hotel_options")
                                .replace("yelp_options", "query_yelp_options")
                            )
                            self.history.append({
                                "role": "system",
                                "content": (
                                    f"CRITICAL CONTEXT REMINDER: Your active database {id_key} is "
                                    f"'{extracted_search_id}'. Use this exactly for any {query_tool_name} calls."
                                )
                            })
                            extracted_search_id = None

        return self
