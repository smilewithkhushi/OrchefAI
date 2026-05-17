import streamlit as st
from models.restaurant import RestaurantProfile
from tools.history_db import get_restaurant_profile, save_restaurant_profile

st.set_page_config(page_title="Catering Profile — OrchefAI", page_icon="🍽️", layout="wide")

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
.summary-card {
    background: #1C1714; border: 2px solid #C9A962;
    border-radius: 12px; padding: 1.2rem 1.5rem; margin-top: 1.2rem;
}
.summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; }
.summary-item { text-align: center; padding: 0.6rem 0.4rem; background: rgba(201,169,98,0.05); border-radius: 8px; }
.summary-value { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #FAFAFA; }
.summary-label { font-family: 'Inter', sans-serif; font-size: 0.68rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
.badge { display: inline-block; background: rgba(201,169,98,0.15); color: #C9A962; padding: 4px 12px; border-radius: 20px; font-family: 'Inter', sans-serif; font-size: 0.73rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <img src="app/static/logo.png" alt="OrchefAI" />
    <div class="hero-text">
        <h1>Catering Profile</h1>
        <p>Your business details help agents optimize plans for your operation</p>
    </div>
</div>
""", unsafe_allow_html=True)


def _label(text):
    st.markdown(f'<p class="sec-label">{text}</p>', unsafe_allow_html=True)


profile = get_restaurant_profile() or RestaurantProfile()

ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CUISINE_OPTIONS = [
    "North Indian", "South Indian", "Chinese", "Malay", "Pan-Asian",
    "Japanese", "Korean", "Thai", "Western", "Italian", "French",
    "Mediterranean", "Middle Eastern", "Mexican", "BBQ & Grill",
    "Seafood", "Bakery & Desserts", "Fusion", "Vegetarian", "Other",
]
SERVICE_STYLES = ["Buffet", "Plated / Sit-down", "Cocktail Pass-around", "Food Stations", "Family Style", "Live Counters"]
EVENT_TYPES = [
    "Wedding", "Corporate Lunch", "Birthday Party", "Cocktail Reception",
    "Conference", "Gala Dinner", "Baby Shower", "Engagement Party",
    "Anniversary", "Graduation Party", "Festival / Cultural",
    "Charity Event", "Product Launch", "Team Building",
]
OUTSOURCE_CATEGORIES = ["Desserts & Pastry", "Beverages & Bar", "Live Counters", "Specialty Cuisine", "Baked Goods", "Ice Cream & Frozen", "Floral & Decor Food"]
REGION_OPTIONS = [
    "Singapore", "Mumbai", "Delhi NCR", "Bangalore", "Chennai",
    "Hyderabad", "Kolkata", "Pune", "Kuala Lumpur", "Bangkok",
    "Jakarta", "Dubai", "Abu Dhabi", "London", "New York",
    "Sydney", "Melbourne", "San Francisco", "Los Angeles",
]
BUSINESS_TYPE_MAP = {
    "In-house Kitchen": "in_house_catering",
    "Outsourced / Cloud Kitchen": "outsourced_catering",
    "Hybrid (Cook + Outsource)": "hybrid",
}
BUSINESS_TYPE_REVERSE = {v: k for k, v in BUSINESS_TYPE_MAP.items()}

with st.form("restaurant_profile_form"):

    tab1, tab2, tab3, tab4 = st.tabs(["Business & Cuisine", "Capacity & Staff", "Partners & Certs", "Delivery & Pricing"])

    with tab1:
        _label("Business Identity")
        btype_label = BUSINESS_TYPE_REVERSE.get(profile.business_type, "In-house Kitchen")
        business_type = st.radio("Business Type", list(BUSINESS_TYPE_MAP.keys()), index=list(BUSINESS_TYPE_MAP.keys()).index(btype_label), horizontal=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Business Name", value=profile.name, placeholder="e.g. Spice Route Catering")
        with col2:
            owner_name = st.text_input("Owner / Manager", value=profile.owner_name)
        with col3:
            location = st.text_input("Primary Location", value=profile.location, placeholder="e.g. Mumbai, India")

        col1, col2 = st.columns([2, 1])
        with col1:
            tagline = st.text_input("Tagline", value=profile.tagline, placeholder="e.g. Premium halal catering for corporate & social events")
        with col2:
            years_in_operation = st.number_input("Years in Operation", min_value=0, max_value=100, value=profile.years_in_operation)

        service_regions = st.multiselect("Service Regions", REGION_OPTIONS, default=[r for r in profile.service_regions if r in REGION_OPTIONS])

        _label("Cuisine & Service")
        cuisine_types = st.multiselect("Cuisine Specialties", CUISINE_OPTIONS, default=[c for c in profile.cuisine_types if c in CUISINE_OPTIONS])
        col1, col2 = st.columns(2)
        with col1:
            service_styles = st.multiselect("Service Styles", SERVICE_STYLES, default=[s for s in profile.service_styles if s in SERVICE_STYLES])
        with col2:
            event_types_served = st.multiselect("Event Types", EVENT_TYPES, default=[e for e in profile.event_types_served if e in EVENT_TYPES])

    with tab2:
        _label("Capacity")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            min_guests = st.number_input("Min Guests", min_value=1, max_value=10000, value=profile.min_guests_per_event)
        with col2:
            max_guests = st.number_input("Max Guests", min_value=1, max_value=10000, value=profile.max_guests_per_event)
        with col3:
            seating_capacity = st.number_input("Seating", min_value=0, value=profile.seating_capacity)
        with col4:
            standing_capacity = st.number_input("Standing", min_value=0, value=profile.standing_capacity)

        _label("Staffing")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_staff = st.number_input("Total Staff", min_value=0, value=profile.total_staff)
        with col2:
            kitchen_staff = st.number_input("Kitchen Staff", min_value=0, value=profile.kitchen_staff)
        with col3:
            service_staff = st.number_input("Service Staff", min_value=0, value=profile.service_staff)
        with col4:
            max_events_per_day = st.number_input("Max Events/Day", min_value=1, max_value=10, value=profile.max_events_per_day)

        _label("Operating Hours")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            operating_days = st.multiselect("Operating Days", ALL_DAYS, default=profile.operating_days)
        with col2:
            opening_time = st.text_input("Opens", value=profile.opening_time, placeholder="09:00")
        with col3:
            closing_time = st.text_input("Closes", value=profile.closing_time, placeholder="23:00")

    with tab3:
        _label("Outsourcing & Partners")
        has_partner_kitchens = st.checkbox("We collaborate with partner kitchens / outsource certain items", value=profile.has_partner_kitchens)
        if has_partner_kitchens:
            col1, col2 = st.columns([1, 2])
            with col1:
                partner_kitchen_count = st.number_input("Partner Kitchens", min_value=0, max_value=50, value=profile.partner_kitchen_count)
            with col2:
                outsource_categories = st.multiselect("Outsourced Categories", OUTSOURCE_CATEGORIES, default=[c for c in profile.outsource_categories if c in OUTSOURCE_CATEGORIES])
            preferred_suppliers_notes = st.text_area("Partner Notes", value=profile.preferred_suppliers_notes, height=60, placeholder="e.g. Baker Street for desserts, BarCraft for beverages")
        else:
            partner_kitchen_count = 0
            outsource_categories = []
            preferred_suppliers_notes = ""

        _label("Certifications")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            halal_certified = st.checkbox("Halal", value=profile.halal_certified)
        with col2:
            fssai_certified = st.checkbox("FSSAI", value=profile.fssai_certified)
        with col3:
            iso_22000 = st.checkbox("ISO 22000", value=profile.iso_22000)
        with col4:
            vegan_certified = st.checkbox("Vegan", value=profile.vegan_certified)
        with col5:
            kosher_certified = st.checkbox("Kosher", value=profile.kosher_certified)
        with col6:
            organic_certified = st.checkbox("Organic", value=profile.organic_certified)

        _label("Facilities")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            liquor_license = st.checkbox("Liquor License", value=profile.liquor_license)
        with col2:
            has_outdoor_area = st.checkbox("Outdoor Area", value=profile.has_outdoor_area)
        with col3:
            has_parking = st.checkbox("Parking", value=profile.has_parking)
        with col4:
            provides_equipment_rental = st.checkbox("Equipment Rental", value=profile.provides_equipment_rental)

    with tab4:
        _label("Delivery & Logistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            has_delivery_fleet = st.checkbox("Own Fleet", value=profile.has_delivery_fleet)
        with col2:
            delivery_radius_km = st.number_input("Radius (km)", min_value=0.0, max_value=500.0, value=profile.delivery_radius_km, step=5.0)
        with col3:
            provides_event_staff = st.checkbox("Event Staff", value=profile.provides_event_staff)
        with col4:
            area_sqft = st.number_input("Prep Area (sqft)", min_value=0.0, value=profile.area_sqft, step=100.0)

        _label("Pricing Defaults")
        col1, col2, col3 = st.columns(3)
        with col1:
            default_margin = st.slider("Profit Margin %", min_value=10, max_value=60, value=int(profile.default_margin_percentage))
        with col2:
            min_order = st.number_input("Min Order (USD)", min_value=0.0, value=profile.min_order_value_usd, step=50.0)
        with col3:
            deposit_pct = st.slider("Deposit %", min_value=0, max_value=100, value=int(profile.deposit_percentage), step=5)

        notes = st.text_area("Additional Notes", value=profile.notes, height=50, placeholder="Anything else relevant to event planning...")

    submitted = st.form_submit_button("Save Profile", use_container_width=True, type="primary")

    if submitted:
        updated = RestaurantProfile(
            name=name, owner_name=owner_name, location=location, tagline=tagline,
            business_type=BUSINESS_TYPE_MAP[business_type],
            years_in_operation=years_in_operation, service_regions=service_regions,
            cuisine_types=cuisine_types, service_styles=service_styles,
            event_types_served=event_types_served,
            total_staff=total_staff, kitchen_staff=kitchen_staff, service_staff=service_staff,
            seating_capacity=seating_capacity, standing_capacity=standing_capacity,
            area_sqft=area_sqft, max_guests_per_event=max_guests, min_guests_per_event=min_guests,
            max_events_per_day=max_events_per_day, operating_days=operating_days,
            opening_time=opening_time, closing_time=closing_time,
            has_partner_kitchens=has_partner_kitchens, partner_kitchen_count=partner_kitchen_count,
            outsource_categories=outsource_categories, preferred_suppliers_notes=preferred_suppliers_notes,
            halal_certified=halal_certified, fssai_certified=fssai_certified, iso_22000=iso_22000,
            vegan_certified=vegan_certified, kosher_certified=kosher_certified, organic_certified=organic_certified,
            liquor_license=liquor_license, has_outdoor_area=has_outdoor_area, has_parking=has_parking,
            has_delivery_fleet=has_delivery_fleet, delivery_radius_km=delivery_radius_km,
            provides_equipment_rental=provides_equipment_rental, provides_event_staff=provides_event_staff,
            default_margin_percentage=float(default_margin), min_order_value_usd=min_order,
            deposit_percentage=float(deposit_pct), notes=notes,
        )
        save_restaurant_profile(updated)
        st.success("Profile saved!")
        st.rerun()

# === SUMMARY ===
if profile.name:
    certs = sum([profile.halal_certified, profile.fssai_certified, profile.iso_22000,
                 profile.vegan_certified, profile.kosher_certified, profile.organic_certified])
    btype_display = BUSINESS_TYPE_REVERSE.get(profile.business_type, "In-house")
    st.markdown(f"""
    <div class="summary-card">
        <div style="text-align:center; margin-bottom:0.8rem;"><span class="badge">{btype_display}</span></div>
        <div class="summary-grid">
            <div class="summary-item"><div class="summary-value">{profile.total_staff}</div><div class="summary-label">Staff</div></div>
            <div class="summary-item"><div class="summary-value">{profile.max_guests_per_event}</div><div class="summary-label">Max Guests</div></div>
            <div class="summary-item"><div class="summary-value">{profile.delivery_radius_km:.0f} km</div><div class="summary-label">Delivery</div></div>
            <div class="summary-item"><div class="summary-value">{certs}</div><div class="summary-label">Certifications</div></div>
            <div class="summary-item"><div class="summary-value">{len(profile.service_styles)}</div><div class="summary-label">Service Styles</div></div>
            <div class="summary-item"><div class="summary-value">{len(profile.service_regions)}</div><div class="summary-label">Regions</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
