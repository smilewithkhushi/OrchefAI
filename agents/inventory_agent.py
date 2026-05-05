import json
import time
from models.event_state import EventState, InventoryData, Shortage, ProcurementItem
from config import call_agent
from agents.prompts import INVENTORY_PROMPT
from tools.search_tool import search_suppliers


async def run_inventory(state: EventState) -> EventState:
    """Check supplier stock and flag shortages. Runs in parallel with MenuAgent using customer data, or refines using menu data if available."""
    start = time.time()
    try:
        halal_required = "halal" in state.customer.dietary_requirements
        guest_count = state.customer.guest_count or 100
        event_type = state.customer.event_type or "corporate_lunch"

        all_suppliers = search_suppliers("", halal_required=False)
        supplier_context = json.dumps(all_suppliers, indent=2, default=str)

        if state.menu.items:
            menu_context = json.dumps([i.model_dump() for i in state.menu.items], indent=2)
            menu_section = f"MENU ITEMS (with portions required):\n{menu_context}"
        else:
            dietary = ", ".join(state.customer.dietary_requirements) or "none"
            menu_section = f"""NO FINALIZED MENU YET — estimate ingredient needs from:
EVENT TYPE: {event_type}
DIETARY REQUIREMENTS: {dietary}
SPECIAL REQUESTS: {state.customer.special_requests or 'none'}
Estimate typical ingredients and quantities for a {event_type} serving {guest_count} guests."""

        user_msg = f"""{menu_section}

AVAILABLE SUPPLIERS:
{supplier_context}

HALAL REQUIRED: {halal_required}
GUEST COUNT: {guest_count}

Calculate all ingredient requirements, check stock availability, and flag any shortages."""

        raw = await call_agent(INVENTORY_PROMPT, user_msg, "inventory")
        data = _parse_json(raw)

        if data is None:
            retry_msg = f"Your previous response was not valid JSON. {user_msg}\nReturn ONLY the JSON object."
            raw = await call_agent(INVENTORY_PROMPT, retry_msg, "inventory")
            data = _parse_json(raw)

        if data is None:
            state.log("InventoryAgent", "Failed to parse response", raw[:200] if raw else "No response", "error")
            return state

        shortages = []
        for s in data.get("shortages", []):
            try:
                shortages.append(Shortage(**s))
            except Exception:
                continue

        procurement = []
        for p in data.get("procurement_list", []):
            try:
                procurement.append(ProcurementItem(**p))
            except Exception:
                continue

        state.inventory = InventoryData(
            checked_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            required_ingredients=data.get("required_ingredients", {}),
            shortages=shortages,
            procurement_list=procurement,
            total_ingredient_cost_usd=data.get("total_ingredient_cost_usd", 0.0),
            notes=data.get("procurement_notes", ""),
        )

        duration = int((time.time() - start) * 1000)
        high_shortages = [s for s in shortages if s.severity == "HIGH"]
        summary = f"{len(procurement)} items sourced, {len(shortages)} shortages ({len(high_shortages)} HIGH), total: ${state.inventory.total_ingredient_cost_usd:.2f}"
        state.log("InventoryAgent", "Checked inventory and procurement", summary, duration_ms=duration)

    except Exception as e:
        state.log("InventoryAgent", "Agent error", str(e)[:200], "error")

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
