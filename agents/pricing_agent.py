import json
import time
from models.event_state import EventState, PricingData, CostBreakdown
from config import call_agent, get_cost_profile, calculate_staffing
from agents.prompts import build_pricing_prompt


async def run_pricing(state: EventState) -> EventState:
    """Calculate full cost breakdown and check budget feasibility."""
    start = time.time()
    try:
        customer_data = state.customer.model_dump()
        inventory_data = state.inventory.model_dump()
        menu_data = {"items": [i.model_dump() for i in state.menu.items]}

        duration_hours = None
        if state.customer.event_time and state.customer.event_end_time:
            try:
                st_h, st_m = map(int, state.customer.event_time.split(":"))
                en_h, en_m = map(int, state.customer.event_end_time.split(":"))
                diff = (en_h * 60 + en_m) - (st_h * 60 + st_m)
                if diff <= 0:
                    diff += 24 * 60
                duration_hours = round(diff / 60, 1)
            except (ValueError, AttributeError):
                pass

        staffing = calculate_staffing(
            guest_count=state.customer.guest_count or 1,
            service_style=state.customer.service_style,
            event_type=state.customer.event_type,
            venue=state.customer.venue,
            event_duration_hours=duration_hours,
        )

        user_msg = f"""CUSTOMER DATA:
{json.dumps(customer_data, indent=2)}

INVENTORY DATA:
{json.dumps(inventory_data, indent=2)}

MENU DATA:
{json.dumps(menu_data, indent=2)}

PRE-CALCULATED LABOR COST:
- Total staff: {staffing['staff_count']} ({staffing['breakdown']['servers']} servers, {staffing['breakdown']['chefs']} chefs, {staffing['breakdown']['head_chef']} head chef, {staffing['breakdown']['supervisor']} supervisor, {staffing['breakdown']['dishwashers']} dishwashers)
- Event duration: {staffing['event_hours']} hours
- Hourly rate ({staffing['region']}): ${staffing['hourly_rate_usd']}/hr
- TOTAL LABOR COST: ${staffing['total_labor_cost_usd']} (USE THIS EXACT VALUE for labor_cost_usd)

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

        guest_count = state.customer.guest_count or 1
        ingredient_cost = state.inventory.total_ingredient_cost_usd or 0.0
        if ingredient_cost < 1.0 and state.menu.items:
            ingredient_cost = round(sum(
                i.cost_per_portion_usd * i.portions_required for i in state.menu.items
            ), 2)
        labor_cost = staffing["total_labor_cost_usd"]
        logistics_cost = round(cost_profile["logistics_cost_per_km_usd"] * cost_profile["default_distance_km"], 2)
        packaging_cost = round(cost_profile["packaging_cost_per_guest_usd"] * guest_count, 2)
        subtotal = ingredient_cost + labor_cost + logistics_cost + packaging_cost
        overhead = round(subtotal * cost_profile["overhead_percentage"], 2)
        total_cost = round(subtotal + overhead, 2)

        cost_breakdown = CostBreakdown(
            ingredient_cost_usd=ingredient_cost,
            labor_cost_usd=labor_cost,
            logistics_cost_usd=logistics_cost,
            packaging_cost_usd=packaging_cost,
            overhead_usd=overhead,
            total_cost_usd=total_cost,
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

        _validate_pricing_math(state)

        duration = int((time.time() - start) * 1000)
        feasible = "FEASIBLE" if state.pricing.budget_feasible else f"SHORTFALL ${state.pricing.budget_shortfall_usd:.2f}"
        summary = f"Total: ${cost_breakdown.total_cost_usd:.2f}, per head: ${state.pricing.per_head_cost_usd:.2f}, margin: {state.pricing.margin_percentage:.1f}%, budget: {feasible}"
        state.log("PricingAgent", "Calculated costs and pricing", summary, duration_ms=duration)

    except Exception as e:
        state.log("PricingAgent", "Agent error", str(e)[:200], "error")

    return state


def _validate_pricing_math(state: EventState):
    """Recalculate derived pricing fields — LLMs are unreliable at arithmetic."""
    cb = state.pricing.cost_breakdown
    recalc_total = (cb.ingredient_cost_usd + cb.labor_cost_usd +
                    cb.logistics_cost_usd + cb.packaging_cost_usd + cb.overhead_usd)
    if abs(recalc_total - cb.total_cost_usd) > 1.0:
        cb.total_cost_usd = round(recalc_total, 2)

    total_cost = cb.total_cost_usd
    guest_count = state.customer.guest_count or 1
    budget = state.customer.budget_usd or 0

    # Target 30% profit margin (configurable via restaurant profile in future)
    target_margin = 0.30
    ideal_price = round(total_cost / (1 - target_margin), 2)

    # Never quote above the customer's budget — if budget covers cost + some margin, fit within it
    if budget > 0 and budget >= total_cost:
        suggested = min(ideal_price, budget)
    elif ideal_price > 0:
        suggested = ideal_price
    else:
        suggested = state.pricing.suggested_price_usd

    state.pricing.suggested_price_usd = suggested

    if suggested > 0:
        state.pricing.margin_percentage = round(
            (suggested - total_cost) / suggested * 100, 1)
        state.pricing.food_cost_percentage = round(
            cb.ingredient_cost_usd / suggested * 100, 1)

    state.pricing.per_head_cost_usd = round(total_cost / guest_count, 2)
    state.pricing.suggested_price_per_head_usd = round(suggested / guest_count, 2)
    # Feasible = budget covers at minimum the total cost
    state.pricing.budget_feasible = budget >= total_cost
    state.pricing.budget_shortfall_usd = round(max(0, total_cost - budget), 2)


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
