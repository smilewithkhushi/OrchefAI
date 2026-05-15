import streamlit as st
import json
from tools.history_db import get_event_history, get_event_detail, get_history_summary

st.set_page_config(page_title="Event History — OrchefAI", page_icon="📋", layout="wide")

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
.detail-label { color: #9CA3AF; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.1rem; }
.detail-value { color: #F3F4F6; font-size: 0.95rem; font-weight: 500; margin-bottom: 0.8rem; }
.section-header { color: #C9A962; font-weight: 600; font-size: 0.85rem; margin: 1rem 0 0.5rem 0; border-bottom: 1px solid #2D2D2D; padding-bottom: 0.3rem; }
.menu-item { background: #1A1A2E; border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.4rem; border-left: 3px solid #C9A962; }
.risk-high { color: #EF4444; font-weight: 600; }
.risk-medium { color: #F59E0B; font-weight: 600; }
.risk-low { color: #10B981; font-weight: 600; }
.risk-none { color: #10B981; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <img src="app/static/logo.png" alt="OrchefAI" />
    <div class="hero-text">
        <h1>Event History</h1>
        <p>Track completed events, conversions, and performance</p>
    </div>
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
            event_id = ev.get("event_id", "")

            with st.expander(f"{status_icon} {event_type} — {guests} guests — ${price:,.0f} — {date[:10]}"):
                state = get_event_detail(event_id)
                if not state:
                    st.warning("Could not load event details.")
                    continue

                # --- Tabs for organized detail view ---
                tab_overview, tab_menu, tab_costs, tab_risks, tab_logs = st.tabs(
                    ["Overview", "Menu", "Costs & Pricing", "Risk Report", "Agent Logs"]
                )

                # === OVERVIEW TAB ===
                with tab_overview:
                    st.markdown('<p class="section-header">EVENT DETAILS</p>', unsafe_allow_html=True)
                    ov1, ov2, ov3, ov4 = st.columns(4)
                    with ov1:
                        st.markdown(f'<p class="detail-label">Event Type</p><p class="detail-value">{event_type}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="detail-label">Event Date</p><p class="detail-value">{state.customer.event_date or "N/A"}</p>', unsafe_allow_html=True)
                    with ov2:
                        st.markdown(f'<p class="detail-label">Guest Count</p><p class="detail-value">{state.customer.guest_count or "N/A"}</p>', unsafe_allow_html=True)
                        time_display = state.customer.event_time or "N/A"
                        if getattr(state.customer, "event_end_time", None):
                            time_display = f"{state.customer.event_time} – {state.customer.event_end_time}"
                        st.markdown(f'<p class="detail-label">Service Time</p><p class="detail-value">{time_display}</p>', unsafe_allow_html=True)
                    with ov3:
                        st.markdown(f'<p class="detail-label">Venue</p><p class="detail-value">{state.customer.venue or "N/A"}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="detail-label">Setting</p><p class="detail-value">{(state.customer.indoor_outdoor or "N/A").title()}</p>', unsafe_allow_html=True)
                    with ov4:
                        st.markdown(f'<p class="detail-label">Service Style</p><p class="detail-value">{(state.customer.service_style or "N/A").replace("_", " ").title()}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="detail-label">Input Mode</p><p class="detail-value">{(state.customer.input_mode or "N/A").title()}</p>', unsafe_allow_html=True)

                    st.markdown('<p class="section-header">CUSTOMER</p>', unsafe_allow_html=True)
                    cu1, cu2 = st.columns(2)
                    with cu1:
                        st.markdown(f'<p class="detail-label">Name</p><p class="detail-value">{state.customer.name or "N/A"}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="detail-label">Contact</p><p class="detail-value">{state.customer.contact or "N/A"}</p>', unsafe_allow_html=True)
                    with cu2:
                        budget_str = f"${state.customer.budget_usd:,.0f}" if state.customer.budget_usd else "N/A"
                        if state.customer.budget_min_usd and state.customer.budget_max_usd:
                            budget_str = f"${state.customer.budget_min_usd:,.0f} – ${state.customer.budget_max_usd:,.0f}"
                        st.markdown(f'<p class="detail-label">Budget</p><p class="detail-value">{budget_str}</p>', unsafe_allow_html=True)
                        dietary = ", ".join(state.customer.dietary_requirements) if state.customer.dietary_requirements else "None"
                        st.markdown(f'<p class="detail-label">Dietary Requirements</p><p class="detail-value">{dietary}</p>', unsafe_allow_html=True)

                    if state.customer.cuisine_preferences:
                        st.markdown(f'<p class="detail-label">Cuisine Preferences</p><p class="detail-value">{", ".join(state.customer.cuisine_preferences)}</p>', unsafe_allow_html=True)
                    if state.customer.special_requests:
                        st.markdown(f'<p class="detail-label">Special Requests</p><p class="detail-value">{state.customer.special_requests}</p>', unsafe_allow_html=True)

                # === MENU TAB ===
                with tab_menu:
                    if state.menu.items:
                        st.markdown('<p class="section-header">MENU ITEMS</p>', unsafe_allow_html=True)

                        categories = {}
                        for item in state.menu.items:
                            cat = item.category or "Other"
                            categories.setdefault(cat, []).append(item)

                        for cat, items in categories.items():
                            st.markdown(f"**{cat.replace('_', ' ').title()}**")
                            for item in items:
                                tags = ", ".join(item.dietary_tags) if item.dietary_tags else ""
                                tag_badge = f" · `{tags}`" if tags else ""
                                st.markdown(
                                    f"- **{item.dish_name}** — {item.portions_required} portions × ${item.cost_per_portion_usd:.2f} = ${item.portions_required * item.cost_per_portion_usd:.2f}{tag_badge}"
                                )
                            st.markdown("")

                        mc1, mc2, mc3 = st.columns(3)
                        mc1.metric("Total Food Cost", f"${state.menu.total_food_cost_usd:,.2f}")
                        mc2.metric("Cost Per Head", f"${state.menu.cost_per_head_usd:,.2f}")
                        mc3.metric("Total Dishes", len(state.menu.items))

                        if state.menu.warnings:
                            st.markdown('<p class="section-header">WARNINGS</p>', unsafe_allow_html=True)
                            for w in state.menu.warnings:
                                st.warning(w)
                        if state.menu.notes:
                            st.caption(f"Notes: {state.menu.notes}")
                    else:
                        st.info("No menu data available.")

                # === COSTS & PRICING TAB ===
                with tab_costs:
                    if state.pricing.cost_breakdown.total_cost_usd > 0:
                        st.markdown('<p class="section-header">COST BREAKDOWN</p>', unsafe_allow_html=True)
                        cb = state.pricing.cost_breakdown

                        pc1, pc2 = st.columns(2)
                        with pc1:
                            st.markdown(f"| Category | Amount |")
                            st.markdown(f"|----------|--------|")
                            st.markdown(f"| Food & Ingredients | ${cb.ingredient_cost_usd:,.2f} |")
                            st.markdown(f"| Staff / Labor | ${cb.labor_cost_usd:,.2f} |")
                            st.markdown(f"| Logistics & Delivery | ${cb.logistics_cost_usd:,.2f} |")
                            st.markdown(f"| Packaging | ${cb.packaging_cost_usd:,.2f} |")
                            st.markdown(f"| Overhead | ${cb.overhead_usd:,.2f} |")
                            st.markdown(f"| **Total Cost** | **${cb.total_cost_usd:,.2f}** |")

                        with pc2:
                            st.metric("Suggested Price", f"${state.pricing.suggested_price_usd:,.2f}")
                            st.metric("Per Head Cost", f"${state.pricing.per_head_cost_usd:,.2f}")
                            st.metric("Per Head Price", f"${state.pricing.suggested_price_per_head_usd:,.2f}")
                            st.metric("Margin", f"{state.pricing.margin_percentage:.1f}%")
                            feasible_text = "✅ Yes" if state.pricing.budget_feasible else f"❌ No (shortfall ${state.pricing.budget_shortfall_usd:,.0f})"
                            st.metric("Budget Feasible", feasible_text)

                        if state.pricing.optimization_suggestions:
                            st.markdown('<p class="section-header">OPTIMIZATION SUGGESTIONS</p>', unsafe_allow_html=True)
                            for sug in state.pricing.optimization_suggestions:
                                saving = sug.get("estimated_saving_usd", 0)
                                st.markdown(f"- {sug.get('suggestion', '')} — saves **${saving:,.0f}**")

                        if state.pricing.notes:
                            st.caption(f"Notes: {state.pricing.notes}")
                    else:
                        st.info("No pricing data available.")

                    # Inventory / Procurement summary
                    if state.inventory.procurement_list:
                        st.markdown('<p class="section-header">PROCUREMENT SUMMARY</p>', unsafe_allow_html=True)
                        st.markdown(f"**Total Ingredient Cost:** ${state.inventory.total_ingredient_cost_usd:,.2f}")
                        st.markdown(f"**Suppliers:** {len(set(p.supplier_name for p in state.inventory.procurement_list))}")
                        st.markdown(f"**Items:** {len(state.inventory.procurement_list)}")

                        if state.inventory.shortages:
                            st.markdown('<p class="section-header">SHORTAGES</p>', unsafe_allow_html=True)
                            for s in state.inventory.shortages:
                                severity_class = "risk-high" if s.severity == "HIGH" else "risk-medium" if s.severity == "MEDIUM" else "risk-low"
                                st.markdown(f'- <span class="{severity_class}">[{s.severity}]</span> **{s.ingredient}** — need {s.required:.1f}, have {s.available:.1f} (deficit: {s.deficit:.1f})', unsafe_allow_html=True)
                                if s.suggested_substitute:
                                    st.caption(f"  Substitute: {s.suggested_substitute}")

                # === RISK REPORT TAB ===
                with tab_risks:
                    risk_level = state.monitoring.overall_risk_level
                    risk_class = f"risk-{risk_level.lower()}" if risk_level else "risk-none"
                    st.markdown(f'<p class="section-header">OVERALL RISK: <span class="{risk_class}">{risk_level}</span></p>', unsafe_allow_html=True)

                    if state.monitoring.risks:
                        for risk in state.monitoring.risks:
                            severity_class = "risk-high" if risk.severity in ["HIGH", "CRITICAL"] else "risk-medium" if risk.severity == "MEDIUM" else "risk-low"
                            st.markdown(f'<span class="{severity_class}">**[{risk.severity}]**</span> **{risk.type}** — {risk.description}', unsafe_allow_html=True)
                            st.caption(f"Affected: {risk.affected_component} | Action: {risk.suggested_action}")
                    else:
                        st.success("No risks identified.")

                    if state.monitoring.re_plan_triggered:
                        st.warning(f"Re-plan was triggered: {state.monitoring.re_plan_constraints}")

                    st.markdown('<p class="section-header">APPROVAL</p>', unsafe_allow_html=True)
                    if state.monitoring.final_approved:
                        st.success(f"✅ Approved — {state.monitoring.approval_notes}")
                    else:
                        st.warning(f"⚠️ Not approved — {state.monitoring.approval_notes}")

                    if state.monitoring.summary:
                        st.caption(f"Summary: {state.monitoring.summary}")

                # === AGENT LOGS TAB ===
                with tab_logs:
                    if state.agent_log:
                        st.markdown('<p class="section-header">PIPELINE EXECUTION LOG</p>', unsafe_allow_html=True)
                        for log in state.agent_log:
                            duration_str = f" ({log.duration_ms}ms)" if log.duration_ms else ""
                            status_emoji = "✅" if log.status == "success" else "❌"
                            st.markdown(f"{status_emoji} **{log.agent}** — {log.action}{duration_str}")
                            st.caption(f"{log.timestamp} | {log.output_summary[:150]}")
                    else:
                        st.info("No agent logs available.")
