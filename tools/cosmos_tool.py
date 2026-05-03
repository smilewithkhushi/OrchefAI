import json
from models.event_state import EventState
from config import COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE, COSMOS_CONTAINER

_in_memory_store: dict[str, dict] = {}

_container = None
if COSMOS_ENDPOINT and COSMOS_KEY:
    try:
        from azure.cosmos import CosmosClient
        _client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
        _db = _client.get_database_client(COSMOS_DATABASE)
        _container = _db.get_container_client(COSMOS_CONTAINER)
    except Exception as e:
        print(f"[CosmosDB] Failed to connect, using in-memory store: {e}")


def save_event_state(state: EventState) -> bool:
    """Persist EventState to Cosmos DB, or in-memory if Cosmos is unavailable."""
    try:
        doc = json.loads(state.model_dump_json())
        if _container:
            doc["id"] = state.event_id
            _container.upsert_item(doc)
        else:
            _in_memory_store[state.event_id] = doc
        return True
    except Exception as e:
        print(f"[CosmosDB Error] Failed to save: {e}")
        return False


def load_event_state(event_id: str) -> EventState | None:
    """Load EventState from Cosmos DB, or in-memory if Cosmos is unavailable."""
    try:
        if _container:
            from azure.cosmos import exceptions
            try:
                doc = _container.read_item(item=event_id, partition_key=event_id)
                return EventState(**doc)
            except exceptions.CosmosResourceNotFoundError:
                return None
        else:
            doc = _in_memory_store.get(event_id)
            return EventState(**doc) if doc else None
    except Exception as e:
        print(f"[CosmosDB Error] Failed to load: {e}")
        return None
