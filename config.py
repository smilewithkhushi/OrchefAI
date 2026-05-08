import os
from dotenv import load_dotenv
from openai import OpenAI

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
COST_PROFILES = {
    "singapore": {
        "label": "Singapore",
        "staff_cost_per_event_usd": 25.0,
        "logistics_cost_per_km_usd": 1.50,
        "packaging_cost_per_guest_usd": 1.50,
        "default_distance_km": 15,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.20,
        "currency_note": "SGD converted at ~0.75 USD",
    },
    "india": {
        "label": "India",
        "staff_cost_per_event_usd": 8.0,
        "logistics_cost_per_km_usd": 0.40,
        "packaging_cost_per_guest_usd": 0.50,
        "default_distance_km": 20,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.20,
        "currency_note": "INR converted at ~0.012 USD",
    },
    "usa": {
        "label": "United States",
        "staff_cost_per_event_usd": 35.0,
        "logistics_cost_per_km_usd": 2.50,
        "packaging_cost_per_guest_usd": 2.00,
        "default_distance_km": 25,
        "overhead_percentage": 0.12,
        "min_margin_percentage": 0.20,
        "currency_note": "USD",
    },
    "uk": {
        "label": "United Kingdom",
        "staff_cost_per_event_usd": 32.0,
        "logistics_cost_per_km_usd": 2.20,
        "packaging_cost_per_guest_usd": 1.80,
        "default_distance_km": 20,
        "overhead_percentage": 0.12,
        "min_margin_percentage": 0.20,
        "currency_note": "GBP converted at ~1.27 USD",
    },
    "uae": {
        "label": "UAE / Middle East",
        "staff_cost_per_event_usd": 22.0,
        "logistics_cost_per_km_usd": 1.20,
        "packaging_cost_per_guest_usd": 1.80,
        "default_distance_km": 20,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.20,
        "currency_note": "AED converted at ~0.27 USD",
    },
    "default": {
        "label": "Global Default",
        "staff_cost_per_event_usd": 20.0,
        "logistics_cost_per_km_usd": 1.50,
        "packaging_cost_per_guest_usd": 1.50,
        "default_distance_km": 20,
        "overhead_percentage": 0.10,
        "min_margin_percentage": 0.20,
        "currency_note": "USD (global average rates)",
    },
}

REGION_KEYWORDS = {
    "singapore": ["singapore", "sg", "marina bay", "raffles", "orchard", "changi"],
    "india": ["india", "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata", "pune", "jaipur"],
    "usa": ["usa", "us", "united states", "new york", "los angeles", "chicago", "san francisco", "miami", "texas", "california", "manhattan"],
    "uk": ["uk", "united kingdom", "london", "manchester", "birmingham", "edinburgh", "england", "scotland"],
    "uae": ["uae", "dubai", "abu dhabi", "sharjah", "doha", "qatar", "riyadh", "saudi", "middle east"],
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


def _get_client() -> OpenAI:
    return OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)


async def call_agent(system_prompt: str, user_message: str, model_key: str) -> str:
    """Call an LLM agent via NVIDIA NIM (OpenAI-compatible API)."""
    model = AGENT_MODELS[model_key]
    print(f"[OrchefAI] Calling {model_key} agent ({model})...", flush=True)
    client = _get_client()
    try:
        response = client.chat.completions.create(
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
