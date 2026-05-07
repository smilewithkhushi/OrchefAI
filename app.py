import streamlit as st
import asyncio
import copy
from agents.orchestrator import run_pipeline
from models.event_state import EventState

st.set_page_config(page_title="OrchefAI", layout="wide", page_icon="\U0001f37d️")

st.title("\U0001f37d️ OrchefAI")
st.caption("AI-Powered Multi-Agent Catering Operations System")

if "state" not in st.session_state:
    st.session_state["state"] = None
if "running" not in st.session_state:
    st.session_state["running"] = False
if "agent_log" not in st.session_state:
    st.session_state["agent_log"] = []

col_chat, col_log = st.columns([1, 1])

with col_chat:
    st.subheader("Event Request")
    user_input = st.text_area(
        "Describe your catering requirement:",
        placeholder='e.g. "Plan a halal dinner for 200 guests this Saturday, budget $12,000"',
        height=120,
    )

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Halal Dinner (200 guests)", type="secondary"):
            st.session_state["prefill"] = "Halal dinner for 200 guests this Saturday, budget $12,000"
            st.rerun()
    with col_btn2:
        if st.button("Corporate Lunch (50 guests)", type="secondary"):
            st.session_state["prefill"] = "Corporate vegetarian lunch for 50 guests next Thursday at our office, budget $1,500"
            st.rerun()
    with col_btn3:
        if st.button("Gala Dinner (100 guests)", type="secondary"):
            st.session_state["prefill"] = "Premium gala dinner for 100 guests, budget $10,000"
            st.rerun()

    if "prefill" in st.session_state:
        user_input = st.session_state.pop("prefill")

    if st.button("Plan This Event", type="primary", disabled=st.session_state["running"]):
        if user_input.strip():
            st.session_state["running"] = True
            st.session_state["agent_log"] = []
            st.session_state["state"] = None

            def on_update(state: EventState):
                st.session_state["agent_log"] = [
                    e.model_dump() for e in state.agent_log
                ]

            with st.spinner("OrchefAI agents working..."):
                try:
                    loop = asyncio.new_event_loop()
                    state = loop.run_until_complete(
                        run_pipeline(user_input, log_callback=on_update)
                    )
                    loop.close()
                    st.session_state["state"] = state
                except Exception as e:
                    st.error(f"Pipeline error: {e}")
                finally:
                    st.session_state["running"] = False
                    st.rerun()

with col_log:
    st.subheader("Agent Activity Log")
    if st.session_state.get("state"):
        state: EventState = st.session_state["state"]
        for entry in state.agent_log:
            if entry.status == "success":
                icon = "✅"
            elif entry.status == "error":
                icon = "❌"
            else:
                icon = "⚠️"

            if entry.agent == "Orchestrator" and "Re-plan" in entry.action:
                st.markdown(f"**⚡ {entry.action}**")
                st.caption(f"  {entry.output_summary}")
            else:
                st.markdown(f"{icon} **{entry.agent}** — {entry.action}")
                st.caption(f"  {entry.output_summary[:150]}")
                if entry.duration_ms:
                    st.caption(f"  ⏱ {entry.duration_ms}ms")
    elif st.session_state["running"]:
        st.info("Agents are working...")
    else:
        st.info("Submit a catering request to see agents in action.")


if st.session_state.get("state"):
    state: EventState = st.session_state["state"]
    st.divider()

    st.subheader("Final Catering Plan")

    status_color = "\U0001f7e2" if state.status == "complete" else "\U0001f7e1"
    st.markdown(f"**Status:** {status_color} {state.status.upper()}")

    if state.customer.guest_count:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Guests", state.customer.guest_count)
        c2.metric("Event", (state.customer.event_type or "N/A").replace("_", " ").title())
        c3.metric("Budget", f"${state.customer.budget_usd:,.2f}" if state.customer.budget_usd else "N/A")
        c4.metric("Dietary", ", ".join(state.customer.dietary_requirements) or "None")

    if state.menu.items:
        st.subheader("Menu")
        menu_rows = []
        for item in state.menu.items:
            menu_rows.append({
                "Dish": item.dish_name,
                "Category": item.category.replace("_", " ").title(),
                "Portions": item.portions_required,
                "Cost/Portion": f"${item.cost_per_portion_usd:.2f}",
                "Dietary Tags": ", ".join(item.dietary_tags),
            })
        st.table(menu_rows)

        mc1, mc2 = st.columns(2)
        mc1.metric("Total Food Cost", f"${state.menu.total_food_cost_usd:,.2f}")
        mc2.metric("Cost Per Head", f"${state.menu.cost_per_head_usd:,.2f}")

    if state.pricing.cost_breakdown.total_cost_usd > 0:
        st.subheader("Cost Breakdown")
        cb = state.pricing.cost_breakdown
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("Ingredients", f"${cb.ingredient_cost_usd:,.2f}")
        pc1.metric("Labor", f"${cb.labor_cost_usd:,.2f}")
        pc2.metric("Logistics", f"${cb.logistics_cost_usd:,.2f}")
        pc2.metric("Packaging", f"${cb.packaging_cost_usd:,.2f}")
        pc3.metric("Overhead", f"${cb.overhead_usd:,.2f}")
        pc3.metric("**Total Cost**", f"${cb.total_cost_usd:,.2f}")

        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Suggested Price", f"${state.pricing.suggested_price_usd:,.2f}")
        fc2.metric("Margin", f"{state.pricing.margin_percentage:.1f}%")
        feasible_text = "Yes" if state.pricing.budget_feasible else f"No (shortfall: ${state.pricing.budget_shortfall_usd:,.2f})"
        fc3.metric("Budget Feasible", feasible_text)

    if state.monitoring.risks:
        st.subheader("Risk Report")
        for risk in state.monitoring.risks:
            if risk.severity == "CRITICAL":
                badge = "\U0001f534"
            elif risk.severity == "HIGH":
                badge = "\U0001f534"
            elif risk.severity == "MEDIUM":
                badge = "\U0001f7e1"
            else:
                badge = "\U0001f7e2"
            st.markdown(f"{badge} **{risk.severity}** — {risk.description}")
            st.caption(f"  Suggested: {risk.suggested_action}")

        if state.monitoring.summary:
            st.info(state.monitoring.summary)

    if state.inventory.shortages:
        st.subheader("Inventory Shortages")
        for s in state.inventory.shortages:
            sev_badge = "\U0001f534" if s.severity == "HIGH" else "\U0001f7e1" if s.severity == "MEDIUM" else "\U0001f7e2"
            st.markdown(f"{sev_badge} **{s.ingredient}**: need {s.required:.1f}kg, have {s.available:.1f}kg (deficit: {s.deficit:.1f}kg)")
            if s.suggested_substitute:
                st.caption(f"  Suggested substitute: {s.suggested_substitute}")
