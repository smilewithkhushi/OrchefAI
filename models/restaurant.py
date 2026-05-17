from pydantic import BaseModel
from typing import List, Optional


class RestaurantProfile(BaseModel):
    # Business Identity
    name: str = ""
    owner_name: str = ""
    location: str = ""
    tagline: str = ""
    business_type: str = "in_house_catering"
    years_in_operation: int = 0
    service_regions: List[str] = []

    # Cuisine & Service
    cuisine_types: List[str] = []
    service_styles: List[str] = []
    event_types_served: List[str] = []

    # Capacity & Staffing
    total_staff: int = 0
    kitchen_staff: int = 0
    service_staff: int = 0
    seating_capacity: int = 0
    standing_capacity: int = 0
    area_sqft: float = 0.0
    max_guests_per_event: int = 500
    min_guests_per_event: int = 10
    max_events_per_day: int = 1
    operating_days: List[str] = []
    opening_time: str = ""
    closing_time: str = ""

    # Outsourcing & Collaboration
    has_partner_kitchens: bool = False
    partner_kitchen_count: int = 0
    outsource_categories: List[str] = []
    preferred_suppliers_notes: str = ""

    # Certifications & Facilities
    halal_certified: bool = False
    fssai_certified: bool = False
    iso_22000: bool = False
    vegan_certified: bool = False
    kosher_certified: bool = False
    organic_certified: bool = False
    liquor_license: bool = False
    has_outdoor_area: bool = False
    has_parking: bool = False

    # Delivery & Logistics
    has_delivery_fleet: bool = False
    delivery_radius_km: float = 0.0
    provides_equipment_rental: bool = False
    provides_event_staff: bool = False

    # Pricing Defaults
    default_margin_percentage: float = 30.0
    min_order_value_usd: float = 0.0
    deposit_percentage: float = 50.0

    # Legacy / misc
    notes: str = ""
