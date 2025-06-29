import os
import uuid
import requests
import json
import re
from datetime import datetime, timedelta, date
from langchain_core.tools import tool
from api.langchainAgent.context import get_current_user_info
from rapidfuzz import fuzz
import psutil

BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/")

VALID_TAGS = [
    "Salary", "Business", "Investment", "Other",
    "Transportation", "Utilities", "Entertainment",
    "Medical", "Food", "Others"
]

CATEGORIES = {
    "Food": ["food", "grocery", "supermarket", "bigbazaar", "reliance"],
    "Entertainment": ["movie", "cinema", "netflix", "hotstar", "game", "theater"],
    "Transportation": ["bus", "taxi", "uber", "ola", "train", "fuel", "petrol"],
    "Utilities": ["electricity", "water bill", "gas", "internet", "wifi"],
    "Medical": ["hospital", "doctor", "medicine", "pharmacy"],
    "Salary": ["salary", "paycheck", "monthly pay"],
    "Business": ["business", "client", "deal", "sale"],
    "Investment": ["investment", "dividend", "stock", "mutual fund", "sip"],
    "Other": ["freelance", "consulting", "misc"],
    "Others": ["other", "random", "unknown", "misc"]
}

def log_memory(stage=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024
    print(f"🔍 Memory {stage}: {mem:.2f} MB")

def generate_unique_id():
    return str(uuid.uuid4())

def auto_categorize(text: str, threshold: int = 85) -> tuple[str, int]:
    text_lower = text.lower()

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category, 100

    best_category = "Others"
    best_score = 0
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            score = fuzz.partial_ratio(text_lower, keyword)
            if score > best_score:
                best_score = score
                best_category = category
                if best_score >= threshold:
                    return best_category, best_score

    return best_category, best_score

@tool
def add_transaction(input: str) -> str:
    """
    Adds a transaction (income or expense) for the authenticated user.
    Accepts either JSON input or natural language.
    """
    log_memory("before")

    user_id, auth_token = get_current_user_info()
    if not user_id or not auth_token:
        return "❌ Cannot fetch insights. Missing user context or auth token."

    try:
        if len(input) > 1000:
            return "❌ Input too long. Please shorten the message."

        try:
            data = json.loads(input)
            transaction_type = data.get("transaction_type")
            if transaction_type not in ["expenses", "income"]:
                return "❌ 'transaction_type' must be 'expenses' or 'income'."
        except json.JSONDecodeError:
            input_lower = input.lower()
            if any(word in input_lower for word in ["spent", "paid", "bought"]):
                transaction_type = "expenses"
            elif any(word in input_lower for word in ["received", "earned", "salary"]):
                transaction_type = "income"
            else:
                return "❌ Could not determine transaction_type. Use 'spent' or 'received'."

            amount_match = re.search(r"(\d+(\.\d+)?)", input_lower)
            if not amount_match:
                return "❌ Could not detect amount. Please include a number."
            amount = float(amount_match.group())

            date_str = datetime.now().strftime("%Y-%m-%d")
            if "yesterday" in input_lower:
                date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            elif "tomorrow" in input_lower:
                date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif "last week" in input_lower:
                date_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            elif "last month" in input_lower:
                date_str = (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1).strftime("%Y-%m-%d")
            else:
                date_match = re.search(r"\d{4}-\d{2}-\d{2}", input)
                if date_match:
                    date_str = date_match.group()

            # Smart title fallback
            title_match = re.search(r"(?:for|on)\s+([\w\s]+)", input_lower)
            if title_match:
                title = title_match.group(1).strip().title()
            else:
                if "salary" in input_lower:
                    title = "Salary"
                elif "freelance" in input_lower:
                    title = "Freelance"
                elif "received" in input_lower:
                    title = "Received Payment"
                elif "earned" in input_lower:
                    title = "Earned Income"
                else:
                    title = "General Income" if transaction_type == "income" else "General Expense"

            for word in ["yesterday", "today", "tomorrow", "last week", "last month"]:
                title = title.replace(word, "").strip()

            tag, _ = auto_categorize(title)

            # Override bad fuzzy tag for income
            if transaction_type == "income":
                if "salary" in input_lower:
                    tag = "Salary"
                elif any(w in input_lower for w in ["freelance", "consulting"]):
                    tag = "Other"
                elif tag not in ["Salary", "Business", "Investment", "Other"]:
                    tag = "Other"

            data = {
                "transaction_type": transaction_type,
                "user_id": user_id,
                "title": title,
                "amount": amount,
                "tag": tag,
                "date": date_str,
                "paymentmethod": "Not specified",
                "description": ""
            }

        # Validation
        required_fields = ["user_id", "title", "amount", "date"]
        if any(field not in data for field in required_fields):
            return "❌ Missing required fields."

        data["amount"] = float(data["amount"])
        if data["amount"] <= 0:
            return "❌ Amount must be a positive number."

        parsed_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        if parsed_date > date.today():
            return "❌ Date cannot be in the future."

        if data.get("tag") not in VALID_TAGS:
            tag, _ = auto_categorize(data["title"])
            data["tag"] = tag if tag in VALID_TAGS else "Others"

        payload = {
            "Id": generate_unique_id(),
            "User": user_id,
            "Title": data["title"],
            "Amount": data["amount"],
            "Tag": data["tag"],
            "Type": transaction_type.capitalize(),
            "Date": data["date"],
            "Paymentmethod": data.get("paymentmethod", "Not specified"),
            "Description": data.get("description", "")
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        endpoint = "expenses/add/" if transaction_type == "expenses" else "income/add/"

        response = requests.post(f"{BASE_URL}/{endpoint}", headers=headers, json=payload, timeout=15)
        response.raise_for_status()

        log_memory("after")
        return f"✅ {transaction_type.capitalize()} added successfully."

    except requests.exceptions.RequestException as e:
        if "429" in str(e) or "resource" in str(e).lower():
            return "❌ Server overloaded or resource exhausted. Please try again later."
        return f"❌ Failed to add {transaction_type}: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"
