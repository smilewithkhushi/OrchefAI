import streamlit as st
from models.restaurant import RestaurantProfile
from tools.history_db import get_restaurant_profile, save_restaurant_profile

st.set_page_config(page_title="Restaurant Profile — OrchefAI", page_icon="🍽️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
.block-container { padding-top: 2rem; max-width: 900px; }
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
.section-label {
    font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 1px; color: #C9A962;
    margin-top: 1.5rem; margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>Restaurant Profile</h1>
    <p>Set up your restaurant details so agents can make better decisions</p>
</div>
""", unsafe_allow_html=True)

profile = get_restaurant_profile() or RestaurantProfile()

ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CUISINE_OPTIONS = [
    "Chinese", "Malay", "Indian", "Western", "Japanese", "Korean",
    "Thai", "Mediterranean", "Italian", "French", "Middle Eastern",
    "Fusion", "Vegetarian", "Seafood", "Other",
]

with st.form("restaurant_profile_form"):
    st.markdown('<div class="section-label">Basic Information</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Restaurant Name", value=profile.name)
        owner_name = st.text_input("Owner / Manager Name", value=profile.owner_name)
    with col2:
        location = st.text_input("Address / Location", value=profile.location)
        cuisine_types = st.multiselect("Cuisine Types", CUISINE_OPTIONS, default=profile.cuisine_types)

    st.markdown('<div class="section-label">Staff</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        total_staff = st.number_input("Total Staff", min_value=0, value=profile.total_staff)
    with col2:
        kitchen_staff = st.number_input("Kitchen Staff", min_value=0, value=profile.kitchen_staff)
    with col3:
        service_staff = st.number_input("Service Staff", min_value=0, value=profile.service_staff)

    st.markdown('<div class="section-label">Capacity & Space</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        seating_capacity = st.number_input("Seating Capacity", min_value=0, value=profile.seating_capacity)
    with col2:
        standing_capacity = st.number_input("Standing Capacity", min_value=0, value=profile.standing_capacity)
    with col3:
        area_sqft = st.number_input("Area (sq ft)", min_value=0.0, value=profile.area_sqft, step=100.0)

    st.markdown('<div class="section-label">Operations</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        operating_days = st.multiselect("Operating Days", ALL_DAYS, default=profile.operating_days)
    with col2:
        opening_time = st.text_input("Opening Time (e.g. 10:00)", value=profile.opening_time)
        closing_time = st.text_input("Closing Time (e.g. 22:00)", value=profile.closing_time)
    with col3:
        max_events_per_day = st.number_input("Max Events / Day", min_value=1, max_value=10, value=profile.max_events_per_day)

    st.markdown('<div class="section-label">Certifications & Facilities</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        halal_certified = st.checkbox("Halal Certified", value=profile.halal_certified)
    with col2:
        liquor_license = st.checkbox("Liquor License", value=profile.liquor_license)
    with col3:
        has_outdoor_area = st.checkbox("Outdoor Area", value=profile.has_outdoor_area)
    with col4:
        has_parking = st.checkbox("Parking Available", value=profile.has_parking)

    notes = st.text_area("Additional Notes", value=profile.notes, height=80,
                         placeholder="Any other details that might help with event planning...")

    submitted = st.form_submit_button("Save Profile", use_container_width=True, type="primary")

    if submitted:
        updated = RestaurantProfile(
            name=name,
            owner_name=owner_name,
            location=location,
            cuisine_types=cuisine_types,
            total_staff=total_staff,
            kitchen_staff=kitchen_staff,
            service_staff=service_staff,
            seating_capacity=seating_capacity,
            standing_capacity=standing_capacity,
            area_sqft=area_sqft,
            operating_days=operating_days,
            opening_time=opening_time,
            closing_time=closing_time,
            has_outdoor_area=has_outdoor_area,
            has_parking=has_parking,
            halal_certified=halal_certified,
            liquor_license=liquor_license,
            max_events_per_day=max_events_per_day,
            notes=notes,
        )
        save_restaurant_profile(updated)
        st.success("Profile saved!")
        st.rerun()

if profile.name:
    st.markdown("---")
    st.markdown('<div class="section-label">Current Profile Summary</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Staff", profile.total_staff)
    col2.metric("Seating Capacity", profile.seating_capacity)
    col3.metric("Operating Days", f"{len(profile.operating_days)}/7")
