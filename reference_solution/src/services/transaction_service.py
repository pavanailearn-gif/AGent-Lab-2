"""Customer transaction history service - REFERENCE SOLUTION"""
import json
from typing import Any, Dict, List, Optional
from pathlib import Path


def load_business_data(filename: str) -> Dict[str, Any]:
    """Load business data JSON file."""
    path = Path("data/business_data") / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_recent_transactions(customer_id: str, limit: Optional[int] = 5) -> List[Dict[str, Any]]:
    """Return a customer's most recent transactions across all accounts, newest first."""
    data = load_business_data("transaction_records.json")
    transactions = [t for t in data.get("transactions", []) if t.get("customer_id") == customer_id]

    transactions.sort(key=lambda t: t.get("date", ""), reverse=True)

    return transactions[:limit]
