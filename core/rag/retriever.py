import json
import os

KNOWLEDGE_PATH = "data/knowledge"

def load_knowledge(topic):
    path = os.path.join(KNOWLEDGE_PATH, topic + ".json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)

def retrieve(query, topic="diseases"):
    entries = load_knowledge(topic)
    query_lower = query.lower()
    matches = [
        e for e in entries
        if any(k.lower() in query_lower for k in e.get("keywords", []))
    ]
    if not matches:
        return "No matching records found in knowledge base."
    results = []
    for m in matches[:3]:
        results.append(m["name"] + ": " + m["description"] + " | Treatment: " + m["treatment"])
    return chr(10).join(results)