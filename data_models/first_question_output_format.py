from pydantic import Field, BaseModel# for flight api


class FlightOutput(BaseModel):
    departure_id : str 
#     = Field(description="""
# Parameter defines the departure airport code or location kgmid.
# An airport code is an uppercase 3-letter code. 
# For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport.
# """)
    arrival_id : str
#     = Field(description="""
# Parameter defines the arrival airport code or location kgmid.
# An airport code is an uppercase 3-letter code.
# For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport.
# """)
    outbound_data : str 
    return_data : str 

class YelpOutput(BaseModel):
    search_term : str = Field(description="""
the search term should be extracted from questions. 
<example>                              
Question = I will travel to Istanbul and like to eat sea food. 
search_term = sea food
</example>                                                     

""")
    location : str = Field(description="""
<example>                              
Question = I will travel to Istanbul, sariyer and like to eat sea food. 
location = Istanbul, sariyer
</example> 
""")

class HotelOutput(BaseModel):
    query : str = Field(description=  """
the search term should be extracted from questions. Search term can contain more than one keywords. It can be city, district, multiple destinations.
<example>                              
Question = I will travel to Istanbul, sariyer and like to eat sea food. 
query = Istanbul, sariyer
</example> 
""")
    check_in_date : str 
    check_out_date : str 
    gl : str

class FinalModel(BaseModel):
    flight_reqs : FlightOutput
    yelp_reqs : YelpOutput
    hotel_reqs : HotelOutput    