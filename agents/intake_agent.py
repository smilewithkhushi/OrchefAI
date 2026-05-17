import json
import time
from models.event_state import EventState, CustomerData
from config import call_agent
from agents.prompts import INTAKE_PROMPT
from utils.currency import validate_budget


async def run_intake(user_input: str, state: EventState) -> EventState:
    """Parse natural language catering request into structured CustomerData."""
    start = time.time()
    try:
        raw = await call_agent(INTAKE_PROMPT, user_input, "intake")
        data = _parse_json(raw)

        if data is None:
            retry_msg = f"Your previous response was not valid JSON. Original request: {user_input}\nReturn ONLY the JSON object."
            raw = await call_agent(INTAKE_PROMPT, retry_msg, "intake")
            data = _parse_json(raw)

        if data is None:
            state.log("IntakeAgent", "Failed to parse response", raw[:200] if raw else "No response", "error")
            return state

        data.pop("missing_fields", None)
        data.pop("confidence", None)
        state.customer = CustomerData(**{k: v for k, v in data.items() if k in CustomerData.model_fields})
        state.customer.raw_input = user_input

        corrected = validate_budget(state.customer.budget_usd, user_input, state.customer.venue)
        if corrected is not None:
            state.customer.budget_usd = corrected

        duration = int((time.time() - start) * 1000)
        summary = f"{state.customer.guest_count or '?'} guests, {state.customer.event_type or '?'}, dietary: {state.customer.dietary_requirements}, budget: ${state.customer.budget_usd or '?'}"
        state.log("IntakeAgent", "Extracted event details from natural language input", summary, duration_ms=duration)

    except Exception as e:
        state.log("IntakeAgent", "Agent error", str(e)[:200], "error")

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
