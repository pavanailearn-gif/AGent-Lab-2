"""
Customer transaction history service.

TODO: Participants will implement the retrieval logic.
"""
import json
from typing import Any, Dict, List, Optional
from pathlib import Path


def load_business_data(filename: str) -> Dict[str, Any]:
    """Load business data JSON file."""
    path = Path("data/business_data") / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_recent_transactions(customer_id: str, limit: Optional[int] = 5) -> List[Dict[str, Any]]:
    """
    Return a customer's most recent transactions across all accounts, newest first.

    TODO: Load data/business_data/transaction_records.json via load_business_data(),
    filter its "transactions" list down to this customer_id, sort by "date"
    descending (newest first), and return at most `limit` results.
    """
    data = load_business_data("transaction_records.json")

    # TODO: filter, sort, and slice the transactions as described above.
    raise NotImplementedError("Transaction history lookup not implemented")
