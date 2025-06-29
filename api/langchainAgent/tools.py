# import uuid
# import requests
# from datetime import datetime, timedelta # Import timedelta for 'yesterday'
# from langchain_core.tools import tool
# from django.conf import settings
# from api.langchainAgent.context import get_current_user_info


# # IMPORTANT: Ensure BASE_URL is correctly defined, preferably from settings.
# # It should include '/api' if your root URLConf prefixes your app's URLs with 'api/'.
# # e.g., settings.API_BASE_URL = 'http://localhost:8000/api'
# BASE_URL =  "http://localhost:8000/"


# def generate_unique_id():
#     return str(uuid.uuid4())


# @tool
# def add_transaction_tool(input: str) -> str:
#     """
#     Add a new expense or income transaction for a user.

#     Expects input as a JSON string with:
#     'transaction_type' (string, required: 'expense' or 'income'),
#     'title' (string, required),
#     'amount' (number, required),
#     'tag' (string, required),
#     'date' (string, required: YYYY-MM-DD).
#     Optionally: 'paymentmethod' (string), 'description' (string).

#     Alternatively, it can parse natural language like:
#     - "I spent 6000 on food items on 2025-05-25. 
#     - "I received 5000 for freelance work yesterday.
#     - "Earned 10000 from salary today f

#     Use this tool when the user mentions:
#     - Spending money
#     - Earning/receiving money
#     - Logging a purchase, bill, or income (e.g. 'I spent 6000 on groceries')

#     Supports both structured JSON input and natural language. Do **not** use this tool for general questions, greetings, or non-financial inputs.
#     """

#     import json, re

#     data = {} # Initialize data dictionary to be populated
#     transaction_type = None # Initialize transaction_type to be determined

#     try:
#         # First attempt: JSON input (preferred and explicit)
#         data = json.loads(input)
#         transaction_type = data.get("transaction_type")
#         if transaction_type not in ["expense", "income"]:
#             return "❌ JSON input: Missing or invalid 'transaction_type'. Must be 'expense' or 'income'."

#     except json.JSONDecodeError:
#         # Fallback: try to extract fields from natural language
#         input_lower = input.lower()

#         # --- 1. Determine transaction_type from keywords ---
#         if "spent" in input_lower or "paid" in input_lower or "bought" in input_lower:
#             transaction_type = "expense"
#         elif "received" in input_lower or "earned" in input_lower or "got" in input_lower or "salary" in input_lower or "bonus" in input_lower:
#             transaction_type = "income"
#         else:
#             return " Natural language input: Could not determine 'transaction_type' (expense/income). Please specify keywords like 'spent'/'received'."

#         try:
#             # --- 2. Extract Amount (dynamic regex based on type) ---
#             amount_pattern = r"(?:spent|paid|bought|received|earned|got)\s+(\d+(\.\d+)?)"
#             amount_match = re.search(amount_pattern, input_lower)
#             if not amount_match:
#                  amount_match = re.search(r"(\d+(\.\d+)?)\s+(?:rupees|rs)", input_lower) # Catch "5000 rupees for..."
#             if not amount_match:
#                 raise ValueError("Amount not found in natural language input.")
#             amount = float(amount_match.group(1))

#             # --- 3. Extract Tag/Title (dynamic based on type) ---
#             tag = "Uncategorized"
#             title = "Transaction"

#             if transaction_type == "expense":
#                 # Try to find "on <item>" or "for <item>" for expenses
#                 tag_match = re.search(r"(?:on|for)\s+([a-zA-Z0-9\s]+?)(?:\s+on|\.$|$)", input_lower)
#                 if tag_match:
#                     tag = tag_match.group(1).strip().capitalize()
#                     title = f"Expense on {tag}"
#                 else:
#                     title = "General Expense"
#             elif transaction_type == "income":
#                 # Try to find "for <item>" or "from <item>" for income
#                 tag_match = re.search(r"(?:for|from)\s+([a-zA-Z0-9\s]+?)(?:\s+on|\.$|$)", input_lower)
#                 if tag_match:
#                     tag = tag_match.group(1).strip().capitalize()
#                     title = f"Income from {tag}"
#                 else:
#                     title = "General Income"

#             # --- 4. Extract Date (handles YYYY-MM-DD, 'today', 'yesterday', 'last friday') ---
#             date_str = None
#             date_match = re.search(r"on\s+(\d{4}-\d{2}-\d{2})", input) # Specific YYYY-MM-DD
#             if date_match:
#                 date_str = date_match.group(1)
#             else:
#                 # Handle relative dates based on current time (Hyderabad, Telangana, India)
#                 # Assume datetime.now() reflects local time or is adjusted if needed
#                 current_date = datetime.now().date()
#                 if "today" in input_lower:
#                     date_str = current_date.strftime("%Y-%m-%d")
#                 elif "yesterday" in input_lower:
#                     date_str = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
#                 elif "last friday" in input_lower:
#                     # Calculate last Friday's date
#                     current_day_of_week = current_date.weekday() # Monday is 0, Friday is 4
#                     days_since_friday = (current_day_of_week - 4 + 7) % 7
#                     if days_since_friday == 0: # If today is Friday, "last Friday" was 7 days ago
#                         days_since_friday = 7
#                     date_str = (current_date - timedelta(days=days_since_friday)).strftime("%Y-%m-%d")
#                 # Add more relative date parsing logic here as needed (e.g., "last monday", "next week")

#             if not date_str:
#                 raise ValueError("Date not found or in invalid format (YYYY-MM-DD, 'today', 'yesterday', 'last friday' supported).")

        
#             user_id, auth_token = get_current_user_info()


#             data = {
#                 "transaction_type": transaction_type, # CRITICAL: Set transaction_type here for NL inputs
#                 "user_id": user_id,
#                 "title": title,
#                 "amount": amount,
#                 "tag": tag,
#                 "date": date_str,
#                 "paymentmethod": "Not specified", # Default if not specified in NL
#                 "description": "" # Default if not specified in NL
#             }
#         except Exception as e:
#             return f"❌ Natural language parsing failed. Error: {str(e)}. Please try a more structured phrase or JSON. Ensure amount, tag/title, date, and user_id are clear."

#     # --- Common Validation for both JSON and NL inputs ---
#     # `transaction_type` should already be determined at this point.
#     # The redundant check here is fine for robustness if needed, but primary check is above.
#     if transaction_type not in ["expense", "income"]:
#         return " Internal error: 'transaction_type' not correctly determined after parsing (should not happen if previous checks pass)."

#     required_fields = [ "title", "amount", "tag", "date"]
#     missing = [f for f in required_fields if f not in data or not data[f]]
#     if missing:
#         return f" Missing fields: {', '.join(missing)}."

#     try:
#         amount = float(data["amount"])
#         if amount <= 0:
#             return "❌ Amount must be a positive number."
#         data["amount"] = amount # Ensure float type for payload
#     except ValueError:
#         return " Amount must be a number."

#     try:
#         final_date_str = data["date"]
#         transaction_date_obj = datetime.strptime(final_date_str, "%Y-%m-%d").date()
#         current_date = datetime.now().date() # Use local current date for comparison
#         if transaction_date_obj > current_date:
#             # FIX: Make error message dynamic for expense/income
#             return f"❌ {transaction_type.capitalize()} date ({final_date_str}) cannot be in the future (Current date: {current_date.strftime('%Y-%m-%d')})."
#         data["date"] = transaction_date_obj.strftime("%Y-%m-%d") # Re-format to ensure consistency
#     except ValueError:
#         return "Date format must be YYYY-MM-DD."

#     user_id, auth_token = get_current_user_info()
#     payload = {
#         "Id": generate_unique_id(),
#         "User": user_id,
#         "Title": data["title"],
#         "Amount": data["amount"], # Use the validated float amount
#         "Tag": data["tag"],
#         "Type": transaction_type.capitalize(), # This is correct for both types
#         "Date": data["date"],
#         "Paymentmethod": data.get("paymentmethod", "Not specified"),
#         "Description": data.get("description", "") # FIX: Changed from "Others" to "" for consistency
#     }

#     # Determine the correct API endpoint based on transaction_type
#     api_endpoint = ""
#     success_message = ""
#     fail_message_prefix = ""

#     if transaction_type == "expense":
#         api_endpoint = f"{BASE_URL}/expenses/add/"
#         success_message = "Expense added successfully."
#         fail_message_prefix = "Failed to add expense"
#     elif transaction_type == "income":
#         api_endpoint = f"{BASE_URL}/income/add/"
#         success_message = "Income added successfully."
#         fail_message_prefix = "Failed to add income"

#     try:
#         response = requests.post(api_endpoint, json=payload, timeout=10)
#         response.raise_for_status()
#         # FIX: Return the dynamic success_message
#         return success_message
#     except requests.exceptions.HTTPError as http_err:
#         status_code = response.status_code if response is not None else 'N/A'
#         response_text = response.text if response is not None else 'No response text'
#         return f"{fail_message_prefix} (HTTP Error {status_code}): {http_err}. Details: {response_text}"
#     except requests.exceptions.ConnectionError as conn_err:
#         return f"{fail_message_prefix} (Connection Error): Could not connect to the API at {api_endpoint}. Please ensure the server is running. {conn_err}"
#     except requests.exceptions.Timeout as timeout_err:
#         return f"{fail_message_prefix} (Request timed out): The API took too long to respond. {timeout_err}"
#     except requests.exceptions.RequestException as req_err:
#         return f"{fail_message_prefix}: An unexpected error occurred during the request: {req_err}"
#     # FIX: Add a general Exception catch for robustness
#     except Exception as e:
#         return f"{fail_message_prefix}: An unexpected internal error occurred in the tool: {str(e)}"
    



# @tool
# def optimize_budget(query: str) -> str:

#     """
#     Analyze user's budget and provide savings suggestions.
#     Use when the user wants to save money or optimize expenses.
#     Example input: "I want to save ₹50,000 in 6 months."
#     Do NOT use this tool for greetings, small talk, or non-financial questions.
#     """
#     print(f"[🔍 optimize_budget] Received query: {query}")

#     user_id, auth_token = get_current_user_info()
#     if not user_id or not auth_token:
#         return "❌ Missing user authentication. Please log in."

#     # Format token as per your Django/Firebase auth middleware
#     headers = {"Authorization": f"Bearer {auth_token}"}

#     def safe_get(url):
#         try:
#             response = requests.get(url, headers=headers, timeout=10)
#             if response.status_code == 401:
#                 return {"error": "unauthorized"}
#             return response.json()
#         except Exception as e:
#             return {"error": str(e)}

#     # Fetch data
#     expenses = safe_get(f"{BASE_URL}/expenses/{user_id}/")
#     income = safe_get(f"{BASE_URL}/incomes/{user_id}/")

#     # Handle unauthorized
#     if "error" in expenses:
#         return "❌ Unauthorized access to expenses. Please check your login/token."
#     if "error" in income:
#         return "❌ Unauthorized access to income. Please check your login/token."

#     if not income:
#         return "⚠️ No income records found. Please add income data first."

#     # Calculate totals
#     try:
#         total_income = sum(float(item["Amount"]) for item in income)
#         total_expense = sum(float(item["Amount"]) for item in expenses)
#         savings = total_income - total_expense
#     except Exception as e:
#         return f"❌ Failed to calculate budget totals: {str(e)}"

#     # Categorize expenses
#     category_totals = {}
#     for exp in expenses:
#         tag = exp.get("Tag", "Other")
#         category_totals[tag] = category_totals.get(tag, 0) + float(exp.get("Amount", 0))

#     # Format response
#     response = f"""
# 📊 **Budget Summary**:
# - 💰 Total Income: ₹{total_income:,.2f}
# - 💸 Total Expenses: ₹{total_expense:,.2f}
# - 💼 Estimated Savings: ₹{savings:,.2f} {"❗ Overspending!" if savings < 0 else "✅"}

# 🔍 **Category Breakdown**:
# """
#     for cat, amt in category_totals.items():
#         percent = (amt / total_expense) * 100 if total_expense else 0
#         warning = "⚠️" if percent > 30 else ""
#         response += f"- {cat}: ₹{amt:,.2f} ({percent:.1f}%) {warning}\n"

#     # Suggestions
#     response += "\n💡 **Suggestions:**\n"
#     if savings < 0:
#         response += "- You're spending more than you earn. Cut overall expenses.\n"
#     elif savings < 0.2 * total_income:
#         response += "- Aim to save at least 20% of your income.\n"
#     if category_totals.get("Food", 0) > 0.3 * total_expense:
#         response += "- Food expenses are too high. Cut back on eating out.\n"
#     if category_totals.get("Entertainment", 0) > 0.15 * total_expense:
#         response += "- Reduce entertainment costs. Target below 15%.\n"

#     return response.strip()




# from langchain.tools import tool
# import requests
# from datetime import datetime
# from collections import defaultdict
# from api.langchainAgent.context import get_current_user_info


# @tool
# def financial_insight_tool(query: str) -> str:
#     """
#     Provides financial insights based on user's spending and income history.

#     Use this tool only when the user asks about:
#     - Monthly or specific time period summaries
#     - Spending, income, or savings trends
#     - Top expense categories

#     ❌ Do NOT use this tool for greetings, confirmations, or unrelated small talk.
#     """
#     print(f"[📈 FinancialInsightTool] Input query: {query}")

#     user_id, auth_token = get_current_user_info()
#     if not user_id or not auth_token:
#         return "❌ Cannot fetch insights. Missing user context or auth token."

#     headers = {"Authorization": f"Bearer {auth_token}"}

#     def fetch(endpoint):
#         try:
#             res = requests.get(f"{BASE_URL}/{endpoint}/{user_id}/", headers=headers, timeout=10)
#             if res.status_code == 401:
#                 return {"error": "unauthorized"}
#             return res.json()
#         except Exception as e:
#             return {"error": str(e)}

#     # Fetch data
#     expenses = fetch("expenses")
#     incomes = fetch("incomes")

#     if "error" in expenses:
#         return "❌ Unable to fetch expenses. Ensure you're logged in."
#     if "error" in incomes:
#         return "❌ Unable to fetch incomes. Ensure you're logged in."

#     if not expenses and not incomes:
#         return "📭 No financial records found. Please add income and expense data to get insights."

#     try:
#         from collections import defaultdict
#         import re

#         monthly_data = defaultdict(lambda: {"income": 0, "expense": 0})
#         category_data = defaultdict(float)

#         for item in incomes:
#             date = item["Date"][:7]  # YYYY-MM
#             monthly_data[date]["income"] += float(item["Amount"])

#         for item in expenses:
#             date = item["Date"][:7]
#             amt = float(item["Amount"])
#             monthly_data[date]["expense"] += amt
#             category_data[item["Tag"]] += amt

#         # Extract user-requested month if mentioned
#         month_match = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{4})", query.lower())
#         if month_match:
#             from calendar import month_name
#             month_str = month_match.group(1).capitalize()
#             year_str = month_match.group(2)
#             month_number = list(month_name).index(month_str)
#             target_month = f"{year_str}-{month_number:02d}"
#         else:
#             months = sorted(monthly_data.keys(), reverse=True)
#             target_month = months[0]

#         # ✅ Check if data exists for target month
#         if target_month not in monthly_data or (
#             monthly_data[target_month]["income"] == 0 and
#             monthly_data[target_month]["expense"] == 0
#         ):
#             return f"📭 No financial records found for {target_month}. Please add income or expenses for that month."

#         # Get previous month for comparison
#         months = sorted(monthly_data.keys(), reverse=True)
#         this_month = monthly_data[target_month]
#         try:
#             prev_index = months.index(target_month) + 1
#             prev_month = monthly_data[months[prev_index]]
#         except IndexError:
#             prev_month = {"income": 0, "expense": 0}

#         # Compute savings
#         this_savings = this_month["income"] - this_month["expense"]
#         prev_savings = prev_month["income"] - prev_month["expense"]
#         savings_delta = this_savings - prev_savings

#         # Top categories
#         top_categories = sorted(category_data.items(), key=lambda x: x[1], reverse=True)[:3]

#         response = f"""
# 📅 **Financial Insight for {target_month}:**
# - 💰 Income: ₹{this_month['income']:,.2f}
# - 💸 Expenses: ₹{this_month['expense']:,.2f}
# - 💼 Savings: ₹{this_savings:,.2f} ({'📉 Down' if savings_delta < 0 else '📈 Up'} ₹{abs(savings_delta):,.2f} from last month)

# 📊 **Top Spending Categories:**
# """
#         if top_categories:
#             for tag, amt in top_categories:
#                 response += f"- {tag}: ₹{amt:,.2f}\n"
#         else:
#             response += "- No category data available.\n"

#         response += f"\n📈 **Trend:**\nCompared to last month, your savings have {'decreased' if savings_delta < 0 else 'increased'}.\n"

#         return response.strip()

#     except Exception as e:
#         return f"❌ Error generating insights: {str(e)}"



# from langchain.tools import tool
# from api.langchainAgent.context import get_current_user_info
# import requests

# @tool
# def goal_tracker_tool(goal_amount_and_duration: str) -> str:
#     """
#     Provide personalized goal-tracking tips.
#     Use this tool when the user sets a savings goal, like "I want to save ₹50,000 in 6 months".

#     Input format (natural language): "I want to save ₹50000 in 6 months"
#     Do not  use this tool for greetings, small talk, or non-financial questions.
#     """

#     print(f"[🎯 GoalTrackerTool] Input: {goal_amount_and_duration}")
    
#     user_id, auth_token = get_current_user_info()
#     if not user_id or not auth_token:
#         return "❌ Missing user session info. Please log in."

#     headers = {"Authorization": f"Bearer {auth_token}"}

#     # Extract goal_amount and months from input string
#     import re
#     goal_match = re.search(r"₹?(\d+(?:,\d{3})*(?:\.\d{1,2})?)", goal_amount_and_duration)
#     months_match = re.search(r"in\s+(\d+)\s+month", goal_amount_and_duration, re.IGNORECASE)

#     if not goal_match or not months_match:
#         return "❌ Please provide a clear goal amount and time, e.g., 'I want to save ₹50000 in 6 months'."

#     try:
#         goal_amount = float(goal_match.group(1).replace(",", ""))
#         months = int(months_match.group(1))

#         required_monthly_saving = goal_amount / months

#         # Get user data
#         expenses = requests.get(f"{BASE_URL}/expenses/{user_id}/", headers=headers, timeout=10).json()
#         incomes = requests.get(f"{BASE_URL}/incomes/{user_id}/", headers=headers, timeout=10).json()

#         total_income = sum(float(i["Amount"]) for i in incomes)
#         total_expense = sum(float(e["Amount"]) for e in expenses)
#         current_savings = total_income - total_expense

#         savings_status = "✅ On track!" if current_savings >= required_monthly_saving else "⚠️ Behind schedule!"

#         return f"""
# 🎯 **Savings Goal Insight**:
# - 🏁 Goal: ₹{goal_amount:,.2f} in {months} months
# - 📅 Monthly Target: ₹{required_monthly_saving:,.2f}

# 📊 **Current Performance**:
# - 💰 Monthly Income: ₹{total_income:,.2f}
# - 💸 Monthly Expenses: ₹{total_expense:,.2f}
# - 💼 Current Savings: ₹{current_savings:,.2f}

# { savings_status } Try to cut unnecessary expenses or increase income to meet your goal.
# """.strip()

#     except Exception as e:
#         return f"❌ Error processing goal: {str(e)}"
