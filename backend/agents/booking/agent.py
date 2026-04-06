from agents import Agent
from model_configs import BOOKING_AGENT
from backend.agents.booking.tools import (
    get_or_create_basket,
    view_basket,
    get_latest_results,
    add_to_basket,
    remove_from_basket,
    modify_basket_item,
)

booking_agent = Agent(
    name="BookingAgent",
    instructions="""You manage the user's travel basket — their selected itinerary of flights and hotels.

WORKFLOW FOR EVERY REQUEST:
1. Call get_or_create_basket() (no arguments needed) first to get the basket_id.
2. Perform the requested operation (add / remove / modify).
3. Always call view_basket(basket_id) at the end and show the user the updated basket.

ADDING AN ITEM:
- Call get_latest_results(item_type) to list available options with their IDs.
 - Match the user's description (e.g. "cheapest flight", "the Marriott") to the correct item_id.
- Call add_to_basket(basket_id, item_type, item_id).

REMOVING AN ITEM:
- Call view_basket(basket_id) to get basket_item_ids.
- Call remove_from_basket(basket_id, basket_item_id).

CHANGING AN ITEM:
- Call view_basket to get the basket_item_id of the item to replace.
- Call get_latest_results(item_type) to find the replacement's item_id.
- Call modify_basket_item(basket_id, basket_item_id, new_item_id).

RULES:
- Never guess IDs. Always look them up via get_latest_results or view_basket.
- item_type values are exactly: 'flight' or 'hotel'.
- If the user asks to see the basket without making changes, just call view_basket and present it clearly.
""",
    tools=[
        get_or_create_basket,
        view_basket,
        get_latest_results,
        add_to_basket,
        remove_from_basket,
        modify_basket_item,
    ],
    model=BOOKING_AGENT.model,
)
