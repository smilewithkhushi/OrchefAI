import json
import time
from models.event_state import EventState, LogisticsData, LogisticsTask
from config import call_agent, calculate_staffing
from agents.prompts import LOGISTICS_PROMPT


async def run_logistics(state: EventState) -> EventState:
    """Plan preparation timeline, resource allocation, and delivery schedule."""
    start = time.time()
    try:
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

        procurement_summary = [
            {
                "ingredient": p.ingredient,
                "supplier": p.supplier_name,
                "lead_time_hours": p.lead_time_hours,
                "availability": p.availability,
            }
            for p in state.inventory.procurement_list
        ]

        menu_summary = [
            {"dish": i.dish_name, "category": i.category, "portions": i.portions_required}
            for i in state.menu.items
        ]

        user_msg = f"""EVENT DETAILS:
- Event type: {state.customer.event_type}
- Date: {state.customer.event_date}
- Service time: {state.customer.event_time} to {state.customer.event_end_time or 'not specified'}
- Venue: {state.customer.venue}
- Guest count: {state.customer.guest_count}

MENU ITEMS:
{json.dumps(menu_summary, indent=2)}

PROCUREMENT (supplier lead times):
{json.dumps(procurement_summary, indent=2)}

STAFFING:
- Total staff: {staffing['staff_count']}
- Breakdown: {json.dumps(staffing['breakdown'])}
- Event duration: {staffing['event_hours']} hours

Plan the complete preparation timeline, delivery schedule, and resource allocation."""

        raw = await call_agent(LOGISTICS_PROMPT, user_msg, "logistics")
        data = _parse_json(raw)

        if data is None:
            retry_msg = f"Your previous response was not valid JSON. {user_msg}\nReturn ONLY the JSON object."
            raw = await call_agent(LOGISTICS_PROMPT, retry_msg, "logistics")
            data = _parse_json(raw)

        if data is None:
            state.log("LogisticsAgent", "Failed to parse response", raw[:200] if raw else "No response", "error")
            return state

        tasks = []
        for t in data.get("preparation_timeline", []):
            try:
                tasks.append(LogisticsTask(**t))
            except Exception:
                continue

        state.logistics = LogisticsData(
            planned_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            preparation_timeline=tasks,
            delivery_schedule=data.get("delivery_schedule", []),
            resource_allocation=data.get("resource_allocation", {}),
            total_prep_hours=data.get("total_prep_hours", 0.0),
            notes=data.get("logistics_notes", ""),
        )

        duration_ms = int((time.time() - start) * 1000)
        summary = f"{len(tasks)} tasks planned, {state.logistics.total_prep_hours:.1f}h total prep, {len(state.logistics.delivery_schedule)} deliveries"
        state.log("LogisticsAgent", "Logistics plan complete", summary, duration_ms=duration_ms)

    except Exception as e:
        state.log("LogisticsAgent", "Agent error", str(e)[:200], "error")

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
