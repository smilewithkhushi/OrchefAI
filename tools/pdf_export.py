import io
from fpdf import FPDF
from models.event_state import EventState


GOLD = (201, 169, 98)
DARK = (28, 23, 20)
WHITE = (250, 250, 250)
GRAY = (156, 163, 175)
GREEN = (34, 197, 94)
RED = (220, 38, 38)
YELLOW = (234, 179, 8)


class CateringPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*GOLD)
        self.cell(0, 12, "OrchefAI", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRAY)
        self.cell(0, 5, "Catering Plan Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_draw_color(*GOLD)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"OrchefAI — Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*GOLD)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*GOLD)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def label_value(self, label: str, value: str):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(55, 5, label)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")

    def kv_row(self, label: str, value: str, color=WHITE):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(55, 5, label)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*color)
        self.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")


def generate_pdf(state: EventState) -> bytes:
    pdf = CateringPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_fill_color(*DARK)

    c = state.customer
    p = state.pricing
    cb = p.cost_breakdown

    # --- Status badge ---
    if state.status == "complete":
        pdf.set_text_color(*GREEN)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "STATUS: APPROVED", align="R", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_text_color(*YELLOW)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "STATUS: NEEDS REVIEW", align="R", new_x="LMARGIN", new_y="NEXT")

    # --- Event Overview ---
    pdf.section_title("Event Overview")
    event_type = (c.event_type or "N/A").replace("_", " ").title()
    pdf.label_value("Event Type", event_type)
    pdf.label_value("Date & Time", f"{c.event_date or 'TBD'} {c.event_time or ''}")
    pdf.label_value("Guest Count", str(c.guest_count or "N/A"))
    pdf.label_value("Venue", c.venue or "Not specified")
    pdf.label_value("Dietary Requirements", ", ".join(c.dietary_requirements) or "None")
    pdf.label_value("Customer Budget", f"${c.budget_usd:,.2f}" if c.budget_usd else "N/A")
    if c.special_requests:
        pdf.label_value("Special Requests", c.special_requests)
    pdf.label_value("Event ID", state.event_id)

    # --- Pricing Summary ---
    if cb.total_cost_usd > 0:
        pdf.section_title("Pricing Summary")
        profit = p.suggested_price_usd - cb.total_cost_usd if p.suggested_price_usd > 0 else 0
        pdf.label_value("Suggested Price to Charge", f"${p.suggested_price_usd:,.2f}")
        pdf.label_value("Price Per Guest", f"${p.suggested_price_per_head_usd:,.2f}")
        pdf.label_value("Your Profit", f"${profit:,.2f}")
        pdf.label_value("Margin", f"{p.margin_percentage:.1f}%")

        color = GREEN if p.budget_feasible else RED
        label = "Yes" if p.budget_feasible else f"No (shortfall ${p.budget_shortfall_usd:,.2f})"
        pdf.kv_row("Budget Feasible", label, color)

    # --- Cost Breakdown ---
    if cb.total_cost_usd > 0:
        pdf.section_title("Cost Breakdown")
        costs = [
            ("Food & Ingredients", cb.ingredient_cost_usd),
            ("Staff / Labor", cb.labor_cost_usd),
            ("Delivery & Transport", cb.logistics_cost_usd),
            ("Packaging & Supplies", cb.packaging_cost_usd),
            ("Overhead", cb.overhead_usd),
        ]
        for label, amount in costs:
            pct = (amount / cb.total_cost_usd * 100) if cb.total_cost_usd > 0 else 0
            pdf.kv_row(label, f"${amount:,.2f}  ({pct:.0f}%)")
        pdf.ln(2)
        pdf.set_draw_color(42, 35, 30)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.label_value("TOTAL COST", f"${cb.total_cost_usd:,.2f}")

    # --- Menu ---
    if state.menu.items:
        pdf.section_title("Menu")
        categories = {}
        for item in state.menu.items:
            cat = item.category.replace("_", " ").title()
            categories.setdefault(cat, []).append(item)

        for cat, items in categories.items():
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*GRAY)
            pdf.cell(0, 6, cat.upper(), new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(107, 114, 128)
            pdf.cell(70, 5, "Dish")
            pdf.cell(30, 5, "Portions")
            pdf.cell(30, 5, "Cost/Portion")
            pdf.cell(30, 5, "Total", align="R")
            pdf.cell(0, 5, "Tags", new_x="LMARGIN", new_y="NEXT")

            for item in items:
                total = item.cost_per_portion_usd * item.portions_required
                tags = ", ".join(item.dietary_tags)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*WHITE)
                pdf.cell(70, 5, item.dish_name[:35])
                pdf.cell(30, 5, str(item.portions_required))
                pdf.cell(30, 5, f"${item.cost_per_portion_usd:.2f}")
                pdf.cell(30, 5, f"${total:,.0f}", align="R")
                pdf.set_text_color(*GRAY)
                pdf.cell(0, 5, tags[:30], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # --- Procurement List ---
    if state.inventory.procurement_list:
        pdf.section_title("Shopping List")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(50, 5, "Item")
        pdf.cell(25, 5, "Qty")
        pdf.cell(45, 5, "Supplier")
        pdf.cell(25, 5, "Cost", align="R")
        pdf.cell(0, 5, "Status", align="R", new_x="LMARGIN", new_y="NEXT")

        for p_item in state.inventory.procurement_list:
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*WHITE)
            pdf.cell(50, 5, p_item.ingredient[:25])
            pdf.cell(25, 5, f"{p_item.quantity_required:.1f} {p_item.unit}")
            pdf.cell(45, 5, p_item.supplier_name[:22])
            pdf.cell(25, 5, f"${p_item.total_cost_usd:,.0f}", align="R")
            color = GREEN if p_item.availability == "confirmed" else YELLOW if p_item.availability == "partial" else RED
            pdf.set_text_color(*color)
            pdf.cell(0, 5, p_item.availability.title(), align="R", new_x="LMARGIN", new_y="NEXT")

    # --- Risks & Warnings ---
    if state.monitoring.risks or state.inventory.shortages:
        pdf.section_title("Risks & Warnings")

        for risk in state.monitoring.risks:
            sev_color = RED if risk.severity in ("HIGH", "CRITICAL") else YELLOW if risk.severity == "MEDIUM" else GREEN
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*sev_color)
            pdf.cell(20, 5, risk.severity)
            pdf.set_text_color(*WHITE)
            pdf.cell(0, 5, risk.description[:80], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*GRAY)
            pdf.cell(0, 5, f"  Action: {risk.suggested_action[:90]}", new_x="LMARGIN", new_y="NEXT")

        if state.inventory.shortages:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*YELLOW)
            pdf.cell(0, 5, "Ingredient Shortages", new_x="LMARGIN", new_y="NEXT")
            for s in state.inventory.shortages:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*WHITE)
                sub = f" — Use {s.suggested_substitute} instead" if s.suggested_substitute else ""
                pdf.cell(0, 5,
                         f"  {s.ingredient}: need {s.required:.1f}kg, have {s.available:.1f}kg (short {s.deficit:.1f}kg){sub}",
                         new_x="LMARGIN", new_y="NEXT")

    # --- AI Summary ---
    if state.monitoring.summary:
        pdf.section_title("AI Summary")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*WHITE)
        pdf.multi_cell(0, 5, state.monitoring.summary)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
