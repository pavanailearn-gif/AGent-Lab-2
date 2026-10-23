"""
Customer profile lookup service.

TODO: Participants will implement the lookup logic.
"""
import json
from typing import Any, Dict, Optional
from pathlib import Path


def load_business_data(filename: str) -> Dict[str, Any]:
    """Load business data JSON file."""
    path = Path("data/business_data") / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_customer_profile(customer_id: str) -> Dict[str, Any]:
    """
    Look up a customer's profile (identity, segment, KYC status, accounts) by ID.

    TODO: Load data/business_data/customer_profiles.json via load_business_data(),
    search its "customers" list for a matching customer_id, and return that
    customer's full profile dict. If no customer matches, return
    {"error": "Customer not found", "customer_id": customer_id} instead of raising.
    """
    data = load_business_data("customer_profiles.json")

    # TODO: search data["customers"] for customer_id and return the match,
    # or the not-found dict shape described above.
    raise NotImplementedError("Customer profile lookup not implemented")
