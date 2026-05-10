import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# NVIDIA NIM
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")


AGENT_MODELS = {
    "orchestrator": "nvidia/nemotron-4-340b-instruct",
    "intake": "meta/llama-3.1-70b-instruct",
    "menu": "meta/llama-3.1-70b-instruct",
    "inventory": "meta/llama-3.1-8b-instruct",
    "pricing": "meta/llama-3.1-8b-instruct",
    "monitoring": "meta/llama-3.1-70b-instruct",
}

# Azure AI Search
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME", "orchefai-knowledge")

# Azure Cosmos DB
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "orchefai")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "events")

# Region-based cost profiles (all monetary values in USD)
# staff_hourly_rate_usd: average hourly wage for catering staff in that region
COST_PROFILES = {
    "singapore": {
        "label": "Singapore",
        "staff_hourly_rate_usd": 12.0,
        "logistics_cost_per_km_usd": 1.50,
        "packaging_cost_per_guest_usd": 1.50,
        "default_distance_km": 15,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.30,
        "currency_note": "SGD converted at ~0.75 USD",
    },
    "india": {
        "label": "India",
        "staff_hourly_rate_usd": 2.50,
        "logistics_cost_per_km_usd": 0.40,
        "packaging_cost_per_guest_usd": 0.50,
        "default_distance_km": 20,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.30,
        "currency_note": "INR converted at ~0.012 USD",
    },
    "usa": {
        "label": "United States",
        "staff_hourly_rate_usd": 22.0,
        "logistics_cost_per_km_usd": 2.50,
        "packaging_cost_per_guest_usd": 2.00,
        "default_distance_km": 25,
        "overhead_percentage": 0.12,
        "min_margin_percentage": 0.30,
        "currency_note": "USD",
    },
    "uk": {
        "label": "United Kingdom",
        "staff_hourly_rate_usd": 17.0,
        "logistics_cost_per_km_usd": 2.20,
        "packaging_cost_per_guest_usd": 1.80,
        "default_distance_km": 20,
        "overhead_percentage": 0.12,
        "min_margin_percentage": 0.30,
        "currency_note": "GBP converted at ~1.27 USD",
    },
    "uae": {
        "label": "UAE / Middle East",
        "staff_hourly_rate_usd": 10.0,
        "logistics_cost_per_km_usd": 1.20,
        "packaging_cost_per_guest_usd": 1.80,
        "default_distance_km": 20,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.30,
        "currency_note": "AED converted at ~0.27 USD",
    },
    "australia": {
        "label": "Australia",
        "staff_hourly_rate_usd": 19.0,
        "logistics_cost_per_km_usd": 2.00,
        "packaging_cost_per_guest_usd": 1.80,
        "default_distance_km": 20,
        "overhead_percentage": 0.12,
        "min_margin_percentage": 0.30,
        "currency_note": "AUD converted at ~0.65 USD",
    },
    "europe": {
        "label": "Europe",
        "staff_hourly_rate_usd": 16.0,
        "logistics_cost_per_km_usd": 2.00,
        "packaging_cost_per_guest_usd": 1.60,
        "default_distance_km": 20,
        "overhead_percentage": 0.12,
        "min_margin_percentage": 0.30,
        "currency_note": "EUR converted at ~1.09 USD",
    },
    "southeast_asia": {
        "label": "Southeast Asia",
        "staff_hourly_rate_usd": 5.0,
        "logistics_cost_per_km_usd": 0.80,
        "packaging_cost_per_guest_usd": 0.80,
        "default_distance_km": 15,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.30,
        "currency_note": "Local currency converted to USD",
    },
    "default": {
        "label": "Global Default",
        "staff_hourly_rate_usd": 12.0,
        "logistics_cost_per_km_usd": 1.50,
        "packaging_cost_per_guest_usd": 1.50,
        "default_distance_km": 20,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.30,
        "currency_note": "USD (global average rates)",
    },
}

REGION_KEYWORDS = {
    "singapore": ["singapore", "sg", "marina bay", "raffles", "orchard", "changi"],
    "india": ["india", "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata", "pune", "jaipur", "noida", "gurgaon", "gurugram", "lucknow", "ahmedabad", "goa", "cochin", "kochi", "chandigarh", "indore", "surat", "nagpur"],
    "usa": ["usa", "us", "united states", "new york", "los angeles", "chicago", "san francisco", "miami", "texas", "california", "manhattan", "boston", "seattle", "washington", "atlanta", "denver", "houston", "dallas"],
    "uk": ["uk", "united kingdom", "london", "manchester", "birmingham", "edinburgh", "england", "scotland", "liverpool", "bristol", "oxford", "cambridge"],
    "uae": ["uae", "dubai", "abu dhabi", "sharjah", "doha", "qatar", "riyadh", "saudi", "middle east", "bahrain", "kuwait", "oman", "muscat", "jeddah"],
    "australia": ["australia", "sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra", "auckland", "new zealand"],
    "europe": ["france", "paris", "germany", "berlin", "munich", "italy", "rome", "milan", "spain", "madrid", "barcelona", "amsterdam", "netherlands", "zurich", "switzerland", "vienna", "austria", "brussels", "belgium", "lisbon", "portugal"],
    "southeast_asia": ["malaysia", "kuala lumpur", "thailand", "bangkok", "indonesia", "jakarta", "bali", "vietnam", "hanoi", "ho chi minh", "philippines", "manila", "cambodia"],
}


def get_cost_profile(venue: str | None) -> dict:
    """Return the cost profile matching the venue location, or default."""
    if not venue:
        return COST_PROFILES["default"]
    venue_lower = venue.lower()
    for region, keywords in REGION_KEYWORDS.items():
        if any(kw in venue_lower for kw in keywords):
            return COST_PROFILES[region]
    return COST_PROFILES["default"]


# Staffing ratios: guests per 1 staff member
STAFFING_RATIOS = {
    "buffet":              {"servers": 25, "chefs": 40},
    "plated":              {"servers": 10, "chefs": 30},
    "family_style":        {"servers": 15, "chefs": 35},
    "cocktail_pass":       {"servers": 15, "chefs": 35},
    "food_stations":       {"servers": 20, "chefs": 30},
}

# Typical event duration in hours by event type
EVENT_DURATION_HOURS = {
    "wedding": 8,
    "gala_dinner": 6,
    "corporate_lunch": 4,
    "conference": 5,
    "birthday_party": 5,
    "cocktail_reception": 3,
    "baby_shower": 4,
    "engagement_party": 5,
    "anniversary": 5,
    "graduation_party": 4,
    "festival_/_cultural": 6,
    "charity_event": 5,
    "product_launch": 4,
    "team_building": 5,
}


def calculate_staffing(
    guest_count: int,
    service_style: str | None,
    event_type: str | None,
    venue: str | None,
    event_duration_hours: float | None = None,
) -> dict:
    """Calculate staff count and total labor cost based on event parameters.

    Returns dict with staff_count, event_hours, hourly_rate, total_labor_cost_usd,
    and a breakdown of roles.
    """
    style = service_style or "buffet"
    ratios = STAFFING_RATIOS.get(style, STAFFING_RATIOS["buffet"])

    import math
    servers = max(2, math.ceil(guest_count / ratios["servers"]))
    chefs = max(1, math.ceil(guest_count / ratios["chefs"]))
    head_chef = 1
    supervisor = 1
    dishwashers = max(1, math.ceil(guest_count / 50))

    total_staff = servers + chefs + head_chef + supervisor + dishwashers

    event_hours = event_duration_hours or EVENT_DURATION_HOURS.get(event_type, 5)

    cost_profile = get_cost_profile(venue)
    hourly_rate = cost_profile["staff_hourly_rate_usd"]

    total_labor_cost = round(total_staff * event_hours * hourly_rate, 2)

    return {
        "staff_count": total_staff,
        "breakdown": {
            "servers": servers,
            "chefs": chefs,
            "head_chef": head_chef,
            "supervisor": supervisor,
            "dishwashers": dishwashers,
        },
        "event_hours": event_hours,
        "hourly_rate_usd": hourly_rate,
        "total_labor_cost_usd": total_labor_cost,
        "region": cost_profile["label"],
    }


_async_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
    return _async_client


async def call_agent(system_prompt: str, user_message: str, model_key: str) -> str:
    """Call an LLM agent via NVIDIA NIM (async, connection-reusing)."""
    model = AGENT_MODELS[model_key]
    print(f"[OrchefAI] Calling {model_key} agent ({model})...", flush=True)
    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        result = response.choices[0].message.content
        print(f"[OrchefAI] {model_key} agent responded ({len(result)} chars)", flush=True)
        return result
    except Exception as e:
        print(f"[OrchefAI] ERROR in {model_key} agent: {e}", flush=True)
        raise


async def stream_agent(system_prompt: str, user_message: str, model_key: str):
    """Yield content chunks as they stream from the LLM."""
    model = AGENT_MODELS[model_key]
    print(f"[OrchefAI] Streaming {model_key} agent ({model})...", flush=True)
    client = _get_client()
    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=4096,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
