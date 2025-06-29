import uuid
import requests
from datetime import datetime, timedelta # Import timedelta for 'yesterday'
from langchain_core.tools import tool
from django.conf import settings
from api.langchainAgent.context import get_current_user_info
import os


# IMPORTANT: Ensure BASE_URL is correctly defined, preferably from settings.
# e.g., settings.API_BASE_URL = 'http://localhost:8000/api'
BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/")


def generate_unique_id():
    return str(uuid.uuid4())


@tool
def optimize_budgets(query: str) -> str:

    """
    Analyze user's budget and provide savings suggestions.
    Use when the user wants to save money or optimize expenses.
    Example input: "I want to save ₹50,000 in 6 months."
    Do NOT use this tool for greetings, small talk, or non-financial questions.
    """

    user_id, auth_token = get_current_user_info()
    if not user_id or not auth_token:
        return "❌ Missing user authentication. Please log in."

    # Format token as per your Django/Firebase auth middleware
    headers = {"Authorization": f"Bearer {auth_token}"}

    def safe_get(url):
        try:
            response = requests.get(url, headers=headers, timeout=120)
            if response.status_code == 401:
                return {"error": "unauthorized"}
            if response.status_code >= 400:
                return {"error": f"API error {response.status_code}"}
            try:
                return response.json()
            except Exception as e:
                return {"error": f"Failed to parse JSON response: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    # Fetch data
    expenses = safe_get(f"{BASE_URL}/expenses/{user_id}/")
    income = safe_get(f"{BASE_URL}/incomes/{user_id}/")

    # Handle unauthorized
    if "error" in expenses:
        return "❌ Unauthorized access to expenses. Please check your login/token."
    if "error" in income:
        return "❌ Unauthorized access to income. Please check your login/token."

    if not income:
        return "⚠️ No income records found. Please add income data first."

    # Calculate totals
    try:
        total_income = sum(float(item["Amount"]) for item in income)
    except (KeyError, ValueError, TypeError) as e:
        return f"❌ Error parsing income data: {str(e)}"
    try:
        total_expense = sum(float(item["Amount"]) for item in expenses)
    except (KeyError, ValueError, TypeError) as e:
        return f"❌ Error parsing expense data: {str(e)}"
    savings = total_income - total_expense

    # Categorize expenses
    category_totals = {}
    for exp in expenses:
        try:
            tag = exp.get("Tag", "Other")
            category_totals[tag] = category_totals.get(tag, 0) + float(exp.get("Amount", 0))
        except (KeyError, ValueError, TypeError) as e:
            continue

    # Format response
    response = f"""
📊 **Budget Summary**:
- 💰 Total Income: ₹{total_income:,.2f}
- 💸 Total Expenses: ₹{total_expense:,.2f}
- 💼 Estimated Savings: ₹{savings:,.2f} {"❗ Overspending!" if savings < 0 else "✅"}

🔍 **Category Breakdown**:
"""
    for cat, amt in category_totals.items():
        percent = (amt / total_expense) * 100 if total_expense else 0
        warning = "⚠️" if percent > 30 else ""
        response += f"- {cat}: ₹{amt:,.2f} ({percent:.1f}%) {warning}\n"

    # Suggestions
    response += "\n💡 **Suggestions:**\n"
    if savings < 0:
        response += "- You're spending more than you earn. Cut overall expenses.\n"
    elif savings < 0.2 * total_income:
        response += "- Aim to save at least 20% of your income.\n"
    if category_totals.get("Food", 0) > 0.3 * total_expense:
        response += "- Food expenses are too high. Cut back on eating out.\n"
    if category_totals.get("Entertainment", 0) > 0.15 * total_expense:
        response += "- Reduce entertainment costs. Target below 15%.\n"

    return response.strip()
