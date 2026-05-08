import json
import time
from models.event_state import EventState, PricingData, CostBreakdown
from config import call_agent, get_cost_profile
from agents.prompts import build_pricing_prompt


async def run_pricing(state: EventState) -> EventState:
    """Calculate full cost breakdown and check budget feasibility."""
    start = time.time()
    try:
        customer_data = state.customer.model_dump()
        inventory_data = state.inventory.model_dump()
        menu_data = {"items": [i.model_dump() for i in state.menu.items]}

        user_msg = f"""CUSTOMER DATA:
{json.dumps(customer_data, indent=2)}

INVENTORY DATA:
{json.dumps(inventory_data, indent=2)}

MENU DATA:
{json.dumps(menu_data, indent=2)}

Calculate the complete cost breakdown, check budget feasibility, and suggest pricing."""

        cost_profile = get_cost_profile(state.customer.venue)
        pricing_prompt = build_pricing_prompt(cost_profile)

        raw = await call_agent(pricing_prompt, user_msg, "pricing")
        data = _parse_json(raw)

        if data is None:
            retry_msg = f"Your previous response was not valid JSON. {user_msg}\nReturn ONLY the JSON object."
            raw = await call_agent(pricing_prompt, retry_msg, "pricing")
            data = _parse_json(raw)

        if data is None:
            state.log("PricingAgent", "Failed to parse response", raw[:200] if raw else "No response", "error")
            return state

        breakdown_data = data.get("cost_breakdown", {})
        cost_breakdown = CostBreakdown(
            ingredient_cost_usd=breakdown_data.get("ingredient_cost_usd", state.inventory.total_ingredient_cost_usd),
            labor_cost_usd=breakdown_data.get("labor_cost_usd", 0.0),
            logistics_cost_usd=breakdown_data.get("logistics_cost_usd", 0.0),
            packaging_cost_usd=breakdown_data.get("packaging_cost_usd", 0.0),
            overhead_usd=breakdown_data.get("overhead_usd", 0.0),
            total_cost_usd=breakdown_data.get("total_cost_usd", 0.0),
        )

        state.pricing = PricingData(
            calculated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            cost_breakdown=cost_breakdown,
            per_head_cost_usd=data.get("per_head_cost_usd", 0.0),
            food_cost_percentage=data.get("food_cost_percentage", 0.0),
            suggested_price_usd=data.get("suggested_price_usd", 0.0),
            suggested_price_per_head_usd=data.get("suggested_price_per_head_usd", 0.0),
            margin_percentage=data.get("margin_percentage", 0.0),
            budget_feasible=data.get("budget_feasible", False),
            budget_shortfall_usd=data.get("budget_shortfall_usd", 0.0),
            optimization_suggestions=data.get("optimization_suggestions", []),
            notes=data.get("pricing_notes", ""),
        )

        duration = int((time.time() - start) * 1000)
        feasible = "FEASIBLE" if state.pricing.budget_feasible else f"SHORTFALL ${state.pricing.budget_shortfall_usd:.2f}"
        summary = f"Total: ${cost_breakdown.total_cost_usd:.2f}, per head: ${state.pricing.per_head_cost_usd:.2f}, margin: {state.pricing.margin_percentage:.1f}%, budget: {feasible}"
        state.log("PricingAgent", "Calculated costs and pricing", summary, duration_ms=duration)

    except Exception as e:
        state.log("PricingAgent", "Agent error", str(e)[:200], "error")

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
