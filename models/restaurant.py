from pydantic import BaseModel
from typing import List, Optional


class RestaurantProfile(BaseModel):
    name: str = ""
    owner_name: str = ""
    location: str = ""
    cuisine_types: List[str] = []
    total_staff: int = 0
    kitchen_staff: int = 0
    service_staff: int = 0
    seating_capacity: int = 0
    standing_capacity: int = 0
    area_sqft: float = 0.0
    operating_days: List[str] = []
    opening_time: str = ""
    closing_time: str = ""
    has_outdoor_area: bool = False
    has_parking: bool = False
    halal_certified: bool = False
    liquor_license: bool = False
    max_events_per_day: int = 1
    notes: str = ""
