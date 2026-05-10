from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class CustomerData(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    guest_count: Optional[int] = None
    venue: Optional[str] = None
    dietary_requirements: List[str] = []
    budget_usd: Optional[float] = None
    budget_min_usd: Optional[float] = None
    budget_max_usd: Optional[float] = None
    cuisine_preferences: List[str] = []
    service_style: Optional[str] = None
    meal_courses: List[str] = []
    beverage_options: List[str] = []
    alcohol_service: bool = False
    menu_variety: Optional[str] = None  # "minimal", "moderate", "extensive"
    indoor_outdoor: Optional[str] = None
    venue_kitchen_available: bool = True
    special_requests: Optional[str] = None
    raw_input: Optional[str] = None
    input_mode: Optional[str] = None


class MenuItem(BaseModel):
    dish_id: str
    dish_name: str
    category: str
    portions_required: int
    cost_per_portion_usd: float
    dietary_tags: List[str] = []
    supplier_id: Optional[str] = None


class MenuData(BaseModel):
    approved: bool = False
    generated_at: Optional[str] = None
    items: List[MenuItem] = []
    dietary_compliance: Dict[str, bool] = {}
    total_food_cost_usd: float = 0.0
    cost_per_head_usd: float = 0.0
    notes: str = ""
    warnings: List[str] = []


class Shortage(BaseModel):
    ingredient: str
    required: float
    available: float
    deficit: float
    severity: str
    suggested_substitute: Optional[str] = None


class ProcurementItem(BaseModel):
    ingredient: str
    quantity_required: float
    unit: str
    supplier_id: str
    supplier_name: str
    unit_price_usd: float
    total_cost_usd: float
    lead_time_hours: int
    availability: str


class InventoryData(BaseModel):
    checked_at: Optional[str] = None
    required_ingredients: Dict[str, Any] = {}
    shortages: List[Shortage] = []
    procurement_list: List[ProcurementItem] = []
    total_ingredient_cost_usd: float = 0.0
    notes: str = ""


class CostBreakdown(BaseModel):
    ingredient_cost_usd: float = 0.0
    labor_cost_usd: float = 0.0
    logistics_cost_usd: float = 0.0
    packaging_cost_usd: float = 0.0
    overhead_usd: float = 0.0
    total_cost_usd: float = 0.0


class PricingData(BaseModel):
    calculated_at: Optional[str] = None
    cost_breakdown: CostBreakdown = CostBreakdown()
    per_head_cost_usd: float = 0.0
    food_cost_percentage: float = 0.0
    suggested_price_usd: float = 0.0
    suggested_price_per_head_usd: float = 0.0
    margin_percentage: float = 0.0
    budget_feasible: bool = False
    budget_shortfall_usd: float = 0.0
    optimization_suggestions: List[Dict] = []
    notes: str = ""


class Risk(BaseModel):
    risk_id: str
    severity: str
    type: str
    description: str
    affected_component: str
    suggested_action: str
    auto_replan: bool = False


class MonitoringData(BaseModel):
    checked_at: Optional[str] = None
    overall_risk_level: str = "NONE"
    risks: List[Risk] = []
    re_plan_triggered: bool = False
    re_plan_constraints: Optional[str] = None
    final_approved: bool = False
    approval_notes: str = ""
    summary: str = ""


class AgentLogEntry(BaseModel):
    timestamp: str
    agent: str
    action: str
    output_summary: str
    status: str
    duration_ms: Optional[int] = None


class EventState(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8].upper()}")
    version: int = 1
    status: str = "created"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    customer: CustomerData = CustomerData()
    menu: MenuData = MenuData()
    inventory: InventoryData = InventoryData()
    pricing: PricingData = PricingData()
    monitoring: MonitoringData = MonitoringData()
    agent_log: List[AgentLogEntry] = []

    def log(self, agent: str, action: str, summary: str, status: str = "success", duration_ms: int = None):
        entry = AgentLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            agent=agent,
            action=action,
            output_summary=summary,
            status=status,
            duration_ms=duration_ms,
        )
        self.agent_log.append(entry)
        self.updated_at = datetime.utcnow().isoformat()
        self.version += 1
