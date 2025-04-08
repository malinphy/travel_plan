from pydantic import BaseModel

class first_agent_output(BaseModel):
    departure_id: str
    arrival_id: str
    outbound_data : str 
    return_date : str