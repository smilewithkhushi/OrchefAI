import json
import os
import streamlit as st
from config import COST_PROFILES, REGION_KEYWORDS
from tools.history_db import get_kitchen_stock, save_kitchen_item, delete_kitchen_item

st.set_page_config(page_title="Inventory — OrchefAI", page_icon="📦", layout="wide")

SUPPLIERS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "suppliers.json")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
.block-container { padding-top: 1.5rem; max-width: 1200px; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }
.hero { display: flex; align-items: center; gap: 1rem; padding: 1rem 0; }
.hero img { height: 80px; }
.hero .hero-text h1 {
    font-size: 2.2rem;
    background: linear-gradient(135deg, #C9A962 0%, #E8D5A3 50%, #C9A962 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0; line-height: 1.1;
}
.hero .hero-text p { color: #9CA3AF; font-size: 0.82rem; font-family: 'Inter', sans-serif; margin: 0; }
.sec-label {
    font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 1px; color: #C9A962;
    margin: 0.6rem 0 0.4rem 0; padding: 0;
}
.sup-card {
    background: #1C1714; border: 1px solid #2D2D2D; border-radius: 10px;
    padding: 1rem 1.2rem; margin-bottom: 0.6rem;
}
.sup-name { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: #FAFAFA; }
.sup-type { font-family: 'Inter', sans-serif; font-size: 0.72rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; }
.sup-city { font-family: 'Inter', sans-serif; font-size: 0.78rem; color: #9CA3AF; margin-top: 0.3rem; }
.badge-halal { display: inline-block; background: rgba(16,185,129,0.15); color: #10B981; padding: 2px 10px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; font-family: 'Inter', sans-serif; }
.badge-no-halal { display: inline-block; background: rgba(239,68,68,0.10); color: #EF4444; padding: 2px 10px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; font-family: 'Inter', sans-serif; }
.rel-high { color: #10B981; font-weight: 700; }
.rel-mid { color: #F59E0B; font-weight: 700; }
.rel-low { color: #EF4444; font-weight: 700; }
.stock-green { color: #10B981; font-weight: 600; }
.stock-yellow { color: #F59E0B; font-weight: 600; }
.stock-red { color: #EF4444; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <img src="app/static/logo.png" alt="OrchefAI" />
    <div class="hero-text">
        <h1>Inventory & Suppliers</h1>
        <p>Manage supplier network, stock levels, and kitchen inventory across regions</p>
    </div>
</div>
""", unsafe_allow_html=True)


@st.cache_data
def load_suppliers():
    with open(SUPPLIERS_PATH) as f:
        return json.load(f)


all_suppliers = load_suppliers()

region_options = {v["label"]: k for k, v in COST_PROFILES.items() if k != "default"}
selected_label = st.selectbox("Operating Region", list(region_options.keys()), index=0)
selected_region = region_options[selected_label]


_NEIGHBORHOOD_OVERRIDES = {"little india": "singapore"}


def _resolve_region(city: str) -> str | None:
    city_lower = city.lower()
    for neighborhood, actual_region in _NEIGHBORHOOD_OVERRIDES.items():
        if neighborhood in city_lower:
            return actual_region
    for region_key, keywords in REGION_KEYWORDS.items():
        normalized = city_lower.replace(",", " ").replace("-", " ")
        if any(kw in normalized for kw in keywords):
            return region_key
    return None


def _filter_suppliers(suppliers_list, region_key):
    filtered = []
    for s in suppliers_list:
        resolved = _resolve_region(s.get("city", ""))
        if resolved == region_key:
            filtered.append(s)
    return filtered


suppliers = _filter_suppliers(all_suppliers, selected_region)

# --- Quick Stats ---
all_ingredients = set()
low_stock_count = 0
reliability_scores = []
for s in suppliers:
    all_ingredients.update(s.get("supplies", []))
    reliability_scores.append(s.get("reliability_score", 0))
    for _k, v in s.get("stock_available_kg", {}).items():
        if v < 100:
            low_stock_count += 1
    for _k, v in s.get("stock_available_units", {}).items():
        if v < 200:
            low_stock_count += 1

avg_reliability = sum(reliability_scores) / len(reliability_scores) if reliability_scores else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Suppliers", len(suppliers))
col2.metric("Ingredients Tracked", len(all_ingredients))
col3.metric("Low Stock Alerts", low_stock_count)
col4.metric("Avg Reliability", f"{avg_reliability:.0%}")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["Supplier Directory", "Stock Levels", "My Kitchen Stock"])

# ===================== TAB 1: SUPPLIER DIRECTORY =====================
with tab1:
    if not suppliers:
        st.info(f"No suppliers registered in **{selected_label}** yet. Add local suppliers to expand your network here.")

    for s in suppliers:
        rel = s.get("reliability_score", 0)
        rel_class = "rel-high" if rel >= 0.95 else ("rel-mid" if rel >= 0.90 else "rel-low")
        halal_badge = '<span class="badge-halal">Halal</span>' if s.get("halal_certified") else '<span class="badge-no-halal">Non-Halal</span>'
        items_count = len(s.get("supplies", []))
        lead = s.get("lead_time_hours", "—")

        st.markdown(f"""
        <div class="sup-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span class="sup-name">{s['name']}</span>
                    <span style="margin-left:0.6rem;">{halal_badge}</span>
                </div>
                <div>
                    <span class="{rel_class}" style="font-size:1.1rem;">{rel:.0%}</span>
                    <span style="color:#9CA3AF; font-size:0.7rem; margin-left:0.2rem;">reliability</span>
                </div>
            </div>
            <div class="sup-type">{s.get('type', '').replace('_', ' ')}</div>
            <div class="sup-city">{s.get('city', '')} &nbsp;·&nbsp; {lead}h lead time &nbsp;·&nbsp; {items_count} items</div>
            <div style="margin-top:0.4rem; font-size:0.78rem; color:#6B7280; font-family:'Inter',sans-serif;">{s.get('notes', '')}</div>
        </div>
        """, unsafe_allow_html=True)

# ===================== TAB 2: STOCK LEVELS =====================
with tab2:
    if not suppliers:
        st.info(f"No supplier stock data for **{selected_label}**. Supplier onboarding for this region is pending.")

    stock_rows = []
    for s in suppliers:
        name = s["name"]
        prices_kg = s.get("price_per_kg_usd", {})
        prices_unit = s.get("price_per_unit_usd", {})
        for ingredient, qty in s.get("stock_available_kg", {}).items():
            price = prices_kg.get(ingredient, 0)
            stock_rows.append((name, ingredient, qty, "kg", price))
        for ingredient, qty in s.get("stock_available_units", {}).items():
            price = prices_unit.get(ingredient, 0)
            stock_rows.append((name, ingredient, qty, "units", price))

    stock_rows.sort(key=lambda r: r[2])

    st.markdown(f'<p class="sec-label">{len(stock_rows)} items across all suppliers — sorted by stock level (lowest first)</p>', unsafe_allow_html=True)

    header_cols = st.columns([2, 2, 1, 0.6, 1, 0.8])
    header_cols[0].markdown("**Supplier**")
    header_cols[1].markdown("**Ingredient**")
    header_cols[2].markdown("**Stock**")
    header_cols[3].markdown("**Unit**")
    header_cols[4].markdown("**Price/unit**")
    header_cols[5].markdown("**Status**")

    for supplier_name, ingredient, qty, unit, price in stock_rows:
        if unit == "kg":
            status_class = "stock-green" if qty >= 500 else ("stock-yellow" if qty >= 100 else "stock-red")
            status_label = "OK" if qty >= 500 else ("Low" if qty >= 100 else "Critical")
        else:
            status_class = "stock-green" if qty >= 5000 else ("stock-yellow" if qty >= 200 else "stock-red")
            status_label = "OK" if qty >= 5000 else ("Low" if qty >= 200 else "Critical")

        cols = st.columns([2, 2, 1, 0.6, 1, 0.8])
        cols[0].write(supplier_name)
        cols[1].write(ingredient.replace("_", " ").title())
        cols[2].write(f"{qty:,.0f}")
        cols[3].write(unit)
        cols[4].write(f"${price:.2f}")
        cols[5].markdown(f'<span class="{status_class}">{status_label}</span>', unsafe_allow_html=True)

# ===================== TAB 3: MY KITCHEN STOCK =====================
with tab3:
    st.markdown(f'<p class="sec-label">In-house inventory for {selected_label}</p>', unsafe_allow_html=True)

    kitchen_items = get_kitchen_stock(region=selected_region)

    if kitchen_items:
        header_cols = st.columns([2, 1, 0.8, 1, 0.8])
        header_cols[0].markdown("**Ingredient**")
        header_cols[1].markdown("**Quantity**")
        header_cols[2].markdown("**Unit**")
        header_cols[3].markdown("**Cost/unit**")
        header_cols[4].markdown("**Action**")

        for item in kitchen_items:
            cols = st.columns([2, 1, 0.8, 1, 0.8])
            cols[0].write(item["ingredient"].replace("_", " ").title())
            cols[1].write(f"{item['quantity']:,.1f}")
            cols[2].write(item["unit"])
            cols[3].write(f"${item['cost_per_unit']:.2f}")
            if cols[4].button("Remove", key=f"del_{item['id']}"):
                delete_kitchen_item(item["id"])
                st.rerun()
    else:
        st.info("No kitchen stock recorded for this region yet. Add items below.")

    st.markdown(f'<p class="sec-label">Add Item</p>', unsafe_allow_html=True)

    with st.form("add_kitchen_item", clear_on_submit=True):
        fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
        with fc1:
            new_ingredient = st.text_input("Ingredient", placeholder="e.g. chicken")
        with fc2:
            new_qty = st.number_input("Quantity", min_value=0.0, value=10.0, step=1.0)
        with fc3:
            new_unit = st.selectbox("Unit", ["kg", "units", "liters", "packs"])
        with fc4:
            new_cost = st.number_input("Cost/unit (USD)", min_value=0.0, value=1.0, step=0.50)

        if st.form_submit_button("Add to Stock", use_container_width=True, type="primary"):
            if new_ingredient.strip():
                save_kitchen_item(new_ingredient.strip().lower().replace(" ", "_"), new_qty, new_unit, new_cost, selected_region)
                st.success(f"Added {new_ingredient}")
                st.rerun()
            else:
                st.warning("Please enter an ingredient name.")
