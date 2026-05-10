import asyncio
import time
from typing import Callable, Optional
from models.event_state import EventState
from tools.cosmos_tool import save_event_state, load_event_state
from tools.history_db import save_completed_event
from agents.intake_agent import run_intake
from agents.menu_agent import run_menu
from agents.inventory_agent import run_inventory
from agents.pricing_agent import run_pricing
from agents.monitoring_agent import run_monitoring

MAX_REPLAN_ATTEMPTS = 1


REQUIRED_FIELDS = {
    "guest_count": "Guest count (e.g. 200 guests)",
    "budget_usd": "Budget (e.g. $12,000 or ₹4,00,000)",
    "event_type": "Event type (e.g. wedding, corporate lunch, gala dinner)",
    "event_date": "Event date (e.g. 15 June 2026)",
    "event_time": "Event time (e.g. 7:00 PM)",
    "venue": "Venue / location (e.g. Marina Bay Sands, Singapore)",
}

RECOMMENDED_FIELDS = {
    "dietary_requirements": "Dietary preferences (e.g. halal, vegetarian, vegan)",
}


def validate_intake(state: EventState) -> tuple[list[str], list[str]]:
    """Return (missing_required, missing_recommended) field descriptions."""
    missing_req = []
    for field, label in REQUIRED_FIELDS.items():
        val = getattr(state.customer, field, None)
        if val is None or val == 0:
            missing_req.append(label)

    missing_rec = []
    for field, label in RECOMMENDED_FIELDS.items():
        val = getattr(state.customer, field, None)
        if not val or (isinstance(val, list) and len(val) == 0):
            missing_rec.append(label)

    return missing_req, missing_rec


async def run_intake_only(
    user_input: str,
    log_callback: Optional[Callable[[EventState], None]] = None,
) -> EventState:
    """Run only the intake step and return state for validation."""
    state = EventState()
    state.status = "validating"
    state.customer.raw_input = user_input
    save_event_state(state)

    print(f"\n{'='*50}", flush=True)
    print("[OrchefAI] Intake Agent — parsing request", flush=True)
    print(f"{'='*50}", flush=True)

    state = await run_intake(user_input, state)
    _notify(log_callback, state)
    save_event_state(state)
    return state


async def run_pipeline_from_state(
    state: EventState,
    log_callback: Optional[Callable[[EventState], None]] = None,
) -> EventState:
    """Run pipeline steps 2-5 + recovery loop on an already-intake-validated state."""
    state.status = "in_progress"
    save_event_state(state)

    print(f"\n{'='*50}", flush=True)
    print("[OrchefAI] Pipeline continuing after validation", flush=True)
    print(f"{'='*50}", flush=True)

    # Step 2: Menu
    print("\n[OrchefAI] Step 2: Menu Agent", flush=True)
    state = await run_menu(state)
    _notify(log_callback, state)
    save_event_state(state)

    # Step 3: Inventory (needs menu items for ingredient calculation)
    print("\n[OrchefAI] Step 3: Inventory Agent", flush=True)
    state = await run_inventory(state)
    _notify(log_callback, state)
    save_event_state(state)

    # Step 4: Pricing
    print("\n[OrchefAI] Step 4: Pricing Agent", flush=True)
    state = await run_pricing(state)
    _notify(log_callback, state)
    save_event_state(state)

    # Step 5: Monitoring
    print("\n[OrchefAI] Step 5: Monitoring Agent", flush=True)
    state = await run_monitoring(state)
    _notify(log_callback, state)
    save_event_state(state)

    # Step 6: Recovery loop if HIGH/CRITICAL risk detected
    replan_count = 0
    while state.monitoring.re_plan_triggered and replan_count < MAX_REPLAN_ATTEMPTS:
        replan_count += 1
        constraints = state.monitoring.re_plan_constraints or ""
        state.log(
            "Orchestrator",
            f"Re-plan triggered (attempt {replan_count})",
            constraints,
        )
        _notify(log_callback, state)
        save_event_state(state)

        original = state.customer.special_requests or ""
        state.customer.special_requests = f"{original} CONSTRAINTS: {constraints}".strip()

        state.monitoring.re_plan_triggered = False

        state = await run_menu(state)
        _notify(log_callback, state)
        save_event_state(state)

        state = await run_inventory(state)
        _notify(log_callback, state)
        save_event_state(state)

        state = await run_pricing(state)
        _notify(log_callback, state)
        save_event_state(state)

        state = await run_monitoring(state)
        _notify(log_callback, state)
        save_event_state(state)

    state.status = "complete" if state.monitoring.final_approved else "needs_review"
    save_event_state(state)
    try:
        save_completed_event(state)
    except Exception as e:
        print(f"[OrchefAI] Warning: failed to save event history: {e}", flush=True)
    state.log("Orchestrator", "Pipeline complete", f"Status: {state.status}")
    _notify(log_callback, state)
    return state


async def run_pipeline(
    user_input: str,
    event_id: str = None,
    log_callback: Optional[Callable[[EventState], None]] = None,
) -> EventState:
    """Full pipeline: intake + validation + remaining steps. Used by non-UI callers."""
    state = await run_intake_only(user_input, log_callback)
    return await run_pipeline_from_state(state, log_callback)


def _notify(callback: Optional[Callable], state: EventState):
    if callback:
        try:
            callback(state)
        except Exception:
            pass
