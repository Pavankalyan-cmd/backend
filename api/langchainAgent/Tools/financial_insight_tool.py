import requests
import re
import os
import logging
from datetime import datetime, timedelta
from calendar import month_name
from collections import defaultdict
from langchain_core.tools import tool
from api.langchainAgent.context import get_current_user_info


BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/")

@tool
def financial_insight(query: str) -> str:
    """
    Provides financial insights based on user's spending and income history.
    Supports queries like:
    - "Show insights for last month"
    - "What were my top expenses in March 2024?"
    - "Give insights for 2025 overall"
    - "Export financial summary for 2025 as PDF"
    """
    logger = logging.getLogger(__name__)
    logger.info(f"[FinancialInsightTool] Input query: {query}")

    user_id, auth_token = get_current_user_info()
    if not user_id or not auth_token:
        return "❌ Cannot fetch insights. Missing user context or auth token."

    headers = {"Authorization": f"Bearer {auth_token}"}

    def fetch(endpoint):
        try:
            res = requests.get(f"{BASE_URL}/{endpoint}/{user_id}/", headers=headers, timeout=120)
            if res.status_code == 401:
                return {"error": "unauthorized"}
            if res.status_code != 200:
                logger.error(f"API call failed: {res.status_code} - {res.text}")
                return {"error": f"API error: {res.status_code}"}
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    expenses = fetch("expenses")
    incomes = fetch("incomes")

    if "error" in expenses:
        return "❌ Unable to fetch expenses. Ensure you're logged in."
    if "error" in incomes:
        return "❌ Unable to fetch incomes. Ensure you're logged in."
    if not expenses and not incomes:
        return "📭 No financial records found."

    try:
        monthly_data = defaultdict(lambda: {"income": 0, "expense": 0})
        category_data = defaultdict(float)

        for item in incomes:
            try:
                date = datetime.strptime(item["Date"], "%Y-%m-%d").strftime("%Y-%m")
                monthly_data[date]["income"] += float(item["Amount"])
            except (KeyError, Exception) as e:
                logger.warning(f"Skipping income entry due to error: {e}")
                continue

        for item in expenses:
            try:
                date = datetime.strptime(item["Date"], "%Y-%m-%d").strftime("%Y-%m")
                amt = float(item["Amount"])
                monthly_data[date]["expense"] += amt
                category_data[item["Tag"]] += amt
            except (KeyError, Exception) as e:
                logger.warning(f"Skipping expense entry due to error: {e}")
                continue

        query_lower = query.lower()
        current_date = datetime.now()
        target_date = None

        # 📅 Check for yearly insight
        year_match = re.search(r"(20\d{2})", query_lower)
        if year_match and ("year" in query_lower or "overall" in query_lower or "summary" in query_lower):
            target_year = year_match.group(1)
            yearly_income = sum(float(i["Amount"]) for i in incomes if i["Date"].startswith(target_year))
            yearly_expense = sum(float(e["Amount"]) for e in expenses if e["Date"].startswith(target_year))
            yearly_savings = yearly_income - yearly_expense
            category_totals = defaultdict(float)
            for e in expenses:
                if e["Date"].startswith(target_year):
                    category_totals[e["Tag"]] += float(e["Amount"])
            top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]

            savings_rate = (yearly_savings / yearly_income * 100) if yearly_income != 0 else 0
            response = f"""
📅 **Financial Summary for {target_year}:**
- 💰 Total Income: ₹{yearly_income:,.2f}
- 💸 Total Expenses: ₹{yearly_expense:,.2f}
- 💼 Total Savings: ₹{yearly_savings:,.2f}
- 📊 Savings Rate: {savings_rate:.1f}%

📊 **Top Spending Categories:**
"""
            if top_categories:
                for tag, amt in top_categories:
                    response += f"- {tag}: ₹{amt:,.2f}\n"
            else:
                response += "- No category data available.\n"

            # PDF export functionality has been removed

            return response.strip()

        # 🗓 Handle monthly insight
        if "last month" in query_lower:
            target_date = current_date.replace(day=1) - timedelta(days=1)
        elif "this month" in query_lower or "current month" in query_lower:
            target_date = current_date
        else:
            match = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{4})?", query_lower)
            if match:
                month_name_str = match.group(1).capitalize()
                year_str = match.group(2) if match.group(2) else str(current_date.year)
                try:
                    month_num = list(month_name).index(month_name_str)
                    target_date = datetime(int(year_str), month_num, 1)
                except:
                    return f"❌ Invalid month: {month_name_str}"

        if not target_date:
            current_month_str = current_date.strftime("%Y-%m")
            valid_months = sorted([m for m in monthly_data if m <= current_month_str], reverse=True)
            if not valid_months:
                return "📭 No financial data available for any valid month."
            target_month = valid_months[0]
        else:
            target_month = target_date.strftime("%Y-%m")

        if target_month not in monthly_data or (
            monthly_data[target_month]["income"] == 0 and monthly_data[target_month]["expense"] == 0
        ):
            return f"📭 No financial records found for {target_month}."

        # Monthly Insight
        this_month = monthly_data[target_month]
        months = sorted(monthly_data.keys(), reverse=True)
        try:
            prev_index = months.index(target_month) + 1
            prev_month = monthly_data[months[prev_index]]
        except IndexError:
            prev_month = {"income": 0, "expense": 0}

        this_savings = this_month["income"] - this_month["expense"]
        prev_savings = prev_month["income"] - prev_month["expense"]
        savings_delta = this_savings - prev_savings

        # Filter top categories for this month only
        category_totals = defaultdict(float)
        for item in expenses:
            if item["Date"].startswith(target_month):
                category_totals[item["Tag"]] += float(item["Amount"])
        top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:3]

        response = f"""
📅 **Financial Insight for {target_month}:**
- 💰 Income: ₹{this_month['income']:,.2f}
- 💸 Expenses: ₹{this_month['expense']:,.2f}
- 💼 Savings: ₹{this_savings:,.2f} ({'📉 Down' if savings_delta < 0 else '📈 Up'} ₹{abs(savings_delta):,.2f} from last month)

📊 **Top Spending Categories:**
"""
        if top_categories:
            for tag, amt in top_categories:
                response += f"- {tag}: ₹{amt:,.2f}\n"
        else:
            response += "- No category data available.\n"

        response += f"\n📈 **Trend:** Compared to last month, your savings have {'decreased' if savings_delta < 0 else 'increased'}.\n"

        return response.strip()

    except Exception as e:
        return f"❌ Error generating insights: {str(e)}"
