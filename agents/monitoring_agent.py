import json
import time
from models.event_state import EventState, MonitoringData, Risk
from config import call_agent
from agents.prompts import MONITORING_PROMPT


async def run_monitoring(state: EventState) -> EventState:
    """Audit the complete EventState for risks and trigger re-plan if needed."""
    start = time.time()
    try:
        audit_data = {
            "customer": {
                "guest_count": state.customer.guest_count,
                "budget_usd": state.customer.budget_usd,
                "dietary_requirements": state.customer.dietary_requirements,
                "event_type": state.customer.event_type,
                "event_date": state.customer.event_date,
                "event_time": state.customer.event_time,
                "venue": state.customer.venue,
            },
            "menu_items": [
                {
                    "dish_name": i.dish_name,
                    "category": i.category,
                    "portions_required": i.portions_required,
                    "cost_per_portion_usd": i.cost_per_portion_usd,
                    "dietary_tags": i.dietary_tags,
                }
                for i in state.menu.items
            ],
            "costs": state.pricing.cost_breakdown.model_dump() if state.pricing.cost_breakdown else {},
            "suggested_price_usd": state.pricing.suggested_price_usd,
            "margin_percentage": state.pricing.margin_percentage,
            "budget_feasible": state.pricing.budget_feasible,
            "shortages": [s.model_dump() if hasattr(s, "model_dump") else s for s in state.inventory.shortages],
            "total_ingredient_cost_usd": state.inventory.total_ingredient_cost_usd,
        }

        user_msg = f"""EVENT AUDIT DATA:
{json.dumps(audit_data, indent=2)}

Perform a full risk audit. Check budget, inventory shortages, dietary compliance, timeline, margins, and supplier reliability. Return your risk assessment."""

        raw = await call_agent(MONITORING_PROMPT, user_msg, "monitoring")
        data = _parse_json(raw)

        if data is None:
            retry_msg = f"Your previous response was not valid JSON. {user_msg}\nReturn ONLY the JSON object."
            raw = await call_agent(MONITORING_PROMPT, retry_msg, "monitoring")
            data = _parse_json(raw)

        if data is None:
            state.log("MonitoringAgent", "Failed to parse response", raw[:200] if raw else "No response", "error")
            return state

        risks = []
        for r in data.get("risks", []):
            try:
                risks.append(Risk(**r))
            except Exception:
                continue

        state.monitoring = MonitoringData(
            checked_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            overall_risk_level=data.get("overall_risk_level", "NONE"),
            risks=risks,
            re_plan_triggered=data.get("re_plan_triggered", False),
            re_plan_constraints=data.get("re_plan_constraints"),
            final_approved=data.get("final_approved", False),
            approval_notes=data.get("approval_notes", ""),
            summary=data.get("summary", ""),
        )

        duration = int((time.time() - start) * 1000)
        high_risks = [r for r in risks if r.severity in ("HIGH", "CRITICAL")]
        replan = " RE-PLAN TRIGGERED." if state.monitoring.re_plan_triggered else ""
        summary = f"Risk: {state.monitoring.overall_risk_level}, {len(risks)} issues ({len(high_risks)} high/critical).{replan}"
        state.log("MonitoringAgent", "Risk assessment complete", summary, duration_ms=duration)

    except Exception as e:
        state.log("MonitoringAgent", "Agent error", str(e)[:200], "error")

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
