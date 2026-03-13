# utils.py
from dateutil.parser import parse
from datetime import datetime, date
import re

# Simple keyword-based automatic category mapping
CATEGORY_KEYWORDS = {
    "salary": "Salary",
    "pay": "Salary",
    "netflix": "Subscriptions",
    "spotify": "Subscriptions",
    "uber": "Transport",
    "ola": "Transport",
    "fuel": "Transport",
    "grocer": "Groceries",
    "supermarket": "Groceries",
    "rent": "Rent",
    "movie": "Entertainment",
    "dinner": "Food",
    "lunch": "Food",
    "doctor": "Health",
    "pharma": "Health",
    "emi": "Loans",
    "loan": "Loans",
    "investment": "Investment",
    "mutual": "Investment",
    "sip": "Investment",
    "shopping": "Shopping",
    "amazon": "Shopping"
}

def guess_category_from_text(text: str, categories: list):
    text = (text or "").lower()
    for kw, cat in CATEGORY_KEYWORDS.items():
        if kw in text:
            # find matching category id/name from categories list
            for c in categories:
                if c["name"].lower() == cat.lower():
                    return c["id"]
    # fallback: 'Other'
    for c in categories:
        if c["name"].lower() == "other":
            return c["id"]
    return categories[0]["id"] if categories else None

def today_str():
    return datetime.today().strftime("%Y-%m-%d")

def parse_date(s):
    if not s:
        return today_str()
    try:
        d = parse(s)
        return d.strftime("%Y-%m-%d")
    except:
        return today_str()
