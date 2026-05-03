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

# Cost constants (USD, Singapore market)
STAFF_COST_PER_EVENT_USD = 25.0
LOGISTICS_COST_PER_KM_USD = 1.50
PACKAGING_COST_PER_GUEST_USD = 1.50
DEFAULT_DISTANCE_KM = 15
OVERHEAD_PERCENTAGE = 0.10
MIN_MARGIN_PERCENTAGE = 0.20


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
