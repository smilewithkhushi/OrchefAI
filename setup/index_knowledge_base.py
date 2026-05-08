"""
OrchefAI — Azure AI Search Knowledge Base Setup
Indexes all 4 data files into Azure AI Search.
Run: python setup/index_knowledge_base.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME", "orchefai-knowledge")

credential = AzureKeyCredential(API_KEY)
index_client = SearchIndexClient(endpoint=ENDPOINT, credential=credential)
search_client = SearchClient(endpoint=ENDPOINT, index_name=INDEX, credential=credential)


def create_index():
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="name", type=SearchFieldDataType.String),
        SearchableField(name="description", type=SearchFieldDataType.String),
        SearchableField(name="cuisine", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="document_type", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="cost_per_portion_usd", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="halal_certified", type=SearchFieldDataType.Boolean, filterable=True),
    ]

    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="name"),
            content_fields=[SemanticField(field_name="description"), SemanticField(field_name="content")],
            keywords_fields=[SemanticField(field_name="cuisine"), SemanticField(field_name="category")],
        ),
    )

    index = SearchIndex(
        name=INDEX,
        fields=fields,
        semantic_search=SemanticSearch(configurations=[semantic_config]),
    )

    index_client.create_or_update_index(index)
    print(f"Index '{INDEX}' created/updated")


def load_documents():
    docs = []
    base_path = os.path.join(os.path.dirname(__file__), "..", "data")

    with open(os.path.join(base_path, "menus.json")) as f:
        menus = json.load(f)
    for m in menus:
        docs.append({
            "id": m["id"],
            "document_type": "menu",
            "name": m["name"],
            "description": m.get("description", ""),
            "cuisine": m.get("cuisine", ""),
            "category": m.get("category", ""),
            "cost_per_portion_usd": float(m.get("cost_per_portion_usd", 0)),
            "halal_certified": "halal" in m.get("dietary_tags", []),
            "content": json.dumps(m),
        })

    with open(os.path.join(base_path, "suppliers.json")) as f:
        suppliers = json.load(f)
    for s in suppliers:
        docs.append({
            "id": s["id"],
            "document_type": "supplier",
            "name": s["name"],
            "description": f"Supplies: {', '.join(s.get('supplies', []))}. Location: {s.get('city', '')}",
            "cuisine": "",
            "category": s.get("type", ""),
            "cost_per_portion_usd": 0.0,
            "halal_certified": s.get("halal_certified", False),
            "content": json.dumps(s),
        })

    with open(os.path.join(base_path, "dietary_rules.json")) as f:
        rules = json.load(f)
    for r in rules:
        docs.append({
            "id": r["id"],
            "document_type": "dietary_rule",
            "name": r["name"],
            "description": r.get("description", ""),
            "cuisine": "",
            "category": "dietary",
            "cost_per_portion_usd": 0.0,
            "halal_certified": False,
            "content": json.dumps(r),
        })

    with open(os.path.join(base_path, "event_templates.json")) as f:
        templates = json.load(f)
    for t in templates:
        docs.append({
            "id": t["id"],
            "document_type": "event_template",
            "name": t["event_type"].replace("_", " ").title(),
            "description": t.get("description", ""),
            "cuisine": "",
            "category": "event_template",
            "cost_per_portion_usd": 0.0,
            "halal_certified": False,
            "content": json.dumps(t),
        })

    return docs


def upload_documents(docs):
    batch_size = 100
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        result = search_client.upload_documents(documents=batch)
        succeeded = sum(1 for r in result if r.succeeded)
        print(f"Uploaded batch {i // batch_size + 1}: {succeeded}/{len(batch)} documents")


if __name__ == "__main__":
    print("Setting up Azure AI Search for OrchefAI...")
    print(f"  Endpoint: {ENDPOINT}")
    print(f"  Index:    {INDEX}\n")

    create_index()
    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents total")
    print(f"  Menus:           {sum(1 for d in docs if d['document_type'] == 'menu')}")
    print(f"  Suppliers:       {sum(1 for d in docs if d['document_type'] == 'supplier')}")
    print(f"  Dietary Rules:   {sum(1 for d in docs if d['document_type'] == 'dietary_rule')}")
    print(f"  Event Templates: {sum(1 for d in docs if d['document_type'] == 'event_template')}")

    upload_documents(docs)
    print("\nAzure AI Search knowledge base ready!")
