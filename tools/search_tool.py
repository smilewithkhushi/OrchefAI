import json
import os
from config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_SEARCH_INDEX

_search_client = None
if AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY:
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        _search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
        )
    except Exception as e:
        print(f"[Azure Search] Failed to connect, using local fallback: {e}")

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_local_json(filename: str) -> list[dict]:
    path = os.path.join(_DATA_DIR, filename)
    with open(path) as f:
        return json.load(f)


def search_menus(query: str, dietary_tags: list[str] = None, top: int = 10) -> list[dict]:
    """Search menu items from Azure AI Search, or local JSON fallback."""
    if _search_client:
        filter_expr = None
        if dietary_tags:
            tag_filters = " and ".join(
                [f"dietary_tags/any(t: t eq '{tag}')" for tag in dietary_tags]
            )
            filter_expr = tag_filters
        try:
            results = _search_client.search(
                search_text=query,
                filter=filter_expr,
                top=top,
                query_type="semantic",
                semantic_configuration_name="default",
            )
            return [dict(r) for r in results]
        except Exception as e:
            print(f"[Azure Search] Query failed, using local fallback: {e}")

    menus = _load_local_json("menus.json")
    query_lower = query.lower()
    results = [m for m in menus if query_lower in json.dumps(m).lower()]
    if dietary_tags:
        results = [
            m for m in results
            if all(t in m.get("dietary_tags", []) for t in dietary_tags)
        ]
    if not results:
        results = menus
        if dietary_tags:
            results = [
                m for m in results
                if all(t in m.get("dietary_tags", []) for t in dietary_tags)
            ]
    return results[:top]


def search_suppliers(ingredient: str, halal_required: bool = False) -> list[dict]:
    """Search suppliers from Azure AI Search, or local JSON fallback."""
    if _search_client:
        query_text = f"supplies {ingredient}"
        filter_expr = "halal_certified eq true" if halal_required else None
        try:
            results = _search_client.search(
                search_text=query_text,
                filter=filter_expr,
                top=5,
            )
            return [dict(r) for r in results]
        except Exception as e:
            print(f"[Azure Search] Supplier query failed, using local fallback: {e}")

    suppliers = _load_local_json("suppliers.json")
    results = [
        s for s in suppliers
        if ingredient in s.get("supplies", [])
    ]
    if halal_required:
        results = [s for s in results if s.get("halal_certified", False)]
    return results[:5]
