import asyncio
import copy
import time
from typing import Callable, Optional
from models.event_state import EventState
from tools.cosmos_tool import save_event_state, load_event_state
from agents.intake_agent import run_intake
from agents.menu_agent import run_menu
from agents.inventory_agent import run_inventory
from agents.pricing_agent import run_pricing
from agents.monitoring_agent import run_monitoring

MAX_REPLAN_ATTEMPTS = 1


async def run_pipeline(
    user_input: str,
    event_id: str = None,
    log_callback: Optional[Callable[[EventState], None]] = None,
) -> EventState:
    """Run the full OrchefAI agent pipeline with recovery loop."""

    state = load_event_state(event_id) if event_id else EventState()
    state.status = "in_progress"
    state.customer.raw_input = user_input
    save_event_state(state)

    print(f"\n{'='*50}", flush=True)
    print("[OrchefAI] Pipeline started", flush=True)
    print(f"{'='*50}", flush=True)

    # Step 1: Intake
    print("\n[OrchefAI] Step 1/5: Intake Agent", flush=True)
    state = await run_intake(user_input, state)
    _notify(log_callback, state)
    save_event_state(state)

    # Step 2+3: Menu + Inventory in PARALLEL
    print("\n[OrchefAI] Step 2+3: Menu Agent ║ Inventory Agent (parallel)", flush=True)
    log_before = len(state.agent_log)
    menu_state = copy.deepcopy(state)
    inventory_state = copy.deepcopy(state)

    menu_state, inventory_state = await asyncio.gather(
        run_menu(menu_state),
        run_inventory(inventory_state),
    )

    state.menu = menu_state.menu
    state.inventory = inventory_state.inventory
    for entry in menu_state.agent_log[log_before:]:
        state.agent_log.append(entry)
    for entry in inventory_state.agent_log[log_before:]:
        state.agent_log.append(entry)
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
    state.log("Orchestrator", "Pipeline complete", f"Status: {state.status}")
    _notify(log_callback, state)
    return state


def _notify(callback: Optional[Callable], state: EventState):
    if callback:
        try:
            callback(state)
        except Exception:
            pass
