"""Customer profile lookup service - REFERENCE SOLUTION"""
import json
from typing import Any, Dict, Optional
from pathlib import Path


def load_business_data(filename: str) -> Dict[str, Any]:
    """Load business data JSON file."""
    path = Path("data/business_data") / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_customer_profile(customer_id: str) -> Dict[str, Any]:
    """Look up a customer's profile (identity, segment, KYC status, accounts) by ID."""
    data = load_business_data("customer_profiles.json")
    customers = data.get("customers", [])

    for customer in customers:
        if customer.get("customer_id") == customer_id:
            return customer

    return {"error": "Customer not found", "customer_id": customer_id}
