import streamlit as st
import asyncio
from agents.orchestrator import run_pipeline
from models.event_state import EventState

st.set_page_config(page_title="OrchefAI", layout="wide", page_icon="🍽️")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

/* Global */
.block-container { padding-top: 2rem; max-width: 1200px; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }

/* Hero header */
.hero {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
}
.hero h1 {
    font-size: 2.8rem;
    background: linear-gradient(135deg, #C9A962 0%, #E8D5A3 50%, #C9A962 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: 1px;
}
.hero p {
    color: #9CA3AF;
    font-size: 1.05rem;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.5px;
}

/* Cards */
.card {
    background: #1C1714;
    border: 1px solid #2A231E;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
}
.card-header {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #C9A962;
    margin-bottom: 0.8rem;
}

/* Metric overrides */
[data-testid="stMetric"] {
    background: #1C1714;
    border: 1px solid #2A231E;
    border-radius: 10px;
    padding: 1rem;
}
[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #9CA3AF !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    color: #FAFAFA !important;
}

/* Agent log entries */
.log-entry {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid #1C1714;
    font-family: 'Inter', sans-serif;
}
.log-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 2px; }
.log-agent {
    font-weight: 600;
    color: #C9A962;
    font-size: 0.85rem;
}
.log-action { color: #D1D5DB; font-size: 0.85rem; }
.log-summary { color: #6B7280; font-size: 0.78rem; margin-top: 2px; }
.log-time {
    color: #4B5563;
    font-size: 0.72rem;
    font-family: 'SF Mono', 'Fira Code', monospace;
}

/* Pipeline steps */
.step-row {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.45rem 0;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
}
.step-done { color: #C9A962; }
.step-active { color: #60A5FA; }
.step-waiting { color: #374151; }
.step-icon { width: 20px; text-align: center; }

/* Risk badges */
.risk-critical, .risk-high {
    background: rgba(220, 38, 38, 0.15);
    border: 1px solid rgba(220, 38, 38, 0.3);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
}
.risk-medium {
    background: rgba(234, 179, 8, 0.1);
    border: 1px solid rgba(234, 179, 8, 0.25);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
}
.risk-low {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.25);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
}
.risk-label {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.8rem;
    letter-spacing: 0.5px;
}
.risk-desc {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #D1D5DB;
    margin-top: 4px;
}
.risk-action {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    color: #6B7280;
    margin-top: 4px;
}

/* Shortage row */
.shortage-row {
    background: #1C1714;
    border: 1px solid #2A231E;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    font-family: 'Inter', sans-serif;
}

/* Menu table */
.menu-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
}
.menu-table th {
    background: #1C1714;
    color: #C9A962;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 1px;
    padding: 0.7rem 1rem;
    text-align: left;
    border-bottom: 2px solid #2A231E;
}
.menu-table td {
    padding: 0.6rem 1rem;
    border-bottom: 1px solid #1C1714;
    color: #D1D5DB;
}
.menu-table tr:hover td { background: rgba(201, 169, 98, 0.05); }
.dish-name { font-weight: 500; color: #FAFAFA; }
.tag {
    display: inline-block;
    background: rgba(201, 169, 98, 0.15);
    color: #C9A962;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 4px;
}

/* Quick-fill buttons */
.stButton > button[kind="secondary"] {
    border: 1px solid #2A231E !important;
    background: #1C1714 !important;
    color: #D1D5DB !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #C9A962 !important;
    color: #C9A962 !important;
}

/* Primary button */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #C9A962, #B8943D) !important;
    color: #0E1117 !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 2rem !important;
    letter-spacing: 0.5px;
}

/* Divider */
.section-divider {
    border: none;
    border-top: 1px solid #2A231E;
    margin: 1.5rem 0;
}

/* Hide default Streamlit elements */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="hero">
    <h1>OrchefAI</h1>
    <p>Multi-Agent Catering Operations System</p>
</div>
""", unsafe_allow_html=True)

# --- Session state ---
for key, default in [("state", None), ("running", False), ("agent_log", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- Layout ---
col_input, col_log = st.columns([3, 2], gap="large")

# ===== LEFT: Input + Results =====
with col_input:
    st.markdown('<div class="card-header">Event Request</div>', unsafe_allow_html=True)

    user_input = st.text_area(
        "Describe your catering requirement:",
        placeholder='e.g. "Plan a halal dinner for 200 guests this Saturday, budget $12,000"',
        height=110,
        label_visibility="collapsed",
    )

    st.markdown('<div style="margin-bottom: 0.5rem; color: #6B7280; font-size: 0.78rem; font-family: Inter, sans-serif;">QUICK FILL</div>', unsafe_allow_html=True)
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        if st.button("Halal Dinner  /  200 pax", type="secondary", use_container_width=True):
            st.session_state["prefill"] = "Halal dinner for 200 guests this Saturday, budget $12,000"
            st.rerun()
    with qc2:
        if st.button("Corporate Lunch  /  50 pax", type="secondary", use_container_width=True):
            st.session_state["prefill"] = "Corporate vegetarian lunch for 50 guests next Thursday at our office, budget $1,500"
            st.rerun()
    with qc3:
        if st.button("Gala Dinner  /  100 pax", type="secondary", use_container_width=True):
            st.session_state["prefill"] = "Premium gala dinner for 100 guests, budget $10,000"
            st.rerun()

    if "prefill" in st.session_state:
        user_input = st.session_state.pop("prefill")

    st.markdown("")
    if st.button("Plan This Event", type="primary", disabled=st.session_state["running"], use_container_width=True):
        if user_input and user_input.strip():
            st.session_state["running"] = True
            st.session_state["agent_log"] = []
            st.session_state["state"] = None

            def on_update(state: EventState):
                st.session_state["agent_log"] = [e.model_dump() for e in state.agent_log]

            with st.spinner("OrchefAI agents working..."):
                try:
                    loop = asyncio.new_event_loop()
                    state = loop.run_until_complete(run_pipeline(user_input, log_callback=on_update))
                    loop.close()
                    st.session_state["state"] = state
                except Exception as e:
                    st.error(f"Pipeline error: {e}")
                finally:
                    st.session_state["running"] = False
                    st.rerun()

# ===== RIGHT: Agent Log =====
with col_log:
    st.markdown('<div class="card-header">Agent Activity Log</div>', unsafe_allow_html=True)

    PIPELINE_STEPS = [
        ("1", "Intake Agent", "intake"),
        ("2", "Menu Agent", "menu"),
        ("3", "Inventory Agent", "inventory"),
        ("4", "Pricing Agent", "pricing"),
        ("5", "Monitoring Agent", "monitoring"),
    ]

    if st.session_state.get("state"):
        state: EventState = st.session_state["state"]
        completed_agents = {e.agent for e in state.agent_log}

        steps_html = ""
        for num, name, key in PIPELINE_STEPS:
            agent_name = name.replace(" Agent", "Agent")
            if agent_name in completed_agents:
                steps_html += f'<div class="step-row step-done"><span class="step-icon">&#10003;</span> Step {num}: {name}</div>'
            else:
                steps_html += f'<div class="step-row step-waiting"><span class="step-icon">&#9675;</span> Step {num}: {name}</div>'
        st.markdown(f'<div class="card">{steps_html}</div>', unsafe_allow_html=True)

        log_html = ""
        for entry in state.agent_log:
            if entry.status == "success":
                icon = "&#10003;"
                icon_color = "#C9A962"
            elif entry.status == "error":
                icon = "&#10007;"
                icon_color = "#DC2626"
            else:
                icon = "&#9888;"
                icon_color = "#EAB308"

            replan = entry.agent == "Orchestrator" and "Re-plan" in entry.action
            if replan:
                icon = "&#9889;"
                icon_color = "#60A5FA"

            time_str = f'<span class="log-time">{entry.duration_ms}ms</span>' if entry.duration_ms else ""
            summary = entry.output_summary[:160] if entry.output_summary else ""

            log_html += f"""
            <div class="log-entry">
                <span class="log-icon" style="color:{icon_color}">{icon}</span>
                <div>
                    <div><span class="log-agent">{entry.agent}</span> <span class="log-action">— {entry.action}</span> {time_str}</div>
                    <div class="log-summary">{summary}</div>
                </div>
            </div>"""

        st.markdown(f'<div class="card">{log_html}</div>', unsafe_allow_html=True)

    elif st.session_state["running"]:
        steps_html = ""
        for num, name, key in PIPELINE_STEPS:
            steps_html += f'<div class="step-row step-waiting"><span class="step-icon">&#9675;</span> Step {num}: {name}</div>'
        st.markdown(f'<div class="card">{steps_html}</div>', unsafe_allow_html=True)
        st.info("Agents are working...")
    else:
        st.markdown("""
        <div class="card" style="text-align:center; padding: 2rem; color: #4B5563;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">&#128269;</div>
            <div style="font-family: Inter, sans-serif; font-size: 0.9rem;">Submit a catering request to see the agents in action.</div>
        </div>
        """, unsafe_allow_html=True)


# ===== RESULTS SECTION =====
if st.session_state.get("state"):
    state: EventState = st.session_state["state"]

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    status_icon = "&#9679;"
    status_color = "#22C55E" if state.status == "complete" else "#EAB308"
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:1.2rem;">
        <span style="font-size:2rem; font-family:'Playfair Display',serif; color:#C9A962;">Final Catering Plan</span>
        <span style="color:{status_color}; font-size:0.9rem;">{status_icon} {state.status.upper()}</span>
    </div>
    """, unsafe_allow_html=True)

    # --- Overview metrics ---
    if state.customer.guest_count:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Guests", state.customer.guest_count)
        m2.metric("Event Type", (state.customer.event_type or "N/A").replace("_", " ").title())
        m3.metric("Budget", f"${state.customer.budget_usd:,.0f}" if state.customer.budget_usd else "N/A")
        m4.metric("Dietary", ", ".join(state.customer.dietary_requirements) or "None")

    # --- Menu ---
    if state.menu.items:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">Menu</div>', unsafe_allow_html=True)

        rows_html = ""
        for item in state.menu.items:
            tags = "".join(f'<span class="tag">{t}</span>' for t in item.dietary_tags)
            rows_html += f"""
            <tr>
                <td><span class="dish-name">{item.dish_name}</span></td>
                <td>{item.category.replace('_', ' ').title()}</td>
                <td style="text-align:center">{item.portions_required}</td>
                <td style="text-align:right">${item.cost_per_portion_usd:.2f}</td>
                <td>{tags}</td>
            </tr>"""

        st.markdown(f"""
        <table class="menu-table">
            <thead><tr>
                <th>Dish</th><th>Category</th><th style="text-align:center">Portions</th><th style="text-align:right">Cost/Portion</th><th>Dietary</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("")
        fc1, fc2 = st.columns(2)
        fc1.metric("Total Food Cost", f"${state.menu.total_food_cost_usd:,.2f}")
        fc2.metric("Cost Per Head", f"${state.menu.cost_per_head_usd:,.2f}")

    # --- Cost Breakdown ---
    if state.pricing.cost_breakdown.total_cost_usd > 0:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">Cost Breakdown</div>', unsafe_allow_html=True)

        cb = state.pricing.cost_breakdown
        bc1, bc2, bc3 = st.columns(3)
        bc1.metric("Ingredients", f"${cb.ingredient_cost_usd:,.2f}")
        bc1.metric("Labor", f"${cb.labor_cost_usd:,.2f}")
        bc2.metric("Logistics", f"${cb.logistics_cost_usd:,.2f}")
        bc2.metric("Packaging", f"${cb.packaging_cost_usd:,.2f}")
        bc3.metric("Overhead", f"${cb.overhead_usd:,.2f}")
        bc3.metric("Total", f"${cb.total_cost_usd:,.2f}")

        st.markdown("")
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("Suggested Price", f"${state.pricing.suggested_price_usd:,.2f}")
        pc2.metric("Margin", f"{state.pricing.margin_percentage:.1f}%")
        feasible = state.pricing.budget_feasible
        feasible_text = "Yes" if feasible else f"No (gap: ${state.pricing.budget_shortfall_usd:,.0f})"
        pc3.metric("Budget Feasible", feasible_text)

    # --- Risks ---
    if state.monitoring.risks:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">Risk Report</div>', unsafe_allow_html=True)

        for risk in state.monitoring.risks:
            sev = risk.severity.lower()
            css_class = f"risk-{sev}" if sev in ("critical", "high", "medium", "low") else "risk-low"
            st.markdown(f"""
            <div class="{css_class}">
                <div class="risk-label">{risk.severity}</div>
                <div class="risk-desc">{risk.description}</div>
                <div class="risk-action">Action: {risk.suggested_action}</div>
            </div>
            """, unsafe_allow_html=True)

        if state.monitoring.summary:
            st.markdown(f"""
            <div class="card" style="border-left: 3px solid #C9A962;">
                <div style="font-family:Inter,sans-serif; font-size:0.85rem; color:#D1D5DB;">{state.monitoring.summary}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- Shortages ---
    if state.inventory.shortages:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">Inventory Shortages</div>', unsafe_allow_html=True)

        for s in state.inventory.shortages:
            sev_color = "#DC2626" if s.severity == "HIGH" else "#EAB308" if s.severity == "MEDIUM" else "#22C55E"
            sub_text = f'<div style="color:#6B7280; font-size:0.78rem; margin-top:4px;">Substitute: {s.suggested_substitute}</div>' if s.suggested_substitute else ""
            st.markdown(f"""
            <div class="shortage-row">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:500; color:#FAFAFA;">{s.ingredient}</span>
                    <span style="color:{sev_color}; font-size:0.78rem; font-weight:600;">{s.severity}</span>
                </div>
                <div style="color:#9CA3AF; font-size:0.82rem; margin-top:4px;">
                    Need {s.required:.1f}kg &middot; Available {s.available:.1f}kg &middot; Deficit {s.deficit:.1f}kg
                </div>
                {sub_text}
            </div>
            """, unsafe_allow_html=True)

    # --- Footer ---
    st.markdown("""
    <hr class="section-divider">
    <div style="text-align:center; color:#374151; font-size:0.75rem; font-family:Inter,sans-serif; padding-bottom:1rem;">
        OrchefAI &mdash; Multi-Agent Catering Operations &mdash; CWB Hackathon 2026
    </div>
    """, unsafe_allow_html=True)
