import os
import json

KNOWLEDGE_PATH = "data/knowledge"

def estimate_weight_from_bcs(bcs_score: float, breed: str = "local") -> float:
    base_weights = {"local": 250, "zebu": 280, "friesian": 450, "angus": 400}
    base = base_weights.get(breed.lower(), 250)
    adjustment = (bcs_score - 3) * 30
    return round(base + adjustment, 1)

def formulate_ration(
    weight_kg: float,
    age_months: float,
    production_stage: str,
    available_feeds: list,
    budget_per_day: float = None
) -> dict:
    dm_requirement = weight_kg * 0.025
    cp_requirement = 0.12 if production_stage == "lactating" else 0.10
    me_requirement = weight_kg * 0.10

    ration = {
        "dry_matter_required_kg": round(dm_requirement, 2),
        "crude_protein_target": f"{round(cp_requirement * 100)}%",
        "metabolizable_energy_mj": round(me_requirement, 2),
        "recommended_feeds": [],
        "notes": []
    }

    if not available_feeds:
        available_feeds = ["grass", "hay", "maize bran"]

    feed_allocations = {
        "grass": {"dm_fraction": 0.5, "cost_per_kg": 0},
        "hay": {"dm_fraction": 0.3, "cost_per_kg": 20},
        "maize bran": {"dm_fraction": 0.15, "cost_per_kg": 35},
        "cotton seed cake": {"dm_fraction": 0.1, "cost_per_kg": 80},
        "urea": {"dm_fraction": 0.01, "cost_per_kg": 150},
        "salt": {"dm_fraction": 0.005, "cost_per_kg": 50}
    }

    total_cost = 0
    for feed in available_feeds:
        feed_lower = feed.lower()
        if feed_lower in feed_allocations:
            info = feed_allocations[feed_lower]
            amount_kg = round(dm_requirement * info["dm_fraction"], 2)
            cost = round(amount_kg * info["cost_per_kg"], 2)
            total_cost += cost
            ration["recommended_feeds"].append({
                "feed": feed,
                "amount_kg_per_day": amount_kg,
                "estimated_cost": cost
            })

    ration["total_daily_cost"] = round(total_cost, 2)

    if production_stage == "lactating":
        ration["notes"].append("Increase concentrate by 0.5kg per litre of milk produced")
    if age_months < 12:
        ration["notes"].append("Young stock - ensure adequate protein for growth")
    if budget_per_day and total_cost > budget_per_day:
        ration["notes"].append(f"Cost exceeds budget. Consider substituting with cheaper local feeds.")

    ration["disclaimer"] = "Feed formulation is advisory only. Consult a nutritionist for precise rations."
    return ration