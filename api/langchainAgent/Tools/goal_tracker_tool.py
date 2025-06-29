import uuid
import requests
from datetime import datetime, timedelta # Import timedelta for 'yesterday'
from langchain_core.tools import tool
from django.conf import settings
from api.langchainAgent.context import get_current_user_info
from langchain.tools import tool
import os
import logging


# IMPORTANT: Ensure BASE_URL is correctly defined, preferably from settings.
# It should include '/api' if your root URLConf prefixes your app's URLs with 'api/'.
# e.g., settings.API_BASE_URL = 'http://localhost:8000/api'
BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/")


def generate_unique_id():
    return str(uuid.uuid4())


@tool
def goal_tracker(goal_amount_and_duration: str) -> str:
    """
    Provide personalized goal-tracking tips.
    Use this tool when the user sets a savings goal, like "I want to save ₹50,000 in 6 months".

    Input format (natural language): "I want to save ₹50000 in 6 months"
    Do not  use this tool for greetings, small talk, or non-financial questions.
    """

    logger = logging.getLogger(__name__)
    logger.info(f"[GoalTrackerTool] Input: {goal_amount_and_duration}")
    
    user_id, auth_token = get_current_user_info()
    if not user_id or not auth_token:
        return "❌ Missing user session info. Please log in."

    headers = {"Authorization": f"Bearer {auth_token}"}

    # Extract goal_amount and months from input string
    import re
    goal_match = re.search(r"₹?(\d+(?:,\d{3})*(?:\.\d{1,2})?)", goal_amount_and_duration)
    months_match = re.search(r"in\s+(\d+)\s+month", goal_amount_and_duration, re.IGNORECASE)

    if not goal_match or not months_match:
        return "❌ Please provide a clear goal amount and time, e.g., 'I want to save ₹50000 in 6 months'."

    try:
        goal_amount = float(goal_match.group(1).replace(",", ""))
        months = int(months_match.group(1))

        required_monthly_saving = goal_amount / months

        # Get user data
        expenses_res = requests.get(f"{BASE_URL}/expenses/{user_id}/", headers=headers, timeout=120)
        if expenses_res.status_code != 200:
            logger.error(f"Failed to fetch expenses: {expenses_res.status_code} - {expenses_res.text}")
            return f"❌ Error fetching expenses: {expenses_res.status_code}"
        expenses = expenses_res.json()

        incomes_res = requests.get(f"{BASE_URL}/incomes/{user_id}/", headers=headers, timeout=30)
        if incomes_res.status_code != 200:
            logger.error(f"Failed to fetch incomes: {incomes_res.status_code} - {incomes_res.text}")
            return f"❌ Error fetching incomes: {incomes_res.status_code}"
        incomes = incomes_res.json()

        total_income = sum(float(i["Amount"]) for i in incomes)
        total_expense = sum(float(e["Amount"]) for e in expenses)
        current_savings = total_income - total_expense

        savings_status = "✅ On track!" if current_savings >= required_monthly_saving else "⚠️ Behind schedule!"

        return f"""
🎯 **Savings Goal Insight**:
- 🏁 Goal: ₹{goal_amount:,.2f} in {months} months
- 📅 Monthly Target: ₹{required_monthly_saving:,.2f}

📊 **Current Performance**:
- 💰 Monthly Income: ₹{total_income:,.2f}
- 💸 Monthly Expenses: ₹{total_expense:,.2f}
- 💼 Current Savings: ₹{current_savings:,.2f}

{ savings_status } Try to cut unnecessary expenses or increase income to meet your goal.
""".strip()

    except Exception as e:
        logger.exception(f"Exception in goal_tracker: {e}")
        return f"❌ Error processing goal: {str(e)}"
