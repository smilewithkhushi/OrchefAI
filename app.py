import streamlit as st
from audio_recorder_streamlit import audio_recorder
from utils.transcribe import transcribe_audio
from utils.audio_storage import save_audio
import asyncio
import textwrap
from html import escape as esc
from tools.pdf_export import generate_pdf
from agents.orchestrator import run_pipeline, run_intake_only, run_pipeline_from_state, validate_intake
from models.event_state import (
    EventState, CustomerData, MenuData, MenuItem, InventoryData,
    ProcurementItem, Shortage, PricingData, CostBreakdown, LogisticsData,
    LogisticsTask, MonitoringData, Risk, AgentLogEntry,
)

st.set_page_config(page_title="Home — OrchefAI", layout="wide", page_icon="🍽️")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

.block-container { padding-top: 1.5rem; max-width: 1200px; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }

/* Hero */
.hero { display: flex; align-items: center; gap: 1rem; padding: 1rem 0; }
.hero img { height: 80px; }
.hero .hero-text h1 {
    font-size: 2.2rem;
    background: linear-gradient(135deg, #C9A962 0%, #E8D5A3 50%, #C9A962 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: 1px;
    line-height: 1.1;
}
.hero .hero-text p { color: #6B7280; font-size: 0.82rem; font-family: 'Inter', sans-serif; letter-spacing: 0.5px; margin: 0; }

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

/* ── Results panel ── */
.results-section { margin-top: 1.5rem; margin-bottom: 1rem; }
.section-divider { border: none; border-top: 1px solid #2A231E; margin: 1.2rem 0; }
.section-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px; border-radius: 50%;
    background: rgba(201, 169, 98, 0.12); color: #C9A962;
    font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 700;
    margin-right: 10px; flex-shrink: 0;
}
.section-title {
    font-family: 'Playfair Display', serif; font-size: 1.25rem; color: #C9A962;
    display: flex; align-items: center;
}
.section-subtitle {
    font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #6B7280;
    margin-top: 2px; margin-left: 36px; margin-bottom: 1rem;
}

/* Risk badges */
.risk-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.risk-critical, .risk-high {
    background: rgba(220, 38, 38, 0.1);
    border: 1px solid rgba(220, 38, 38, 0.25);
    border-radius: 10px;
    padding: 0.7rem 1rem;
}
.risk-medium {
    background: rgba(234, 179, 8, 0.08);
    border: 1px solid rgba(234, 179, 8, 0.2);
    border-radius: 10px;
    padding: 0.7rem 1rem;
}
.risk-low {
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.2);
    border-radius: 10px;
    padding: 0.7rem 1rem;
}
.risk-label { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.72rem; letter-spacing: 0.5px; }
.risk-desc { font-family: 'Inter', sans-serif; font-size: 0.82rem; color: #D1D5DB; margin-top: 4px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.risk-action { font-family: 'Inter', sans-serif; font-size: 0.72rem; color: #9CA3AF; margin-top: 4px; }

/* Shortage row */
.shortage-row {
    background: #1C1714;
    border: 1px solid #2A231E;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 0.5rem;
    font-family: 'Inter', sans-serif;
}

/* Menu / procurement table */
.menu-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #2A231E;
}
.menu-table th {
    background: #1C1714;
    color: #C9A962;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 1px;
    padding: 0.8rem 1rem;
    text-align: left;
    border-bottom: 2px solid #2A231E;
}
.menu-table td {
    padding: 0.55rem 1rem;
    border-bottom: 1px solid rgba(42, 35, 30, 0.6);
    color: #D1D5DB;
}
.menu-table tr:nth-child(even) td { background: rgba(28, 23, 20, 0.4); }
.menu-table tr:hover td { background: rgba(201, 169, 98, 0.06); }
.dish-name { font-weight: 500; color: #FAFAFA; }
.tag {
    display: inline-block;
    background: rgba(201, 169, 98, 0.12);
    color: #C9A962;
    font-size: 0.68rem;
    padding: 2px 8px;
    border-radius: 20px;
    margin-right: 4px;
    letter-spacing: 0.3px;
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

/* Divider — defined in results panel section above */

/* Loader */
.loader-container {
    text-align: center;
    padding: 2.5rem 1.5rem;
    margin: 1.5rem 0;
    background: linear-gradient(135deg, #1C1714 0%, #0E1117 100%);
    border: 1px solid #2A231E;
    border-radius: 16px;
}
.loader-dots {
    display: inline-flex;
    gap: 6px;
    margin-bottom: 1rem;
}
.loader-dots span {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #C9A962;
    animation: loader-bounce 1.4s ease-in-out infinite;
}
.loader-dots span:nth-child(2) { animation-delay: 0.16s; }
.loader-dots span:nth-child(3) { animation-delay: 0.32s; }
@keyframes loader-bounce {
    0%, 80%, 100% { opacity: 0.25; transform: scale(0.8); }
    40% { opacity: 1; transform: scale(1.2); }
}
.loader-msg {
    font-family: 'Inter', sans-serif;
    font-size: 0.92rem;
    color: #FAFAFA;
    font-weight: 500;
    margin-bottom: 4px;
}
.loader-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    color: #6B7280;
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
    <img src="app/static/logo.png" alt="OrchefAI" />
    <div class="hero-text">
        <h1>OrchefAI</h1>
        <p>Multi-Agent Catering Operations System</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Session state ---
for key, default in [("state", None), ("running", False), ("agent_log", []),
                      ("intake_state", None), ("validation_errors", None),
                      ("validation_warnings", None), ("is_regeneration", False)]:
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

ALL_AGENTS_DONE = _demo_log(["IntakeAgent", "MenuAgent", "InventoryAgent", "PricingAgent", "LogisticsAgent", "MonitoringAgent"])

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
    ("5", "Logistics", "LogisticsAgent"),
    ("6", "Monitoring", "MonitoringAgent"),
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


# --- Render: loading indicator ---
LOADER_MESSAGES_NEW = [
    ("Crafting your catering plan...", "Our AI agents are working together to design the perfect event"),
    ("Planning the menu for your guests...", "Matching dishes to your dietary requirements and preferences"),
    ("Sourcing ingredients from suppliers...", "Checking availability and negotiating the best prices"),
    ("Calculating costs and pricing...", "Ensuring everything fits within your budget"),
    ("Running final quality checks...", "Almost there — verifying compliance and flagging any risks"),
]
LOADER_MESSAGES_REGEN = [
    ("Heard you — regenerating your plan...", "Incorporating your feedback into a fresh proposal"),
    ("Reworking the menu with your changes...", "Adjusting dishes based on your preferences"),
    ("Re-sourcing ingredients...", "Finding the best suppliers for the updated menu"),
    ("Recalculating the numbers...", "Making sure the new plan fits your budget"),
    ("Final review on the updated plan...", "Almost done — just a few more checks"),
]


def render_loader(placeholder, is_regen=False, step_index=0):
    messages = LOADER_MESSAGES_REGEN if is_regen else LOADER_MESSAGES_NEW
    idx = min(step_index, len(messages) - 1)
    msg, sub = messages[idx]
    with placeholder.container():
        st.markdown(f"""
        <div class="loader-container">
            <div class="loader-dots"><span></span><span></span><span></span></div>
            <div class="loader-msg">{msg}</div>
            <div class="loader-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)


# --- Render: results panel ---
def _html(content: str):
    lines = textwrap.dedent(content).splitlines()
    cleaned = "\n".join(ln.strip() for ln in lines if ln.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


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

        # ── Hero header: plan title + status badge ──
        status_map = {"complete": ("#22C55E", "APPROVED"), "needs_review": ("#EAB308", "NEEDS REVIEW")}
        status_color, status_label = status_map.get(state.status, ("#60A5FA", state.status.replace("_", " ").upper()))

        event_type = esc((state.customer.event_type or "N/A").replace("_", " ").title())
        date_str = esc(state.customer.event_date or "TBD")
        time_str = esc(state.customer.event_time or "")
        if state.customer.event_end_time:
            time_str = f"{time_str} – {esc(state.customer.event_end_time)}"
        venue = esc(state.customer.venue or "Not specified")
        dietary = ", ".join(esc(d.title()) for d in state.customer.dietary_requirements) if state.customer.dietary_requirements else "None specified"
        guest_count = state.customer.guest_count or 0

        _html(f"""
        <div style="margin-top:2rem; margin-bottom:0.8rem; padding:1.5rem 2rem;
                    background:linear-gradient(135deg, #1C1714 0%, #0E1117 100%);
                    border:1px solid #2A231E; border-radius:16px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1.2rem;">
                <div style="font-size:1.6rem; font-family:'Playfair Display',serif; color:#FAFAFA; font-weight:700;">
                    {event_type} &mdash; Catering Plan
                </div>
                <span style="background:{status_color}18; color:{status_color}; font-size:0.75rem; font-weight:700;
                             font-family:Inter,sans-serif; padding:5px 14px; border-radius:20px;
                             border:1px solid {status_color}33; letter-spacing:0.8px; text-transform:uppercase;">
                    {status_label}
                </span>
            </div>
            <div style="display:flex; gap:2rem; flex-wrap:wrap; font-family:Inter,sans-serif; font-size:0.82rem; color:#9CA3AF;">
                <span>{date_str} {time_str}</span>
                <span>&middot;</span>
                <span><strong style="color:#FAFAFA;">{guest_count}</strong> guests</span>
                <span>&middot;</span>
                <span>{venue}</span>
                <span>&middot;</span>
                <span>{dietary}</span>
            </div>
        </div>
        """)

        # ==============================================================
        # SECTION 1: PRICING — what to charge + budget status
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

            _html("""
            <div class="results-section">
                <div class="section-title"><span class="section-num">1</span>Pricing &amp; Budget</div>
                <div class="section-subtitle">What to quote the customer and your profit margins</div>
            </div>
            """)

            # Hero price card (larger) + two supporting cards
            _html(f"""
            <div style="display:grid; grid-template-columns:1.3fr 1fr 1fr; gap:0.8rem; margin-bottom:1rem;">
                <div style="background:linear-gradient(145deg, rgba(201,169,98,0.14), rgba(201,169,98,0.04));
                            border:1px solid rgba(201,169,98,0.25); border-radius:14px; padding:1.4rem 1.2rem; text-align:center;
                            position:relative; overflow:hidden;">
                    <div style="position:absolute; top:0; left:0; right:0; height:3px;
                                background:linear-gradient(90deg, #C9A962, #E8D5A3, #C9A962);"></div>
                    <div style="font-family:Inter,sans-serif; font-size:0.7rem; text-transform:uppercase;
                                letter-spacing:1.2px; color:#C9A962; margin-bottom:8px; font-weight:600;">Quote Price</div>
                    <div style="font-family:'Playfair Display',serif; font-size:2.5rem; color:#FAFAFA; font-weight:700;
                                line-height:1.1;">
                        ${suggested_price:,.0f}
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.75rem; color:#6B7280; margin-top:6px;">
                        ${per_head:,.0f} per guest
                    </div>
                </div>
                <div style="background:#1C1714; border:1px solid #2A231E; border-radius:14px; padding:1.2rem; text-align:center;
                            display:flex; flex-direction:column; justify-content:center;">
                    <div style="font-family:Inter,sans-serif; font-size:0.7rem; text-transform:uppercase;
                                letter-spacing:1px; color:#6B7280; margin-bottom:6px;">Your Cost</div>
                    <div style="font-family:'Playfair Display',serif; font-size:1.8rem; color:#FAFAFA; font-weight:700;">
                        ${total_cost:,.0f}
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.75rem; color:#6B7280; margin-top:4px;">
                        ${total_cost / max(guest_count, 1):,.0f} per guest
                    </div>
                </div>
                <div style="background:#1C1714; border:1px solid #2A231E; border-radius:14px; padding:1.2rem; text-align:center;
                            display:flex; flex-direction:column; justify-content:center;">
                    <div style="font-family:Inter,sans-serif; font-size:0.7rem; text-transform:uppercase;
                                letter-spacing:1px; color:#6B7280; margin-bottom:6px;">Net Profit</div>
                    <div style="font-family:'Playfair Display',serif; font-size:1.8rem; color:#22C55E; font-weight:700;">
                        ${profit:,.0f}
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.75rem; color:#22C55E; margin-top:4px;
                                font-weight:600;">
                        {margin:.0f}% margin
                    </div>
                </div>
            </div>
            """)

            # Budget status alert
            if not feasible and shortfall > 0:
                _html(f"""
                <div style="background:rgba(220,38,38,0.08); border:1px solid rgba(220,38,38,0.2);
                            border-radius:14px; padding:1.2rem 1.5rem; margin-bottom:1rem;">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:0.6rem;">
                        <span style="font-size:1.1rem; color:#DC2626;">&#9888;</span>
                        <span style="font-family:Inter,sans-serif; font-weight:700; font-size:0.88rem; color:#DC2626;">
                            Budget Shortfall
                        </span>
                        <span style="font-family:Inter,sans-serif; font-size:0.78rem; color:#9CA3AF; margin-left:auto;">
                            Client budget: ${budget:,.0f}
                        </span>
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.85rem; color:#D1D5DB; line-height:1.6;">
                        This event costs <strong>${total_cost:,.0f}</strong> to deliver.
                        The customer needs to increase their budget by
                        <strong style="color:#DC2626;">${shortfall:,.0f}</strong>.
                    </div>
                    <div style="font-family:Inter,sans-serif; font-size:0.82rem; color:#C9A962;
                                margin-top:0.8rem; padding:0.7rem 1rem; background:rgba(201,169,98,0.06);
                                border-radius:10px; border-left:3px solid #C9A962; line-height:1.5;">
                        <strong>Suggested response:</strong> &ldquo;For {guest_count} guests,
                        the minimum is ${total_cost:,.0f}. We recommend ${suggested_price:,.0f}
                        for the full experience, or we can adjust the menu to fit your budget.&rdquo;
                    </div>
                </div>
                """)

                if state.pricing.optimization_suggestions:
                    savings_html = ""
                    for sug in state.pricing.optimization_suggestions:
                        label = esc(sug.get("suggestion", ""))
                        saving = sug.get("estimated_saving_usd", 0)
                        savings_html += f"""
                        <div style="display:flex; justify-content:space-between; align-items:center;
                                    padding:0.6rem 1rem; border-bottom:1px solid rgba(42,35,30,0.5);">
                            <span style="font-size:0.82rem; color:#D1D5DB;">{label}</span>
                            <span style="font-size:0.78rem; font-weight:700; color:#22C55E; white-space:nowrap;
                                        background:rgba(34,197,94,0.08); padding:3px 10px; border-radius:20px;">
                                -${saving:,.0f}
                            </span>
                        </div>"""
                    _html(f"""
                    <div style="background:#1C1714; border:1px solid #2A231E; border-radius:12px;
                                overflow:hidden; margin-bottom:1rem;">
                        <div style="padding:0.7rem 1rem; font-family:Inter,sans-serif; font-weight:600;
                                    font-size:0.78rem; color:#EAB308; text-transform:uppercase; letter-spacing:0.8px;
                                    border-bottom:1px solid #2A231E;">
                            Cost Optimizations
                        </div>
                        {savings_html}
                    </div>
                    """)
            else:
                _html(f"""
                <div style="background:rgba(34,197,94,0.06); border:1px solid rgba(34,197,94,0.2);
                            border-radius:14px; padding:0.9rem 1.3rem; margin-bottom:1rem;
                            display:flex; align-items:center; gap:10px;">
                    <div style="width:32px; height:32px; border-radius:50%; background:rgba(34,197,94,0.12);
                                display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                        <span style="color:#22C55E; font-size:1rem;">&#10003;</span>
                    </div>
                    <div style="font-family:Inter,sans-serif;">
                        <div style="font-weight:600; font-size:0.85rem; color:#22C55E;">Within Budget</div>
                        <div style="font-size:0.78rem; color:#9CA3AF;">
                            Customer budget <strong style="color:#FAFAFA;">${budget:,.0f}</strong>
                            covers all costs. Profit: <strong style="color:#22C55E;">${profit:,.0f}</strong>.
                        </div>
                    </div>
                </div>
                """)

        # ==============================================================
        # SECTION 2: COST BREAKDOWN
        # ==============================================================
        if state.pricing.cost_breakdown.total_cost_usd > 0:
            _html("""
            <hr class="section-divider" />
            <div class="results-section">
                <div class="section-title"><span class="section-num">2</span>Cost Breakdown</div>
                <div class="section-subtitle">Where your money goes</div>
            </div>
            """)

            cb = state.pricing.cost_breakdown
            cost_items = [
                ("Food &amp; Ingredients", cb.ingredient_cost_usd, "#C9A962"),
                ("Staff &amp; Labor", cb.labor_cost_usd, "#60A5FA"),
                ("Delivery &amp; Transport", cb.logistics_cost_usd, "#A78BFA"),
                ("Packaging &amp; Supplies", cb.packaging_cost_usd, "#F472B6"),
                ("Overhead", cb.overhead_usd, "#6B7280"),
            ]
            total = cb.total_cost_usd or 1

            bar_html = ""
            for label, amount, color in cost_items:
                pct = (amount / total * 100) if total > 0 else 0
                pct_label = f'<span style="font-size:0.68rem; font-weight:600; color:#0E1117; padding-left:8px;">{pct:.0f}%</span>' if pct > 12 else ""
                pct_outside = f'<span style="font-size:0.68rem; font-weight:600; color:{color}; margin-left:6px; flex-shrink:0;">{pct:.0f}%</span>' if pct <= 12 else ""
                bar_html += f"""
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px; font-family:Inter,sans-serif;">
                    <div style="width:8px; height:8px; border-radius:50%; background:{color}; flex-shrink:0;"></div>
                    <div style="width:140px; font-size:0.82rem; color:#D1D5DB; flex-shrink:0;">{label}</div>
                    <div style="flex:1; background:rgba(42,35,30,0.5); border-radius:8px; height:26px; overflow:hidden;">
                        <div style="width:{max(pct, 1.5):.1f}%; height:100%; background:{color}; border-radius:8px;
                                    display:flex; align-items:center;">
                            {pct_label}
                        </div>
                    </div>
                    {pct_outside}
                    <div style="width:75px; text-align:right; font-size:0.82rem; font-weight:600; color:#FAFAFA;
                                flex-shrink:0;">${amount:,.0f}</div>
                </div>"""

            _html(f"""
            <div class="card" style="padding:1.4rem 1.5rem;">
                {bar_html}
                <div style="display:flex; justify-content:space-between; align-items:center;
                            border-top:2px solid #2A231E; margin-top:14px; padding-top:14px;
                            font-family:Inter,sans-serif;">
                    <span style="font-size:0.85rem; font-weight:700; color:#C9A962; text-transform:uppercase;
                                 letter-spacing:0.8px;">Total</span>
                    <span style="font-size:1.4rem; font-weight:700; color:#FAFAFA;
                                 font-family:'Playfair Display',serif;">${total:,.0f}</span>
                </div>
            </div>
            """)

        # ==============================================================
        # SECTION 3: MENU
        # ==============================================================
        if state.menu.items:
            total_menu_cost = sum(i.cost_per_portion_usd * i.portions_required for i in state.menu.items)
            _html(f"""
            <hr class="section-divider" />
            <div class="results-section">
                <div class="section-title"><span class="section-num">3</span>Menu</div>
                <div class="section-subtitle">{len(state.menu.items)} dishes &middot;
                    Total food cost: ${total_menu_cost:,.0f}</div>
            </div>
            """)

            categories = {}
            for item in state.menu.items:
                cat = item.category.replace("_", " ").title()
                categories.setdefault(cat, []).append(item)

            for cat, items in categories.items():
                cat_total = sum(i.cost_per_portion_usd * i.portions_required for i in items)
                rows_html = ""
                for item in items:
                    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in item.dietary_tags)
                    item_total = item.cost_per_portion_usd * item.portions_required
                    rows_html += f"""<tr>
                        <td style="font-weight:500; color:#FAFAFA;">{esc(item.dish_name)} {tags}</td>
                        <td style="text-align:center;">{item.portions_required}</td>
                        <td style="text-align:right;">${item.cost_per_portion_usd:.2f}</td>
                        <td style="text-align:right; font-weight:600; color:#C9A962;">${item_total:,.0f}</td>
                    </tr>"""
                _html(f"""
                <div style="font-family:Inter,sans-serif; font-weight:600; font-size:0.72rem;
                            text-transform:uppercase; letter-spacing:1.2px; color:#6B7280;
                            margin-top:12px; margin-bottom:6px; display:flex; justify-content:space-between;">
                    <span>{esc(cat)}</span><span style="color:#4B5563;">${cat_total:,.0f}</span>
                </div>
                <table class="menu-table">
                    <thead><tr>
                        <th>Dish</th><th style="text-align:center;">Portions</th>
                        <th style="text-align:right;">Unit</th><th style="text-align:right;">Total</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """)

            if state.menu.warnings:
                warnings_html = "".join(
                    f'<div style="display:flex; align-items:flex-start; gap:8px; padding:0.5rem 0; border-bottom:1px solid rgba(234,179,8,0.1);"><span style="flex-shrink:0;">&#9888;</span><span>{esc(w)}</span></div>'
                    for w in state.menu.warnings
                )
                _html(f"""
                <div style="background:rgba(234,179,8,0.06); border:1px solid rgba(234,179,8,0.18);
                            border-radius:10px; padding:0.6rem 1rem; margin-top:10px;
                            font-family:Inter,sans-serif; font-size:0.82rem; color:#EAB308;">
                    {warnings_html}
                </div>
                """)

        # ==============================================================
        # SECTION 4: PROCUREMENT
        # ==============================================================
        if state.inventory.procurement_list:
            total_procurement = sum(p.total_cost_usd for p in state.inventory.procurement_list)
            confirmed_count = sum(1 for p in state.inventory.procurement_list if p.availability == "confirmed")
            _html(f"""
            <hr class="section-divider" />
            <div class="results-section">
                <div class="section-title"><span class="section-num">4</span>Procurement</div>
                <div class="section-subtitle">{len(state.inventory.procurement_list)} items &middot;
                    {confirmed_count} confirmed &middot; ${total_procurement:,.0f} total</div>
            </div>
            """)

            rows_html = ""
            for i, p in enumerate(state.inventory.procurement_list):
                avail_colors = {"confirmed": "#22C55E", "partial": "#EAB308", "unavailable": "#DC2626"}
                avail_color = avail_colors.get(p.availability, "#6B7280")
                avail_icon = "&#10003;" if p.availability == "confirmed" else "&#9679;" if p.availability == "partial" else "&#10007;"
                rows_html += f"""<tr>
                    <td style="font-weight:500; color:#FAFAFA;">{esc(p.ingredient)}</td>
                    <td style="white-space:nowrap;">{p.quantity_required:.1f} {esc(p.unit)}</td>
                    <td style="color:#9CA3AF;">{esc(p.supplier_name)}</td>
                    <td style="text-align:right; font-weight:600;">${p.total_cost_usd:,.0f}</td>
                    <td style="text-align:center;">
                        <span style="color:{avail_color}; font-size:0.72rem; font-weight:600;">
                            {avail_icon} {esc(p.availability.title())}
                        </span>
                    </td>
                </tr>"""

            _html(f"""
            <table class="menu-table">
                <thead><tr>
                    <th>Ingredient</th><th>Qty</th><th>Supplier</th>
                    <th style="text-align:right;">Cost</th><th style="text-align:center;">Status</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            """)

        # ==============================================================
        # SECTION 5: LOGISTICS & TIMELINE
        # ==============================================================
        if state.logistics.preparation_timeline:
            _html(f"""
            <hr class="section-divider" />
            <div class="results-section">
                <div class="section-title"><span class="section-num">5</span>Logistics &amp; Timeline</div>
                <div class="section-subtitle">{len(state.logistics.preparation_timeline)} tasks &middot;
                    {state.logistics.total_prep_hours:.1f}h total prep &middot;
                    {len(state.logistics.delivery_schedule)} deliveries</div>
            </div>
            """)

            assigned_colors = {"kitchen_staff": "#F59E0B", "service_staff": "#3B82F6", "logistics": "#8B5CF6", "vendor": "#10B981"}
            timeline_html = ""
            for t in state.logistics.preparation_timeline:
                a_color = assigned_colors.get(t.assigned_to, "#6B7280")
                timeline_html += f"""<tr>
                    <td style="border-left:3px solid {a_color}; font-weight:500; color:#FAFAFA;">{esc(t.task)}</td>
                    <td style="white-space:nowrap;">{esc(t.start_time)} – {esc(t.end_time)}</td>
                    <td><span style="color:{a_color}; font-size:0.7rem; font-weight:600;
                               padding:2px 8px; background:{a_color}15; border-radius:12px;">
                        {esc(t.assigned_to.replace('_', ' ').title())}</span></td>
                    <td style="text-align:center;">{t.duration_hours:.1f}h</td>
                </tr>"""

            _html(f"""
            <table class="menu-table">
                <thead><tr>
                    <th>Task</th><th>Time</th><th>Team</th><th style="text-align:center;">Hrs</th>
                </tr></thead>
                <tbody>{timeline_html}</tbody>
            </table>
            """)

            if state.logistics.delivery_schedule:
                del_cards = ""
                for d in state.logistics.delivery_schedule:
                    v_type = d.get("vehicle_type", "van")
                    v_color = "#3B82F6" if v_type == "cold_van" else "#F59E0B"
                    v_icon = "&#10052;" if v_type == "cold_van" else "&#9898;"
                    del_cards += f"""
                    <div style="background:#1C1714; border:1px solid #2A231E; border-radius:10px;
                                padding:0.7rem 1rem; font-family:Inter,sans-serif;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:500; color:#FAFAFA; font-size:0.82rem;">{esc(str(d.get('item_type', '')))}</span>
                            <span style="color:{v_color}; font-size:0.68rem; font-weight:600;
                                        padding:2px 8px; background:{v_color}15; border-radius:12px;">
                                {v_icon} {esc(v_type.replace('_', ' ').title())}</span>
                        </div>
                        <div style="font-size:0.75rem; color:#9CA3AF;">
                            {esc(str(d.get('departure_time', '')))} &#8594; {esc(str(d.get('arrival_time', '')))}
                        </div>
                    </div>"""
                _html(f"""
                <div style="font-family:Inter,sans-serif; font-weight:600; font-size:0.72rem;
                            color:#C9A962; margin:14px 0 8px 0; text-transform:uppercase;
                            letter-spacing:0.8px;">Delivery Schedule</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;">
                    {del_cards}
                </div>
                """)

        # ==============================================================
        # SECTION 6: RISK ASSESSMENT
        # ==============================================================
        has_risks = state.monitoring.risks
        has_shortages = state.inventory.shortages
        if has_risks or has_shortages:
            risk_level = state.monitoring.overall_risk_level or "NONE"
            risk_colors = {"NONE": "#22C55E", "LOW": "#22C55E", "MEDIUM": "#EAB308", "HIGH": "#DC2626", "CRITICAL": "#DC2626"}
            rl_color = risk_colors.get(risk_level, "#6B7280")
            _html(f"""
            <hr class="section-divider" />
            <div class="results-section">
                <div class="section-title">
                    <span class="section-num">6</span>Risk Assessment
                    <span style="font-family:Inter,sans-serif; font-size:0.68rem; font-weight:700;
                                 color:{rl_color}; margin-left:12px; padding:3px 10px;
                                 background:{rl_color}15; border:1px solid {rl_color}30;
                                 border-radius:20px; letter-spacing:0.5px;">{esc(risk_level)}</span>
                </div>
                <div class="section-subtitle">Issues and warnings to review before confirming</div>
            </div>
            """)

            if has_risks:
                risk_cards = ""
                sev_colors = {"critical": "#DC2626", "high": "#DC2626", "medium": "#EAB308", "low": "#22C55E"}
                for risk in state.monitoring.risks:
                    sev = risk.severity.lower()
                    css_class = f"risk-{sev}" if sev in ("critical", "high", "medium", "low") else "risk-low"
                    dot_color = sev_colors.get(sev, "#6B7280")
                    risk_cards += f"""
                    <div class="{css_class}">
                        <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                            <span style="width:7px; height:7px; border-radius:50%; background:{dot_color};
                                        flex-shrink:0;"></span>
                            <span class="risk-label" style="color:{dot_color};">{esc(risk.severity)}</span>
                            <span style="font-family:Inter,sans-serif; font-size:0.68rem; color:#4B5563;
                                        margin-left:auto;">{esc(risk.type)}</span>
                        </div>
                        <div class="risk-desc">{esc(risk.description)}</div>
                        <div class="risk-action">{esc(risk.suggested_action)}</div>
                    </div>"""
                _html(f'<div class="risk-grid">{risk_cards}</div>')

            if has_shortages:
                shortage_rows = ""
                for s in state.inventory.shortages:
                    sev_color = "#DC2626" if s.severity == "HIGH" else "#EAB308" if s.severity == "MEDIUM" else "#22C55E"
                    deficit_pct = (s.deficit / s.required * 100) if s.required > 0 else 0
                    sub_text = f' &rarr; {esc(s.suggested_substitute)}' if s.suggested_substitute else ""
                    shortage_rows += f"""<tr>
                        <td style="font-weight:500; color:#FAFAFA;">{esc(s.ingredient)}</td>
                        <td style="text-align:right;">{s.required:.1f}kg</td>
                        <td style="text-align:right;">{s.available:.1f}kg</td>
                        <td style="text-align:right; color:{sev_color}; font-weight:600;">-{s.deficit:.1f}kg ({deficit_pct:.0f}%)</td>
                        <td style="text-align:center;"><span style="color:{sev_color}; font-size:0.7rem; font-weight:700;
                            padding:2px 8px; background:{sev_color}15; border-radius:12px;">{esc(s.severity)}</span>{sub_text}</td>
                    </tr>"""
                _html(f"""
                <div style="font-family:Inter,sans-serif; font-weight:600; font-size:0.72rem;
                            color:#EAB308; margin-top:12px; margin-bottom:6px; text-transform:uppercase;
                            letter-spacing:0.8px;">Ingredient Shortages</div>
                <table class="menu-table">
                    <thead><tr><th>Ingredient</th><th style="text-align:right;">Need</th>
                        <th style="text-align:right;">Have</th><th style="text-align:right;">Deficit</th>
                        <th style="text-align:center;">Status</th></tr></thead>
                    <tbody>{shortage_rows}</tbody>
                </table>
                """)

        # ── AI Summary ──
        if state.monitoring.summary:
            summary_paragraphs = "<br>".join(esc(p) for p in state.monitoring.summary.split("\n") if p.strip())
            _html(f"""
            <div style="background:#1C1714; border:1px solid #2A231E; border-radius:14px;
                        padding:1rem 1.5rem; margin-top:1.2rem;">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                    <div style="width:22px; height:22px; border-radius:6px; background:rgba(201,169,98,0.12);
                                display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                        <span style="font-size:0.65rem; color:#C9A962;">AI</span>
                    </div>
                    <span style="font-family:Inter,sans-serif; font-size:0.68rem; text-transform:uppercase;
                                 letter-spacing:1px; color:#6B7280; font-weight:600;">Summary</span>
                </div>
                <div style="font-family:Inter,sans-serif; font-size:0.82rem; color:#D1D5DB; line-height:1.5;
                            max-height:200px; overflow-y:auto;">
                    {summary_paragraphs}
                </div>
            </div>
            """)

        # ── Action buttons ──
        _html('<div style="margin-top:1.5rem;"></div>')
        pdf_bytes = generate_pdf(state)
        ev_type = (state.customer.event_type or "event").replace("_", "-")
        filename = f"orchefai-{ev_type}-{guest_count}guests.pdf"
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

        # ── Regenerate with feedback ──
        _html("""
        <div style="margin-top:1.5rem; padding:1.2rem 1.5rem; background:#1C1714;
                    border:1px solid #2A231E; border-radius:14px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:0.5rem;">
                <span style="font-size:0.9rem;">&#8634;</span>
                <span style="font-family:Inter,sans-serif; font-weight:600; font-size:0.85rem; color:#C9A962;">
                    Refine This Plan
                </span>
            </div>
            <p style="font-family:Inter,sans-serif; color:#6B7280; font-size:0.78rem; margin-bottom:0.6rem;">
                Describe changes — the AI will regenerate the entire proposal with your feedback.
            </p>
        </div>
        """)
        regen_feedback = st.text_area(
            "Your feedback",
            placeholder="e.g. Replace the lamb dishes with chicken, add a live pasta station, reduce overall cost by 15%...",
            key="regen_feedback",
            label_visibility="collapsed",
        )
        if st.button("Regenerate Plan", use_container_width=True, key="regen_btn"):
            if regen_feedback and regen_feedback.strip():
                existing = state.customer.special_requests or ""
                state.customer.special_requests = f"{existing}\nREVISION REQUEST: {regen_feedback.strip()}".strip()
                state.menu.items = []
                state.inventory = InventoryData()
                state.pricing = PricingData()
                state.monitoring = MonitoringData()
                state.status = "in_progress"
                st.session_state["_action"] = "plan_form"
                st.session_state["_action_customer"] = state.customer
                st.session_state["is_regeneration"] = True
                st.session_state["state"] = None
                st.rerun()
            else:
                st.warning("Please describe what you'd like changed before regenerating.")

        _html("""
        <div style="text-align:center; color:#2A231E; font-size:0.72rem; font-family:Inter,sans-serif;
                    padding:2rem 0 1rem 0; letter-spacing:0.5px;">
            OrchefAI &middot; Multi-Agent Catering Operations &middot; CWB Hackathon 2026
        </div>
        """)


# ============================================================
# LAYOUT
# ============================================================

header_col, toggle_col = st.columns([3, 1])
with header_col:
    st.markdown('<div class="card-header">New Catering Order</div>', unsafe_allow_html=True)
with toggle_col:
    free_text_mode = st.toggle("Free-text input", value=False, key="free_text_toggle")

# Demo presets (shown in both modes)
st.markdown("""
<style>
    .qf-row { display:flex; gap:10px; margin-bottom:1rem; flex-wrap:wrap; }
    .qf-chip { background:#1C1714; border:1px solid #2A231E; border-radius:8px; padding:6px 14px; font-family:Inter,sans-serif; font-size:0.75rem; color:#9CA3AF; text-decoration:none; display:inline-flex; align-items:center; gap:6px; transition:all 0.2s; white-space:nowrap; }
    .qf-chip:hover { border-color:#C9A962; color:#C9A962; }
    .qf-chip span { font-size:0.85rem; }
</style>
<div class="qf-row">
    <span style="font-family:Inter,sans-serif; font-size:0.72rem; color:#4B5563; align-self:center; margin-right:4px;">TRY DEMO:</span>
    <a class="qf-chip" href="?qf_demo=wedding"><span>🕌</span> Wedding · 200 pax · $15K</a>
    <a class="qf-chip" href="?qf_demo=corporate"><span>🏢</span> Corporate · 50 pax · $2K</a>
    <a class="qf-chip" href="?qf_demo=gala"><span>🍸</span> Gala · 150 pax · $12K</a>
</div>
""", unsafe_allow_html=True)

if free_text_mode:
    # --- Free-text fallback (old mode) ---
    user_input = st.text_area(
        "Describe the client's catering requirement:",
        key="event_input",
        placeholder='e.g. "Plan a halal dinner for 200 guests this Saturday at Marina Bay Sands, 7 PM, budget $12,000"',
        height=120,
        label_visibility="collapsed",
    )

    audio_bytes = audio_recorder(
        text="",
        recording_color="#DC2626",
        neutral_color="#C9A962",
        icon_size="1.2rem",
        pause_threshold=2.5,
        sample_rate=16000,
        key="voice_recorder",
    )

    if audio_bytes:
        with st.spinner("Transcribing..."):
            try:
                event_id = None
                state = st.session_state.get("state")
                if hasattr(state, "event_id"):
                    event_id = state.event_id
                save_audio(audio_bytes, event_id)

                transcript = transcribe_audio(audio_bytes)
                if transcript:
                    current = st.session_state.get("event_input", "")
                    if current.strip():
                        st.session_state["event_input"] = current.rstrip() + " " + transcript
                    else:
                        st.session_state["event_input"] = transcript
                    st.rerun()
                else:
                    st.toast("Could not detect speech. Please try again.")
            except Exception as e:
                st.error(f"Transcription failed: {e}")

else:
    # --- Structured Intake Form ---
    user_input = None

    from datetime import date, time as dt_time

    EVENT_TYPES = ["Wedding", "Corporate Lunch", "Birthday Party", "Cocktail Reception", "Conference", "Gala Dinner", "Baby Shower", "Engagement Party", "Anniversary", "Graduation Party", "Festival / Cultural", "Charity Event", "Product Launch", "Team Building", "Other"]
    EVENT_TYPE_MAP = {"Wedding": "wedding", "Corporate Lunch": "corporate_lunch", "Birthday Party": "birthday_party", "Cocktail Reception": "cocktail_reception", "Conference": "conference", "Gala Dinner": "gala_dinner", "Baby Shower": "baby_shower", "Engagement Party": "engagement_party", "Anniversary": "anniversary", "Graduation Party": "graduation_party", "Festival / Cultural": "festival_cultural", "Charity Event": "charity_event", "Product Launch": "product_launch", "Team Building": "team_building", "Other": "other"}
    DIETARY_OPTIONS = ["Non-Veg", "Vegetarian", "Vegan", "Halal", "Seafood", "Jain", "Gluten-Free", "Nut-Free", "Dairy-Free", "Egg-Free", "Diabetic-Friendly", "Keto", "Pescatarian", "Kosher"]
    CUISINE_OPTIONS = ["Asian", "Indian", "Mediterranean", "Western", "Middle Eastern", "Chinese", "Japanese", "Italian", "French", "Fusion"]
    SERVICE_STYLES = ["Buffet", "Plated Service", "Family Style", "Cocktail Pass-Around", "Food Stations"]
    SERVICE_STYLE_MAP = {"Buffet": "buffet", "Plated Service": "plated", "Family Style": "family_style", "Cocktail Pass-Around": "cocktail_pass", "Food Stations": "food_stations"}
    COURSE_OPTIONS = ["Starters / Canapes", "Soup", "Main Course", "Side Dishes", "Dessert", "Live Cooking Station"]
    BEVERAGE_OPTIONS = ["Non-Alcoholic", "Mocktails", "Wine", "Beer", "Full Bar", "Tea / Coffee Station"]

    with st.form("intake_form", clear_on_submit=False):
        # ── Section A: Core details (always visible) ──
        st.markdown('<p style="color:#C9A962; font-weight:600; font-size:0.85rem; margin-bottom:0.3rem;">ORDER DETAILS</p>', unsafe_allow_html=True)
        fa_col1, fa_col2 = st.columns(2)
        with fa_col1:
            form_event_type = st.selectbox("Event Type *", EVENT_TYPES, index=None, placeholder="Select event type...")
            form_date = st.date_input("Event Date *", value=None, min_value=date.today())
            form_venue = st.text_input("Venue / Delivery Location *", placeholder="e.g. Marina Bay Sands, Singapore")
        with fa_col2:
            form_guest_count = st.number_input("Expected Guests *", min_value=1, max_value=10000, value=None, step=10, placeholder="e.g. 200")
            ft_col1, ft_col2 = st.columns(2)
            with ft_col1:
                form_time = st.time_input("Service Start *", value=dt_time(19, 0))
            with ft_col2:
                form_end_time = st.time_input("Service End *", value=dt_time(23, 0))
            fb_col1, fb_col2 = st.columns(2)
            with fb_col1:
                form_budget_min = st.number_input("Min Budget ($)", min_value=0, value=None, step=500, placeholder="e.g. 5000")
            with fb_col2:
                form_budget_max = st.number_input("Max Budget ($) *", min_value=0, value=None, step=500, placeholder="e.g. 15000")
        form_event_type_custom = ""
        if form_event_type == "Other":
            form_event_type_custom = st.text_input("Specify event type", placeholder="e.g. Housewarming, Farewell Party...")

        # ── Section B: Menu preferences (collapsed by default) ──
        st.markdown('<p style="color:#C9A962; font-weight:600; font-size:0.85rem; margin-top:1.2rem; margin-bottom:0.3rem;">MENU PREFERENCES</p><p style="color:#6B7280; font-size:0.75rem; font-family:Inter,sans-serif; margin-bottom:0.5rem;">Optional — helps the AI plan a better menu</p>', unsafe_allow_html=True)
        fm_col1, fm_col2 = st.columns(2)
        with fm_col1:
            form_dietary = st.multiselect("Dietary Requirements", DIETARY_OPTIONS, placeholder="e.g. Halal, Vegetarian...")
            form_cuisines = st.multiselect("Cuisine Type", CUISINE_OPTIONS, placeholder="e.g. Indian, Italian...")
        with fm_col2:
            form_service_style = st.selectbox("Service Format", SERVICE_STYLES, index=None, placeholder="e.g. Buffet, Plated...")
            form_courses = st.multiselect("Courses to Serve", COURSE_OPTIONS, placeholder="e.g. Starters, Main, Dessert...")
        fm2_col1, fm2_col2 = st.columns(2)
        with fm2_col1:
            form_variety = st.selectbox("Menu Variety", ["Minimal (2-3 items)", "Moderate (4-6 items)", "Extensive (7+ items)"], index=1, help="How many dishes per course?")
        with fm2_col2:
            form_beverages = st.multiselect("Beverage Service", BEVERAGE_OPTIONS, placeholder="e.g. Mocktails, Tea/Coffee...")

        # ── Section C: Venue, client & notes (compact row) ──
        st.markdown('<p style="color:#C9A962; font-weight:600; font-size:0.85rem; margin-top:1.2rem; margin-bottom:0.3rem;">ADDITIONAL DETAILS</p>', unsafe_allow_html=True)
        fc_col1, fc_col2, fc_col3 = st.columns(3)
        with fc_col1:
            form_indoor_outdoor = st.radio("Venue Setting", ["Indoor", "Outdoor", "Both"], horizontal=True)
            form_kitchen = st.checkbox("On-site kitchen available", value=True)
        with fc_col2:
            form_name = st.text_input("Client Name / Company", placeholder="e.g. Acme Corp")
        with fc_col3:
            form_contact = st.text_input("Client Contact", placeholder="e.g. john@acme.com")
        form_special = st.text_area("Special Instructions", placeholder="e.g. Live cooking station, kids menu for 20, VIP table setup...", height=68)

        # ── Submit ──
        submitted = st.form_submit_button("Generate Plan", type="primary", disabled=st.session_state["running"], use_container_width=True)

        if submitted:
            errors = []
            if not form_event_type:
                errors.append("Event type is required")
            if form_event_type == "Other" and not form_event_type_custom.strip():
                errors.append("Please specify your event type")
            if not form_guest_count or form_guest_count < 1:
                errors.append("Guest count is required")
            if not form_date:
                errors.append("Event date is required")
            if not form_venue or not form_venue.strip():
                errors.append("Venue / location is required")
            if not form_budget_max or form_budget_max <= 0:
                errors.append("Maximum budget is required")
            if form_budget_min and form_budget_max and form_budget_min > form_budget_max:
                errors.append("Minimum budget cannot exceed maximum budget")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                budget_max = float(form_budget_max)
                budget_min = float(form_budget_min) if form_budget_min else None

                customer = CustomerData(
                    name=form_name if form_name else None,
                    contact=form_contact if form_contact else None,
                    event_type=form_event_type_custom.strip().lower().replace(" ", "_") if form_event_type == "Other" and form_event_type_custom.strip() else EVENT_TYPE_MAP.get(form_event_type),
                    event_date=form_date.isoformat(),
                    event_time=form_time.strftime("%H:%M"),
                    event_end_time=form_end_time.strftime("%H:%M"),
                    guest_count=form_guest_count,
                    venue=form_venue.strip(),
                    dietary_requirements=[d.lower() for d in form_dietary],
                    budget_usd=budget_max,
                    budget_min_usd=budget_min,
                    budget_max_usd=budget_max,
                    cuisine_preferences=[c.lower() for c in form_cuisines],
                    service_style=SERVICE_STYLE_MAP.get(form_service_style) if form_service_style else None,
                    meal_courses=[c.lower() for c in form_courses],
                    menu_variety=form_variety.split(" ")[0].lower(),
                    beverage_options=[b.lower() for b in form_beverages],
                    alcohol_service=any(b in ["Wine", "Beer", "Full Bar"] for b in form_beverages),
                    indoor_outdoor=form_indoor_outdoor.lower() if form_indoor_outdoor else None,
                    venue_kitchen_available=form_kitchen,
                    special_requests=form_special if form_special else None,
                    input_mode="form",
                )

                st.session_state["_action"] = "plan_form"
                st.session_state["_action_customer"] = customer

# --- Validation feedback (free-text mode only) ---
if free_text_mode:
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

    # --- Action buttons (free-text mode) ---
    can_proceed = st.session_state.get("intake_state") is not None and not st.session_state["validation_errors"]
    btn_cols = st.columns([1, 1] if can_proceed else [1])

    with btn_cols[0]:
        if st.button("Generate Plan", type="primary", disabled=st.session_state["running"], use_container_width=True):
            if user_input and user_input.strip():
                st.session_state["_action"] = "plan"
                st.session_state["_action_input"] = user_input

    if can_proceed:
        with btn_cols[1]:
            if st.button("Continue Anyway", type="secondary", disabled=st.session_state["running"], use_container_width=True):
                st.session_state["_action"] = "continue"

# === Placeholders (loader, progress bar + results, full-width below input) ===
loader_placeholder = st.empty()
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

    render_loader(loader_placeholder, is_regen=False, step_index=0)

    _step_counter = {"n": 0}

    def on_intake_update(s: EventState):
        _step_counter["n"] = min(_step_counter["n"] + 1, 4)
        render_loader(loader_placeholder, is_regen=False, step_index=_step_counter["n"])
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
            loader_placeholder.empty()
            st.rerun()
        elif missing_rec:
            st.session_state["intake_state"] = intake_state
            st.session_state["validation_warnings"] = missing_rec
            st.session_state["running"] = False
            loader_placeholder.empty()
            st.rerun()
        else:
            def on_pipeline_update(s: EventState):
                _step_counter["n"] = min(_step_counter["n"] + 1, 4)
                render_loader(loader_placeholder, is_regen=False, step_index=_step_counter["n"])
                render_progress_bar(s, progress_placeholder, running=True)
                render_results_panel(s, results_placeholder)

            loop2 = asyncio.new_event_loop()
            state = loop2.run_until_complete(run_pipeline_from_state(intake_state, log_callback=on_pipeline_update))
            loop2.close()
            st.session_state["state"] = state
            st.session_state["intake_state"] = None
            st.session_state["running"] = False
            loader_placeholder.empty()
            st.rerun()

    except Exception as e:
        loader_placeholder.empty()
        st.error(f"Pipeline error: {e}")
        st.session_state["running"] = False

elif action == "plan_form":
    customer = st.session_state.pop("_action_customer", None)
    is_regen = st.session_state.pop("is_regeneration", False)
    if customer:
        st.session_state["running"] = True
        st.session_state["state"] = None
        st.session_state["intake_state"] = None
        st.session_state["validation_errors"] = None
        st.session_state["validation_warnings"] = None

        render_loader(loader_placeholder, is_regen=is_regen, step_index=0)

        form_state = EventState()
        form_state.customer = customer
        form_state.status = "in_progress"
        form_state.log("IntakeAgent", "form_submission", f"{customer.guest_count} guests, {customer.event_type}", "success")

        _step_counter = {"n": 0}

        def on_pipeline_update(s: EventState):
            _step_counter["n"] = min(_step_counter["n"] + 1, 4)
            render_loader(loader_placeholder, is_regen=is_regen, step_index=_step_counter["n"])
            render_progress_bar(s, progress_placeholder, running=True)
            render_results_panel(s, results_placeholder)

        try:
            loop = asyncio.new_event_loop()
            state = loop.run_until_complete(run_pipeline_from_state(form_state, log_callback=on_pipeline_update))
            loop.close()
            st.session_state["state"] = state
        except Exception as e:
            st.error(f"Pipeline error: {e}")
        finally:
            loader_placeholder.empty()
            st.session_state["running"] = False
            st.rerun()

elif action == "continue":
    st.session_state["running"] = True

    render_loader(loader_placeholder, is_regen=False, step_index=1)
    _step_counter = {"n": 1}

    def on_pipeline_update(s: EventState):
        _step_counter["n"] = min(_step_counter["n"] + 1, 4)
        render_loader(loader_placeholder, is_regen=False, step_index=_step_counter["n"])
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
        loader_placeholder.empty()
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
