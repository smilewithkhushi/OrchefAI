import streamlit as st
from tools.history_db import get_event_history, get_history_summary

st.set_page_config(page_title="Event History — OrchefAI", page_icon="📋", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
.block-container { padding-top: 2rem; max-width: 1100px; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }
.hero { text-align: center; padding: 1.5rem 0 1rem 0; }
.hero h1 {
    font-size: 2.2rem;
    background: linear-gradient(135deg, #C9A962 0%, #E8D5A3 50%, #C9A962 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.hero p { color: #9CA3AF; font-size: 1rem; font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>Event History</h1>
    <p>Track completed events, conversions, and performance</p>
</div>
""", unsafe_allow_html=True)

summary = get_history_summary()

if not summary or summary.get("total", 0) == 0:
    st.info("No completed events yet. Run your first catering plan from the main page!")
else:
    total = summary["total"]
    approved = summary.get("approved", 0) or 0
    needs_review = summary.get("needs_review", 0) or 0
    conversion = (approved / total * 100) if total > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Events", total)
    col2.metric("Approved", int(approved))
    col3.metric("Needs Review", int(needs_review))
    col4.metric("Conversion Rate", f"{conversion:.0f}%")
    col5.metric("Avg Margin", f"{summary.get('avg_margin', 0) or 0:.1f}%")

    st.markdown("---")

    events = get_event_history(limit=50)
    if events:
        for ev in events:
            status = ev.get("status", "")
            status_icon = "🟢" if status == "complete" else "🟡"
            feasible = "Yes" if ev.get("budget_feasible") else "No"
            event_type = (ev.get("event_type") or "N/A").replace("_", " ").title()
            price = ev.get("suggested_price_usd") or 0
            margin = ev.get("margin_percentage") or 0
            guests = ev.get("guest_count") or 0
            venue = ev.get("venue") or "N/A"
            date = ev.get("completed_at") or ev.get("created_at") or ""

            with st.expander(f"{status_icon} {event_type} — {guests} guests — ${price:,.0f} — {date[:10]}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Guests", guests)
                c2.metric("Suggested Price", f"${price:,.0f}")
                c3.metric("Margin", f"{margin:.1f}%")
                c4.metric("Budget OK", feasible)
                st.caption(f"Venue: {venue} | Risk: {ev.get('risk_level', 'N/A')} | ID: {ev.get('event_id', '')}")
