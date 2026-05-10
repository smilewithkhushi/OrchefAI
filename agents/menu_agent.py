import json
import time
from models.event_state import EventState, MenuItem, MenuData
from config import call_agent
from agents.prompts import MENU_PROMPT
from tools.search_tool import search_menus


async def run_menu(state: EventState) -> EventState:
    """Generate a menu plan using RAG search + LLM."""
    start = time.time()
    try:
        dietary = state.customer.dietary_requirements
        event_type = state.customer.event_type or "corporate_lunch"
        guest_count = state.customer.guest_count or 100
        budget = state.customer.budget_usd or 5000

        query = f"{event_type} {' '.join(dietary)} Singapore catering"
        rag_results = search_menus(query, dietary_tags=dietary if dietary else None, top=15)

        rag_context = json.dumps(rag_results, indent=2, default=str)
        customer_context = state.customer.model_dump_json()
        constraints = state.customer.special_requests or ""

        cuisine_prefs = ", ".join(state.customer.cuisine_preferences) if state.customer.cuisine_preferences else "No preference"
        service = state.customer.service_style or "No preference"
        courses = ", ".join(state.customer.meal_courses) if state.customer.meal_courses else "Full course"
        beverages = ", ".join(state.customer.beverage_options) if state.customer.beverage_options else "Standard"
        variety = state.customer.menu_variety or ("minimal" if guest_count <= 30 else "moderate" if guest_count <= 100 else "extensive")
        budget_range = ""
        if state.customer.budget_min_usd and state.customer.budget_max_usd:
            budget_range = f"Budget range: ${state.customer.budget_min_usd:.0f} – ${state.customer.budget_max_usd:.0f}"

        user_msg = f"""CUSTOMER DATA:
{customer_context}

PREFERENCES:
- Cuisine preferences: {cuisine_prefs}
- Service style: {service}
- Meal courses requested: {courses}
- Menu variety: {variety} (controls number of dishes per course)
- Beverages: {beverages}
- Alcohol service: {state.customer.alcohol_service}
- Indoor/Outdoor: {state.customer.indoor_outdoor or "Not specified"}
- Kitchen available at venue: {state.customer.venue_kitchen_available}
{budget_range}

AVAILABLE DISHES FROM KNOWLEDGE BASE:
{rag_context}

ADDITIONAL CONSTRAINTS: {constraints}

Generate a complete menu plan for this event."""

        raw = await call_agent(MENU_PROMPT, user_msg, "menu")
        data = _parse_json(raw)

        if data is None:
            retry_msg = f"Your previous response was not valid JSON. {user_msg}\nReturn ONLY the JSON object."
            raw = await call_agent(MENU_PROMPT, retry_msg, "menu")
            data = _parse_json(raw)

        if data is None:
            state.log("MenuAgent", "Failed to parse response", raw[:200] if raw else "No response", "error")
            return state

        items = []
        for item_data in data.get("menu_items", []):
            try:
                items.append(MenuItem(**item_data))
            except Exception:
                continue

        state.menu = MenuData(
            approved=False,
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            items=items,
            dietary_compliance=data.get("dietary_compliance", {}),
            total_food_cost_usd=data.get("total_food_cost_usd", 0.0),
            cost_per_head_usd=data.get("cost_per_head_usd", 0.0),
            notes=data.get("menu_notes", ""),
            warnings=data.get("warnings", []),
        )

        duration = int((time.time() - start) * 1000)
        summary = f"{len(items)} dishes selected, total food cost: ${state.menu.total_food_cost_usd:.2f}, per head: ${state.menu.cost_per_head_usd:.2f}"
        state.log("MenuAgent", "Generated menu plan via RAG", summary, duration_ms=duration)

    except Exception as e:
        state.log("MenuAgent", "Agent error", str(e)[:200], "error")

    return state


def _parse_json(raw: str) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None
