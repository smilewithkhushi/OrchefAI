import streamlit as st
from streamlit.components.v1 import html as st_html
import asyncio
import textwrap
from tools.pdf_export import generate_pdf
from agents.orchestrator import run_pipeline, run_intake_only, run_pipeline_from_state, validate_intake
from models.event_state import (
    EventState, CustomerData, MenuData, MenuItem, InventoryData,
    ProcurementItem, Shortage, PricingData, CostBreakdown, MonitoringData,
    Risk, AgentLogEntry,
)

st.set_page_config(page_title="OrchefAI", layout="wide", page_icon="🍽️")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

.block-container { padding-top: 2rem; max-width: 1200px; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }

/* Hero */
.hero { text-align: center; padding: 1.5rem 0 1rem 0; }
.hero h1 {
    font-size: 2.8rem;
    background: linear-gradient(135deg, #C9A962 0%, #E8D5A3 50%, #C9A962 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: 1px;
}
.hero p { color: #9CA3AF; font-size: 1.05rem; font-family: 'Inter', sans-serif; letter-spacing: 0.5px; }

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

/* Metrics */
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

/* Horizontal stepper */
.stepper {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem 1rem;
}
.stepper-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 90px;
}
.stepper-circle {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    transition: all 0.3s;
}
.stepper-circle.done {
    background: linear-gradient(135deg, #C9A962, #B8943D);
    color: #0E1117;
    box-shadow: 0 0 12px rgba(201, 169, 98, 0.3);
}
.stepper-circle.active {
    background: rgba(96, 165, 250, 0.15);
    border: 2px solid #60A5FA;
    color: #60A5FA;
    animation: step-pulse 1.5s ease-in-out infinite;
}
.stepper-circle.waiting {
    background: #1C1714;
    border: 2px solid #2A231E;
    color: #4B5563;
}
@keyframes step-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(96, 165, 250, 0.4); }
    50% { box-shadow: 0 0 0 10px rgba(96, 165, 250, 0); }
}
.stepper-line {
    flex: 1;
    height: 3px;
    background: #2A231E;
    min-width: 30px;
    max-width: 80px;
    border-radius: 2px;
}
.stepper-line.done {
    background: linear-gradient(90deg, #C9A962, #B8943D);
}
.stepper-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    font-weight: 500;
    margin-top: 8px;
    letter-spacing: 0.3px;
}
.stepper-label.done { color: #C9A962; }
.stepper-label.active { color: #60A5FA; }
.stepper-label.waiting { color: #4B5563; }

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
.risk-label { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.8rem; letter-spacing: 0.5px; }
.risk-desc { font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #D1D5DB; margin-top: 4px; }
.risk-action { font-family: 'Inter', sans-serif; font-size: 0.78rem; color: #6B7280; margin-top: 4px; }

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

/* Buttons */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #C9A962, #B8943D) !important;
    color: #0E1117 !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 2rem !important;
    letter-spacing: 0.5px;
}
div.stButton > button[kind="secondary"] {
    border: 1px solid #2A231E !important;
    background: #1C1714 !important;
    color: #D1D5DB !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #C9A962 !important;
    color: #C9A962 !important;
}

/* Divider */
.section-divider {
    border: none;
    border-top: 1px solid #2A231E;
    margin: 1.5rem 0;
}

/* Hide defaults */
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
for key, default in [("state", None), ("running", False), ("agent_log", []),
                      ("intake_state", None), ("validation_errors", None),
                      ("validation_warnings", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- Quick-fill templates ---
QF_TEMPLATES = {
    "wedding": "Plan a halal wedding dinner for 200 guests at Marina Bay Sands, Singapore this Saturday at 7:00 PM. Budget is $15,000 USD. Dietary requirements: halal, nut-free.",
    "corporate": "Corporate vegetarian lunch for 50 guests at Raffles Place office, Singapore next Thursday at 12:00 PM. Budget $2,000 USD. Dietary requirements: vegetarian.",
    "gala": "Premium gala cocktail reception for 150 guests at The Fullerton Hotel, Singapore this Friday at 8:00 PM. Budget $12,000 USD. Mixed dietary: vegetarian and gluten-free options needed.",
}

# --- Pre-baked demo results (instant display, no API calls) ---
def _demo_log(agents):
    return [AgentLogEntry(timestamp="2026-05-08T12:00:00", agent=a, action="completed", output_summary="OK", status="success") for a in agents]

ALL_AGENTS_DONE = _demo_log(["IntakeAgent", "MenuAgent", "InventoryAgent", "PricingAgent", "MonitoringAgent"])

DEMO_STATES = {
    "wedding": EventState(
        event_id="DEMO-WEDDING",
        status="complete",
        customer=CustomerData(
            name="Demo Client",
            event_type="wedding",
            event_date="2026-05-15",
            event_time="19:00",
            guest_count=200,
            venue="Marina Bay Sands, Singapore",
            dietary_requirements=["halal", "nut-free"],
            budget_usd=15000.0,
            raw_input=QF_TEMPLATES["wedding"],
        ),
        menu=MenuData(
            approved=True,
            items=[
                MenuItem(dish_id="W1", dish_name="Chicken Satay Skewers", category="starter", portions_required=220, cost_per_portion_usd=2.50, dietary_tags=["halal", "nut-free"]),
                MenuItem(dish_id="W2", dish_name="Lamb Biryani", category="main", portions_required=220, cost_per_portion_usd=5.80, dietary_tags=["halal"]),
                MenuItem(dish_id="W3", dish_name="Grilled Barramundi", category="main", portions_required=220, cost_per_portion_usd=6.20, dietary_tags=["halal", "nut-free"]),
                MenuItem(dish_id="W4", dish_name="Steamed Jasmine Rice", category="accompaniment", portions_required=220, cost_per_portion_usd=0.80, dietary_tags=["halal", "nut-free"]),
                MenuItem(dish_id="W5", dish_name="Garden Salad", category="accompaniment", portions_required=220, cost_per_portion_usd=1.20, dietary_tags=["halal", "nut-free"]),
                MenuItem(dish_id="W6", dish_name="Pandan Chiffon Cake", category="dessert", portions_required=220, cost_per_portion_usd=2.80, dietary_tags=["halal", "nut-free"]),
                MenuItem(dish_id="W7", dish_name="Rose Bandung", category="beverage", portions_required=220, cost_per_portion_usd=1.00, dietary_tags=["halal", "nut-free"]),
            ],
            total_food_cost_usd=4466.0,
            cost_per_head_usd=22.33,
            dietary_compliance={"halal": True, "nut-free": True},
            notes="All items halal & nut-free. 10% buffer included.",
            warnings=[],
        ),
        inventory=InventoryData(
            procurement_list=[
                ProcurementItem(ingredient="Chicken Thigh (halal)", quantity_required=55.0, unit="kg", supplier_id="S1", supplier_name="Hai Sia Seafood", unit_price_usd=6.50, total_cost_usd=357.5, lead_time_hours=24, availability="confirmed"),
                ProcurementItem(ingredient="Lamb Shoulder (halal)", quantity_required=66.0, unit="kg", supplier_id="S2", supplier_name="Singapore Halal Meats", unit_price_usd=14.00, total_cost_usd=924.0, lead_time_hours=36, availability="confirmed"),
                ProcurementItem(ingredient="Barramundi Fillet", quantity_required=44.0, unit="kg", supplier_id="S3", supplier_name="Greendale Fish", unit_price_usd=18.00, total_cost_usd=792.0, lead_time_hours=12, availability="confirmed"),
                ProcurementItem(ingredient="Basmati Rice", quantity_required=35.0, unit="kg", supplier_id="S4", supplier_name="FairPrice Wholesale", unit_price_usd=2.20, total_cost_usd=77.0, lead_time_hours=6, availability="confirmed"),
                ProcurementItem(ingredient="Pandan Extract", quantity_required=5.0, unit="litre", supplier_id="S5", supplier_name="Bake King SG", unit_price_usd=8.00, total_cost_usd=40.0, lead_time_hours=12, availability="partial"),
            ],
            shortages=[],
            total_ingredient_cost_usd=2190.5,
        ),
        pricing=PricingData(
            cost_breakdown=CostBreakdown(
                ingredient_cost_usd=2190.5,
                labor_cost_usd=500.0,
                logistics_cost_usd=33.75,
                packaging_cost_usd=300.0,
                overhead_usd=302.4,
                total_cost_usd=3326.65,
            ),
            per_head_cost_usd=16.63,
            food_cost_percentage=32.5,
            suggested_price_usd=4158.0,
            suggested_price_per_head_usd=20.79,
            margin_percentage=20.0,
            budget_feasible=True,
            budget_shortfall_usd=0.0,
            optimization_suggestions=[],
            notes="Within budget with healthy margin.",
        ),
        monitoring=MonitoringData(
            overall_risk_level="LOW",
            risks=[
                Risk(risk_id="R1", severity="LOW", type="timeline", description="Pandan extract has partial availability — order early.", affected_component="inventory", suggested_action="Confirm with Bake King SG 48 hours before event."),
            ],
            final_approved=True,
            summary="Plan approved. All items halal-certified and nut-free. Budget is sufficient with 20% margin. One low-risk item to monitor.",
        ),
        agent_log=ALL_AGENTS_DONE,
    ),
    "corporate": EventState(
        event_id="DEMO-CORP",
        status="complete",
        customer=CustomerData(
            name="Demo Client",
            event_type="corporate_lunch",
            event_date="2026-05-12",
            event_time="12:00",
            guest_count=50,
            venue="Raffles Place Office, Singapore",
            dietary_requirements=["vegetarian"],
            budget_usd=2000.0,
            raw_input=QF_TEMPLATES["corporate"],
        ),
        menu=MenuData(
            approved=True,
            items=[
                MenuItem(dish_id="C1", dish_name="Caprese Bruschetta", category="starter", portions_required=55, cost_per_portion_usd=2.00, dietary_tags=["vegetarian"]),
                MenuItem(dish_id="C2", dish_name="Mushroom Risotto", category="main", portions_required=55, cost_per_portion_usd=4.50, dietary_tags=["vegetarian"]),
                MenuItem(dish_id="C3", dish_name="Paneer Tikka Wrap", category="main", portions_required=55, cost_per_portion_usd=3.80, dietary_tags=["vegetarian"]),
                MenuItem(dish_id="C4", dish_name="Seasonal Fruit Platter", category="dessert", portions_required=55, cost_per_portion_usd=2.50, dietary_tags=["vegetarian"]),
                MenuItem(dish_id="C5", dish_name="Iced Lemon Tea", category="beverage", portions_required=55, cost_per_portion_usd=0.80, dietary_tags=["vegetarian"]),
            ],
            total_food_cost_usd=748.0,
            cost_per_head_usd=14.96,
            dietary_compliance={"vegetarian": True},
            notes="All vegetarian. 10% buffer included.",
        ),
        inventory=InventoryData(
            procurement_list=[
                ProcurementItem(ingredient="Arborio Rice", quantity_required=8.0, unit="kg", supplier_id="S1", supplier_name="FairPrice Wholesale", unit_price_usd=4.50, total_cost_usd=36.0, lead_time_hours=6, availability="confirmed"),
                ProcurementItem(ingredient="Fresh Mozzarella", quantity_required=5.5, unit="kg", supplier_id="S2", supplier_name="The Cheese Shop SG", unit_price_usd=16.00, total_cost_usd=88.0, lead_time_hours=12, availability="confirmed"),
                ProcurementItem(ingredient="Paneer Block", quantity_required=7.0, unit="kg", supplier_id="S3", supplier_name="Little India Grocers", unit_price_usd=8.00, total_cost_usd=56.0, lead_time_hours=6, availability="confirmed"),
                ProcurementItem(ingredient="Mixed Mushrooms", quantity_required=6.0, unit="kg", supplier_id="S4", supplier_name="Kin Yan Agrotech", unit_price_usd=12.00, total_cost_usd=72.0, lead_time_hours=12, availability="confirmed"),
            ],
            shortages=[],
            total_ingredient_cost_usd=252.0,
        ),
        pricing=PricingData(
            cost_breakdown=CostBreakdown(
                ingredient_cost_usd=252.0,
                labor_cost_usd=125.0,
                logistics_cost_usd=22.50,
                packaging_cost_usd=75.0,
                overhead_usd=47.45,
                total_cost_usd=521.95,
            ),
            per_head_cost_usd=10.44,
            food_cost_percentage=31.5,
            suggested_price_usd=652.0,
            suggested_price_per_head_usd=13.04,
            margin_percentage=20.0,
            budget_feasible=True,
            budget_shortfall_usd=0.0,
            notes="Well within budget. Good margins for a corporate lunch.",
        ),
        monitoring=MonitoringData(
            overall_risk_level="NONE",
            risks=[],
            final_approved=True,
            summary="Plan approved. All items vegetarian-compliant. Budget is comfortable with strong margins.",
        ),
        agent_log=ALL_AGENTS_DONE,
    ),
    "gala": EventState(
        event_id="DEMO-GALA",
        status="needs_review",
        customer=CustomerData(
            name="Demo Client",
            event_type="cocktail_reception",
            event_date="2026-05-10",
            event_time="20:00",
            guest_count=150,
            venue="The Fullerton Hotel, Singapore",
            dietary_requirements=["vegetarian", "gluten-free"],
            budget_usd=12000.0,
            raw_input=QF_TEMPLATES["gala"],
        ),
        menu=MenuData(
            approved=True,
            items=[
                MenuItem(dish_id="G1", dish_name="Truffle Arancini (GF)", category="starter", portions_required=165, cost_per_portion_usd=4.20, dietary_tags=["vegetarian", "gluten-free"]),
                MenuItem(dish_id="G2", dish_name="Smoked Salmon Blinis", category="starter", portions_required=165, cost_per_portion_usd=5.50, dietary_tags=["gluten-free"]),
                MenuItem(dish_id="G3", dish_name="Wild Mushroom Vol-au-Vent", category="main", portions_required=165, cost_per_portion_usd=6.80, dietary_tags=["vegetarian"]),
                MenuItem(dish_id="G4", dish_name="Seared Scallops", category="main", portions_required=165, cost_per_portion_usd=8.50, dietary_tags=["gluten-free"]),
                MenuItem(dish_id="G5", dish_name="Mini Pavlova", category="dessert", portions_required=165, cost_per_portion_usd=3.80, dietary_tags=["vegetarian", "gluten-free"]),
                MenuItem(dish_id="G6", dish_name="Sparkling Mocktail", category="beverage", portions_required=165, cost_per_portion_usd=2.50, dietary_tags=["vegetarian", "gluten-free"]),
            ],
            total_food_cost_usd=5164.5,
            cost_per_head_usd=34.43,
            dietary_compliance={"vegetarian": True, "gluten-free": True},
            notes="Premium cocktail menu. Mixed dietary sections.",
            warnings=["Vol-au-Vent contains gluten — serve in separate section from GF items."],
        ),
        inventory=InventoryData(
            procurement_list=[
                ProcurementItem(ingredient="Fresh Scallops", quantity_required=25.0, unit="kg", supplier_id="S1", supplier_name="Hai Sia Seafood", unit_price_usd=45.00, total_cost_usd=1125.0, lead_time_hours=12, availability="partial"),
                ProcurementItem(ingredient="Black Truffle Oil", quantity_required=3.0, unit="litre", supplier_id="S2", supplier_name="Culinary Imports SG", unit_price_usd=65.00, total_cost_usd=195.0, lead_time_hours=48, availability="confirmed"),
                ProcurementItem(ingredient="Smoked Salmon", quantity_required=18.0, unit="kg", supplier_id="S3", supplier_name="Nordic Seafood", unit_price_usd=28.00, total_cost_usd=504.0, lead_time_hours=24, availability="confirmed"),
                ProcurementItem(ingredient="Mixed Wild Mushrooms", quantity_required=12.0, unit="kg", supplier_id="S4", supplier_name="Kin Yan Agrotech", unit_price_usd=18.00, total_cost_usd=216.0, lead_time_hours=12, availability="confirmed"),
            ],
            shortages=[
                Shortage(ingredient="Fresh Scallops", required=25.0, available=18.0, deficit=7.0, severity="MEDIUM", suggested_substitute="King Prawns"),
            ],
            total_ingredient_cost_usd=2040.0,
        ),
        pricing=PricingData(
            cost_breakdown=CostBreakdown(
                ingredient_cost_usd=2040.0,
                labor_cost_usd=500.0,
                logistics_cost_usd=33.75,
                packaging_cost_usd=225.0,
                overhead_usd=279.9,
                total_cost_usd=3078.65,
            ),
            per_head_cost_usd=20.52,
            food_cost_percentage=34.1,
            suggested_price_usd=3848.0,
            suggested_price_per_head_usd=25.65,
            margin_percentage=20.0,
            budget_feasible=True,
            budget_shortfall_usd=0.0,
            optimization_suggestions=[
                {"suggestion": "Replace scallops with king prawns", "estimated_saving_usd": 380.0},
                {"suggestion": "Use domestic truffle oil instead of imported", "estimated_saving_usd": 120.0},
            ],
            notes="Within budget. Scallop shortage may require substitution.",
        ),
        monitoring=MonitoringData(
            overall_risk_level="MEDIUM",
            risks=[
                Risk(risk_id="R1", severity="MEDIUM", type="inventory", description="Fresh scallop supply short by 7kg — may need to substitute with king prawns.", affected_component="inventory", suggested_action="Confirm with Hai Sia Seafood or switch to king prawns for 40 portions."),
                Risk(risk_id="R2", severity="MEDIUM", type="dietary", description="Vol-au-Vent contains gluten — must be clearly separated from gluten-free section.", affected_component="menu", suggested_action="Use separate serving stations with clear GF labels."),
            ],
            final_approved=False,
            summary="Plan needs review. Scallop shortage and dietary separation require attention. Budget is comfortable.",
        ),
        agent_log=ALL_AGENTS_DONE,
    ),
}

# --- Query param handlers ---
if "voice_text" in st.query_params:
    st.session_state["event_input"] = st.query_params["voice_text"]
    st.query_params.clear()
    st.rerun()
if "qf_demo" in st.query_params:
    key = st.query_params["qf_demo"]
    if key in DEMO_STATES:
        st.session_state["event_input"] = QF_TEMPLATES[key]
        st.session_state["state"] = DEMO_STATES[key]
        st.session_state["running"] = False
        st.session_state["validation_errors"] = None
        st.session_state["validation_warnings"] = None
        st.session_state["intake_state"] = None
    st.query_params.clear()
    st.rerun()
if "qf" in st.query_params:
    key = st.query_params["qf"]
    if key in QF_TEMPLATES:
        st.session_state["event_input"] = QF_TEMPLATES[key]
    st.query_params.clear()
    st.rerun()

# --- Constants ---
PIPELINE_STEPS = [
    ("1", "Intake", "IntakeAgent"),
    ("2", "Menu", "MenuAgent"),
    ("3", "Inventory", "InventoryAgent"),
    ("4", "Pricing", "PricingAgent"),
    ("5", "Monitoring", "MonitoringAgent"),
]


# --- Render: horizontal progress stepper ---
def render_progress_bar(state, placeholder, running=False):
    completed_agents = {e.agent for e in state.agent_log}

    steps = []
    found_active = False
    for num, label, agent_key in PIPELINE_STEPS:
        if agent_key in completed_agents:
            steps.append(("done", label, num))
        elif running and not found_active:
            found_active = True
            steps.append(("active", label, num))
        else:
            steps.append(("waiting", label, num))

    html = '<div class="stepper">'
    for i, (status, label, num) in enumerate(steps):
        if i > 0:
            line_class = "stepper-line done" if steps[i - 1][0] == "done" else "stepper-line"
            html += f'<div class="{line_class}"></div>'
        content = "&#10003;" if status == "done" else num
        html += f"""<div class="stepper-step">
            <div class="stepper-circle {status}">{content}</div>
            <div class="stepper-label {status}">{label}</div>
        </div>"""
    html += "</div>"

    with placeholder.container():
        st.markdown(html, unsafe_allow_html=True)


# --- Render: results panel ---
def _html(content: str):
    st.markdown(textwrap.dedent(content), unsafe_allow_html=True)


def render_results_panel(state, placeholder):
    has_any = (
        state.customer.guest_count
        or state.menu.items
        or state.pricing.cost_breakdown.total_cost_usd > 0
        or state.monitoring.risks
        or state.inventory.shortages
    )
    if not has_any:
        return

    with placeholder.container():
        _html('<hr class="section-divider">')

        # --- Header with status ---
        status_map = {"complete": ("#22C55E", "APPROVED"), "needs_review": ("#EAB308", "NEEDS REVIEW")}
        status_color, status_label = status_map.get(state.status, ("#60A5FA", state.status.replace("_", " ").upper()))
        _html(f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1.5rem;">
            <span style="font-size:2rem; font-family:'Playfair Display',serif; color:#C9A962;">Catering Plan</span>
            <span style="background:{status_color}22; color:{status_color}; font-size:0.8rem; font-weight:600;
                         font-family:Inter,sans-serif; padding:6px 16px; border-radius:20px;
                         border:1px solid {status_color}44; letter-spacing:0.5px;">
                {status_label}
            </span>
        </div>
        """)

        # --- Event overview ---
        if state.customer.guest_count:
            venue = state.customer.venue or "Not specified"
            event_type = (state.customer.event_type or "N/A").replace("_", " ").title()
            date_str = state.customer.event_date or "TBD"
            time_str = state.customer.event_time or ""
            dietary = ", ".join(state.customer.dietary_requirements) or "None specified"
            _html(f"""
            <div class="card" style="border-left:3px solid #C9A962;">
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:1rem; font-family:Inter,sans-serif;">
                    <div>
                        <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#6B7280; margin-bottom:4px;">Event</div>
                        <div style="font-size:1rem; font-weight:600; color:#FAFAFA;">{event_type}</div>
                        <div style="font-size:0.82rem; color:#9CA3AF; margin-top:2px;">{date_str} {time_str}</div>
                    </div>
                    <div>
                        <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#6B7280; margin-bottom:4px;">Guests &amp; Venue</div>
                        <div style="font-size:1rem; font-weight:600; color:#FAFAFA;">{state.customer.guest_count} guests</div>
                        <div style="font-size:0.82rem; color:#9CA3AF; margin-top:2px;">{venue}</div>
                    </div>
                    <div>
                        <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#6B7280; margin-bottom:4px;">Dietary Needs</div>
                        <div style="font-size:0.9rem; font-weight:500; color:#FAFAFA;">{dietary}</div>
                    </div>
                </div>
            </div>
            """)

        # ==============================================================
        # SECTION 1: CHARGE THE CUSTOMER (most important for restaurant)
        # ==============================================================
        if state.pricing.cost_breakdown.total_cost_usd > 0:
            budget = state.customer.budget_usd or 0
            total_cost = state.pricing.cost_breakdown.total_cost_usd
            suggested_price = state.pricing.suggested_price_usd
            per_head = state.pricing.suggested_price_per_head_usd
            margin = state.pricing.margin_percentage
            profit = suggested_price - total_cost if suggested_price > 0 else 0
            feasible = state.pricing.budget_feasible
            shortfall = state.pricing.budget_shortfall_usd

            _html('<hr class="section-divider">')
            _html("""
            <div style="font-family:'Playfair Display',serif; font-size:1.4rem; color:#C9A962; margin-bottom:1rem;">
                What to Charge the Customer
            </div>
            """)

            # Big price cards
            _html(f"""
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:1rem; margin-bottom:1rem;">
                <div style="background:linear-gradient(135deg, rgba(201,169,98,0.15), rgba(201,169,98,0.05));
                            border:1px solid rgba(201,169,98,0.3); border-radius:12px; padding:1.2rem; text-align:center;">
                    <div style="font-family:Inter,sans-serif; font-size:0.72rem; text-transform:uppercase;
                                letter-spacing:1px; color:#C9A962; margin-bottom:6px;">Total Price to Charge</div>
                    <div style="font-family:'Playfair Display',serif; font-size:2.2rem; color:#FAFAFA; font-weight:700;">
                        ${suggested_price:,.0f}
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.78rem; color:#9CA3AF; margin-top:4px;">
                        Quote this amount to the customer
                    </div>
                </div>
                <div style="background:#1C1714; border:1px solid #2A231E; border-radius:12px; padding:1.2rem; text-align:center;">
                    <div style="font-family:Inter,sans-serif; font-size:0.72rem; text-transform:uppercase;
                                letter-spacing:1px; color:#6B7280; margin-bottom:6px;">Price Per Guest</div>
                    <div style="font-family:'Playfair Display',serif; font-size:2.2rem; color:#FAFAFA; font-weight:700;">
                        ${per_head:,.0f}
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.78rem; color:#9CA3AF; margin-top:4px;">
                        per person served
                    </div>
                </div>
                <div style="background:#1C1714; border:1px solid #2A231E; border-radius:12px; padding:1.2rem; text-align:center;">
                    <div style="font-family:Inter,sans-serif; font-size:0.72rem; text-transform:uppercase;
                                letter-spacing:1px; color:#6B7280; margin-bottom:6px;">Your Profit</div>
                    <div style="font-family:'Playfair Display',serif; font-size:2.2rem; color:#22C55E; font-weight:700;">
                        ${profit:,.0f}
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.78rem; color:#9CA3AF; margin-top:4px;">
                        {margin:.0f}% margin
                    </div>
                </div>
            </div>
            """)

            # Budget alert — what to tell the customer
            if not feasible and shortfall > 0:
                _html(f"""
                <div style="background:rgba(220,38,38,0.1); border:1px solid rgba(220,38,38,0.3);
                            border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1rem;">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:0.6rem;">
                        <span style="font-size:1.3rem;">&#9888;</span>
                        <span style="font-family:Inter,sans-serif; font-weight:700; font-size:0.95rem; color:#DC2626;">
                            Customer Budget is Not Enough
                        </span>
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.9rem; color:#D1D5DB; line-height:1.6;">
                        The customer said their budget is <strong>${budget:,.0f}</strong>,
                        but this event costs at least <strong>${total_cost:,.0f}</strong> to prepare.<br>
                        They need to add <strong style="color:#DC2626;">${shortfall:,.0f} more</strong> to cover costs.
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.85rem; color:#C9A962;
                                margin-top:0.8rem; padding:0.7rem; background:rgba(201,169,98,0.08);
                                border-radius:8px; border-left:3px solid #C9A962;">
                        <strong>Tell the customer:</strong> "For {state.customer.guest_count} guests with your requirements,
                        the minimum price is ${total_cost:,.0f}. We can adjust the menu to fit your budget,
                        or we recommend increasing the budget to ${suggested_price:,.0f} for the full experience."
                    </div>
                </div>
                """)

                if state.pricing.optimization_suggestions:
                    _html("""
                    <div style="font-family:Inter,sans-serif; font-weight:600; font-size:0.85rem; color:#EAB308;
                                margin-bottom:0.5rem;">Ways to Reduce Cost:</div>
                    """)
                    for sug in state.pricing.optimization_suggestions:
                        label = sug.get("suggestion", "")
                        saving = sug.get("estimated_saving_usd", 0)
                        _html(f"""
                        <div style="background:#1C1714; border:1px solid #2A231E; border-radius:8px;
                                    padding:0.6rem 1rem; margin-bottom:0.4rem; display:flex;
                                    justify-content:space-between; align-items:center; font-family:Inter,sans-serif;">
                            <span style="font-size:0.85rem; color:#D1D5DB;">{label}</span>
                            <span style="font-size:0.82rem; font-weight:600; color:#22C55E;">Save ${saving:,.0f}</span>
                        </div>
                        """)
            else:
                _html(f"""
                <div style="background:rgba(34,197,94,0.08); border:1px solid rgba(34,197,94,0.25);
                            border-radius:12px; padding:1rem 1.5rem; margin-bottom:1rem;
                            display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.3rem;">&#10003;</span>
                    <div style="font-family:Inter,sans-serif;">
                        <div style="font-weight:600; font-size:0.9rem; color:#22C55E;">Budget Looks Good</div>
                        <div style="font-size:0.82rem; color:#9CA3AF;">
                            Customer budget of <strong style="color:#FAFAFA;">${budget:,.0f}</strong>
                            covers this event. You make <strong style="color:#22C55E;">${profit:,.0f} profit</strong>.
                        </div>
                    </div>
                </div>
                """)

        # ==============================================================
        # SECTION 2: YOUR COSTS (what the restaurant actually spends)
        # ==============================================================
        if state.pricing.cost_breakdown.total_cost_usd > 0:
            _html('<hr class="section-divider">')
            _html("""
            <div style="font-family:'Playfair Display',serif; font-size:1.4rem; color:#C9A962; margin-bottom:1rem;">
                Your Costs
            </div>
            """)

            cb = state.pricing.cost_breakdown
            cost_items = [
                ("Food &amp; Ingredients", cb.ingredient_cost_usd, "#C9A962"),
                ("Staff / Labor", cb.labor_cost_usd, "#60A5FA"),
                ("Delivery &amp; Transport", cb.logistics_cost_usd, "#A78BFA"),
                ("Packaging &amp; Supplies", cb.packaging_cost_usd, "#F472B6"),
                ("Overhead (rent, utilities)", cb.overhead_usd, "#6B7280"),
            ]
            total = cb.total_cost_usd or 1

            bar_html = ""
            for label, amount, color in cost_items:
                pct = (amount / total * 100) if total > 0 else 0
                bar_html += f'<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px; font-family:Inter,sans-serif;"><div style="width:160px; font-size:0.82rem; color:#D1D5DB; flex-shrink:0;">{label}</div><div style="flex:1; background:#1C1714; border-radius:6px; height:24px; overflow:hidden;"><div style="width:{pct:.1f}%; height:100%; background:{color}; border-radius:6px; min-width:2px;"></div></div><div style="width:90px; text-align:right; font-size:0.85rem; font-weight:600; color:#FAFAFA; flex-shrink:0;">${amount:,.0f}</div></div>'

            _html(f"""
            <div class="card">
                {bar_html}
                <div style="display:flex; justify-content:space-between; align-items:center;
                            border-top:2px solid #2A231E; margin-top:12px; padding-top:12px;
                            font-family:Inter,sans-serif;">
                    <span style="font-size:0.9rem; font-weight:700; color:#C9A962; text-transform:uppercase;
                                 letter-spacing:0.5px;">Total Cost to You</span>
                    <span style="font-size:1.3rem; font-weight:700; color:#FAFAFA;">${total:,.0f}</span>
                </div>
            </div>
            """)

        # ==============================================================
        # SECTION 3: MENU — what to prepare
        # ==============================================================
        if state.menu.items:
            _html('<hr class="section-divider">')
            _html("""
            <div style="font-family:'Playfair Display',serif; font-size:1.4rem; color:#C9A962; margin-bottom:1rem;">
                Menu &mdash; What to Prepare
            </div>
            """)

            categories = {}
            for item in state.menu.items:
                cat = item.category.replace("_", " ").title()
                categories.setdefault(cat, []).append(item)

            for cat, items in categories.items():
                cat_html = f'<div style="font-family:Inter,sans-serif; font-weight:600; font-size:0.78rem; text-transform:uppercase; letter-spacing:1px; color:#6B7280; margin-bottom:8px; margin-top:16px;">{cat}</div>'
                for item in items:
                    tags = "".join(f'<span class="tag">{t}</span>' for t in item.dietary_tags)
                    total_cost = item.cost_per_portion_usd * item.portions_required
                    cat_html += f'<div style="background:#1C1714; border:1px solid #2A231E; border-radius:10px; padding:0.8rem 1rem; margin-bottom:6px; font-family:Inter,sans-serif;"><div style="display:flex; justify-content:space-between; align-items:center;"><div><span style="font-weight:600; color:#FAFAFA; font-size:0.9rem;">{item.dish_name}</span><span style="margin-left:8px;">{tags}</span></div><span style="font-weight:600; color:#C9A962; font-size:0.85rem;">${total_cost:,.0f}</span></div><div style="font-size:0.78rem; color:#6B7280; margin-top:4px;">{item.portions_required} portions &middot; ${item.cost_per_portion_usd:.2f} each</div></div>'
                _html(cat_html)

            if state.menu.warnings:
                for w in state.menu.warnings:
                    _html(f"""
                    <div style="background:rgba(234,179,8,0.08); border:1px solid rgba(234,179,8,0.2);
                                border-radius:8px; padding:0.6rem 1rem; margin-top:8px;
                                font-family:Inter,sans-serif; font-size:0.82rem; color:#EAB308;">
                        &#9888; {w}
                    </div>
                    """)

        # ==============================================================
        # SECTION 4: SHOPPING LIST (procurement)
        # ==============================================================
        if state.inventory.procurement_list:
            _html('<hr class="section-divider">')
            _html("""
            <div style="font-family:'Playfair Display',serif; font-size:1.4rem; color:#C9A962; margin-bottom:1rem;">
                Shopping List
            </div>
            """)

            rows_html = ""
            for p in state.inventory.procurement_list:
                avail_color = "#22C55E" if p.availability == "confirmed" else "#EAB308" if p.availability == "partial" else "#DC2626"
                avail_label = p.availability.title()
                rows_html += f'<tr><td style="font-weight:500; color:#FAFAFA;">{p.ingredient}</td><td>{p.quantity_required:.1f} {p.unit}</td><td>{p.supplier_name}</td><td style="text-align:right;">${p.total_cost_usd:,.0f}</td><td style="text-align:center;"><span style="color:{avail_color}; font-weight:600; font-size:0.78rem;">{avail_label}</span></td></tr>'

            _html(f"""
            <table class="menu-table">
                <thead><tr>
                    <th>Item</th><th>Quantity</th><th>Supplier</th>
                    <th style="text-align:right;">Cost</th><th style="text-align:center;">Status</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            """)

        # ==============================================================
        # SECTION 5: WARNINGS — things to watch out for
        # ==============================================================
        has_risks = state.monitoring.risks
        has_shortages = state.inventory.shortages
        if has_risks or has_shortages:
            _html('<hr class="section-divider">')
            _html("""
            <div style="font-family:'Playfair Display',serif; font-size:1.4rem; color:#C9A962; margin-bottom:1rem;">
                Things to Watch Out For
            </div>
            """)

            if has_risks:
                for risk in state.monitoring.risks:
                    sev = risk.severity.lower()
                    css_class = f"risk-{sev}" if sev in ("critical", "high", "medium", "low") else "risk-low"
                    icon = "&#9888;" if sev in ("critical", "high") else "&#9432;"
                    _html(f"""
                    <div class="{css_class}">
                        <div style="display:flex; align-items:center; gap:6px;">
                            <span style="font-size:1rem;">{icon}</span>
                            <span class="risk-label" style="color:inherit;">{risk.severity}</span>
                        </div>
                        <div class="risk-desc">{risk.description}</div>
                        <div class="risk-action"><strong>What to do:</strong> {risk.suggested_action}</div>
                    </div>
                    """)

            if has_shortages:
                _html("""
                <div style="font-family:Inter,sans-serif; font-weight:600; font-size:0.82rem;
                            color:#EAB308; margin-top:12px; margin-bottom:8px;">Ingredient Shortages</div>
                """)
                for s in state.inventory.shortages:
                    sev_color = "#DC2626" if s.severity == "HIGH" else "#EAB308" if s.severity == "MEDIUM" else "#22C55E"
                    sub_text = f' &mdash; <span style="color:#C9A962;">Use {s.suggested_substitute} instead</span>' if s.suggested_substitute else ""
                    _html(f"""
                    <div class="shortage-row">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:500; color:#FAFAFA;">{s.ingredient}</span>
                            <span style="color:{sev_color}; font-size:0.78rem; font-weight:600;">{s.severity}</span>
                        </div>
                        <div style="color:#9CA3AF; font-size:0.82rem; margin-top:4px;">
                            Need {s.required:.1f}kg but only {s.available:.1f}kg available (short by {s.deficit:.1f}kg){sub_text}
                        </div>
                    </div>
                    """)

        # --- Monitoring summary ---
        if state.monitoring.summary:
            _html(f"""
            <div class="card" style="border-left:3px solid #C9A962; margin-top:1rem;">
                <div style="font-family:Inter,sans-serif; font-size:0.72rem; text-transform:uppercase;
                            letter-spacing:1px; color:#6B7280; margin-bottom:6px;">AI Summary</div>
                <div style="font-family:Inter,sans-serif; font-size:0.85rem; color:#D1D5DB; line-height:1.5;">
                    {state.monitoring.summary}
                </div>
            </div>
            """)

        # --- Action buttons ---
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
        with btn_col1:
            pdf_bytes = generate_pdf(state)
            event_type = (state.customer.event_type or "event").replace("_", "-")
            filename = f"orchefai-{event_type}-{state.customer.guest_count or 0}guests.pdf"
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )
        with btn_col2:
            st.page_link("pages/1_Restaurant_Profile.py", label="Restaurant Profile", use_container_width=True)
        with btn_col3:
            st.page_link("pages/2_Event_History.py", label="Event History", use_container_width=True)

        _html("""
        <hr class="section-divider">
        <div style="text-align:center; color:#374151; font-size:0.75rem; font-family:Inter,sans-serif; padding-bottom:1rem;">
            OrchefAI &mdash; Multi-Agent Catering Operations &mdash; CWB Hackathon 2026
        </div>
        """)


# ============================================================
# LAYOUT
# ============================================================

st.markdown('<div class="card-header">Event Request</div>', unsafe_allow_html=True)

col_input, col_qf = st.columns([3, 2], gap="medium")

# --- Left: textarea + voice ---
with col_input:
    user_input = st.text_area(
        "Describe your catering requirement:",
        key="event_input",
        placeholder='e.g. "Plan a halal dinner for 200 guests this Saturday at Marina Bay Sands, 7 PM, budget $12,000"',
        height=140,
        label_visibility="collapsed",
    )

    VOICE_HTML = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: transparent; }
        .voice-row { display: flex; align-items: center; gap: 10px; font-family: 'Inter', sans-serif; }
        .mic-btn {
            width: 38px; height: 38px; border-radius: 50%;
            background: #1C1714; border: 1.5px solid #2A231E;
            color: #C9A962; font-size: 1.1rem;
            cursor: pointer; display: flex; align-items: center; justify-content: center;
            transition: all 0.2s;
        }
        .mic-btn:hover { border-color: #C9A962; }
        .mic-btn.recording {
            background: rgba(220, 38, 38, 0.15); border-color: #DC2626; color: #DC2626;
            animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.3); }
            50% { box-shadow: 0 0 0 8px rgba(220, 38, 38, 0); }
        }
        .voice-status { font-size: 0.78rem; color: #6B7280; letter-spacing: 0.3px; }
        .voice-status.active { color: #DC2626; font-weight: 500; }
        .voice-preview { font-size: 0.78rem; color: #9CA3AF; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .no-support { font-size: 0.78rem; color: #4B5563; }
    </style>
    <div class="voice-row" id="voiceRow">
        <button class="mic-btn" id="micBtn" onclick="toggleVoice()" title="Voice input">&#127908;</button>
        <span class="voice-status" id="status">Voice input</span>
        <span class="voice-preview" id="preview"></span>
    </div>
    <div class="no-support" id="noSupport" style="display:none;">Voice input requires Chrome or Edge.</div>
    <script>
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { document.getElementById('voiceRow').style.display='none'; document.getElementById('noSupport').style.display='block'; }
    else {
        const r = new SR(); r.lang='en-US'; r.interimResults=true; r.continuous=true; r.maxAlternatives=1;
        let rec=false, ft='', to=null;
        r.onresult = function(e) {
            let interim = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
                if (e.results[i].isFinal) ft += e.results[i][0].transcript + ' ';
                else interim += e.results[i][0].transcript;
            }
            document.getElementById('preview').textContent = ft + interim;
            clearTimeout(to);
            to = setTimeout(function() { stop(); }, 4000);
        };
        r.onend = function() { if (rec) stop(); };
        r.onerror = function(e) {
            if (e.error !== 'no-speech' && e.error !== 'aborted')
                document.getElementById('status').textContent = 'Error: ' + e.error;
            rec = false;
            document.getElementById('micBtn').classList.remove('recording');
        };
        window.toggleVoice = function() {
            if (rec) { stop(); }
            else {
                ft = '';
                document.getElementById('preview').textContent = '';
                document.getElementById('status').textContent = 'Listening...';
                document.getElementById('status').classList.add('active');
                document.getElementById('micBtn').classList.add('recording');
                rec = true; r.start();
                to = setTimeout(function() { stop(); }, 60000);
            }
        };
        function stop() {
            clearTimeout(to); rec = false; r.stop();
            document.getElementById('micBtn').classList.remove('recording');
            document.getElementById('status').classList.remove('active');
            const t = ft.trim();
            if (t) {
                document.getElementById('status').textContent = 'Filling in...';
                window.parent.location.href = window.parent.location.pathname + '?voice_text=' + encodeURIComponent(t);
            } else { document.getElementById('status').textContent = 'Voice input'; }
        }
    }
    </script>
    """
    st_html(VOICE_HTML, height=50)

# --- Right: quick-fill preset cards ---
with col_qf:
    st.markdown("""
    <style>
        .qf-label {
            font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.72rem;
            text-transform: uppercase; letter-spacing: 1px; color: #6B7280;
            margin-bottom: 8px;
        }
        .qf-card {
            background: #1C1714; border: 1px solid #2A231E; border-radius: 10px;
            padding: 10px 14px; margin-bottom: 8px; cursor: pointer;
            display: flex; align-items: center; gap: 10px; transition: all 0.2s;
            text-decoration: none;
        }
        .qf-card:hover { border-color: #C9A962; background: rgba(201,169,98,0.05); }
        .qf-icon { font-size: 1.4rem; flex-shrink: 0; }
        .qf-title { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.8rem; color: #FAFAFA; }
        .qf-detail { font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #6B7280; margin-top: 2px; }
        .qf-budget { font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #C9A962; font-weight: 600; margin-top: 1px; }
    </style>
    <div class="qf-label">Demo Presets (Instant)</div>
    <a class="qf-card" href="?qf_demo=wedding">
        <div class="qf-icon">🕌</div>
        <div>
            <div class="qf-title">Halal Wedding Dinner</div>
            <div class="qf-detail">200 guests · Marina Bay Sands · Sat 7 PM</div>
            <div class="qf-budget">$15,000</div>
        </div>
    </a>
    <a class="qf-card" href="?qf_demo=corporate">
        <div class="qf-icon">🏢</div>
        <div>
            <div class="qf-title">Corporate Lunch</div>
            <div class="qf-detail">50 guests · Raffles Place · Thu 12 PM</div>
            <div class="qf-budget">$2,000</div>
        </div>
    </a>
    <a class="qf-card" href="?qf_demo=gala">
        <div class="qf-icon">🍸</div>
        <div>
            <div class="qf-title">Gala Cocktail Reception</div>
            <div class="qf-detail">150 guests · Fullerton Hotel · Fri 8 PM</div>
            <div class="qf-budget">$12,000</div>
        </div>
    </a>
    """, unsafe_allow_html=True)

# --- Validation feedback ---
if st.session_state["validation_errors"]:
    st.markdown(f"""
    <div style="background: rgba(220, 38, 38, 0.1); border: 1px solid rgba(220, 38, 38, 0.3);
                border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;">
        <div style="font-family: Inter, sans-serif; font-weight: 600; font-size: 0.85rem;
                    color: #DC2626; margin-bottom: 0.5rem;">Missing Required Information</div>
        <div style="font-family: Inter, sans-serif; font-size: 0.82rem; color: #D1D5DB;">
            {"".join(f'<div style="padding: 2px 0;">&#8226; {f}</div>' for f in st.session_state["validation_errors"])}
        </div>
        <div style="font-family: Inter, sans-serif; font-size: 0.75rem; color: #6B7280; margin-top: 0.5rem;">
            Please update your request above and try again.
        </div>
    </div>
    """, unsafe_allow_html=True)

if st.session_state["validation_warnings"]:
    st.markdown(f"""
    <div style="background: rgba(234, 179, 8, 0.08); border: 1px solid rgba(234, 179, 8, 0.25);
                border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;">
        <div style="font-family: Inter, sans-serif; font-weight: 600; font-size: 0.85rem;
                    color: #EAB308; margin-bottom: 0.5rem;">Recommended (for better results)</div>
        <div style="font-family: Inter, sans-serif; font-size: 0.82rem; color: #D1D5DB;">
            {"".join(f'<div style="padding: 2px 0;">&#8226; {f}</div>' for f in st.session_state["validation_warnings"])}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Action buttons ---
can_proceed = st.session_state.get("intake_state") is not None and not st.session_state["validation_errors"]
btn_cols = st.columns([1, 1] if can_proceed else [1])

with btn_cols[0]:
    if st.button("Plan This Event", type="primary", disabled=st.session_state["running"], use_container_width=True):
        if user_input and user_input.strip():
            st.session_state["_action"] = "plan"
            st.session_state["_action_input"] = user_input

if can_proceed:
    with btn_cols[1]:
        if st.button("Continue Anyway", type="secondary", disabled=st.session_state["running"], use_container_width=True):
            st.session_state["_action"] = "continue"

# === Placeholders (progress bar + results, full-width below input) ===
progress_placeholder = st.empty()
results_placeholder = st.empty()


# ============================================================
# PIPELINE EXECUTION
# ============================================================
action = st.session_state.pop("_action", None)

if action == "plan":
    input_text = st.session_state.pop("_action_input", "")
    st.session_state["running"] = True
    st.session_state["state"] = None
    st.session_state["intake_state"] = None
    st.session_state["validation_errors"] = None
    st.session_state["validation_warnings"] = None

    def on_intake_update(s: EventState):
        render_progress_bar(s, progress_placeholder, running=True)

    try:
        loop = asyncio.new_event_loop()
        intake_state = loop.run_until_complete(run_intake_only(input_text, log_callback=on_intake_update))
        loop.close()

        missing_req, missing_rec = validate_intake(intake_state)

        if missing_req:
            st.session_state["intake_state"] = None
            st.session_state["validation_errors"] = missing_req
            st.session_state["validation_warnings"] = missing_rec if missing_rec else None
            st.session_state["running"] = False
            st.rerun()
        elif missing_rec:
            st.session_state["intake_state"] = intake_state
            st.session_state["validation_warnings"] = missing_rec
            st.session_state["running"] = False
            st.rerun()
        else:
            def on_pipeline_update(s: EventState):
                render_progress_bar(s, progress_placeholder, running=True)
                render_results_panel(s, results_placeholder)

            loop2 = asyncio.new_event_loop()
            state = loop2.run_until_complete(run_pipeline_from_state(intake_state, log_callback=on_pipeline_update))
            loop2.close()
            st.session_state["state"] = state
            st.session_state["intake_state"] = None
            st.session_state["running"] = False
            st.rerun()

    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.session_state["running"] = False

elif action == "continue":
    st.session_state["running"] = True

    def on_pipeline_update(s: EventState):
        render_progress_bar(s, progress_placeholder, running=True)
        render_results_panel(s, results_placeholder)

    try:
        loop = asyncio.new_event_loop()
        state = loop.run_until_complete(
            run_pipeline_from_state(st.session_state["intake_state"], log_callback=on_pipeline_update)
        )
        loop.close()
        st.session_state["state"] = state
    except Exception as e:
        st.error(f"Pipeline error: {e}")
    finally:
        st.session_state["intake_state"] = None
        st.session_state["validation_errors"] = None
        st.session_state["validation_warnings"] = None
        st.session_state["running"] = False
        st.rerun()

# ============================================================
# STATIC DISPLAY (after pipeline completes)
# ============================================================
elif st.session_state.get("state") and not st.session_state["running"]:
    render_progress_bar(st.session_state["state"], progress_placeholder)
    render_results_panel(st.session_state["state"], results_placeholder)
