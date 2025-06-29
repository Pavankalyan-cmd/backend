import unittest
from unittest.mock import patch, MagicMock
from api.langchainAgent.Tools.optimize_budget import optimize_budgets

class TestOptimizeBudgetsTool(unittest.TestCase):

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_successful_budget(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")

        income_response = MagicMock()
        income_response.status_code = 200
        income_response.json.return_value = [{"Amount": 70000}]

        expense_response = MagicMock()
        expense_response.status_code = 200
        expense_response.json.return_value = [{"Amount": 30000, "Tag": "Food"}, {"Amount": 5000, "Tag": "Entertainment"}]

        mock_get.side_effect = [expense_response, income_response]
        result = optimize_budgets("Optimize my budget")
        self.assertIn("Total Income", result)
        self.assertIn("Food", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    def test_missing_user_context(self, mock_user_info):
        mock_user_info.return_value = (None, None)
        result = optimize_budgets("Help me save money")
        self.assertIn("❌ Missing user authentication", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_api_unauthorized(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")
        unauthorized_response = MagicMock()
        unauthorized_response.status_code = 401
        mock_get.return_value = unauthorized_response
        result = optimize_budgets("Show my budget")
        self.assertIn("❌ Unauthorized access", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_income_json_parse_error(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")
        expense_response = MagicMock()
        expense_response.status_code = 200
        expense_response.json.return_value = [{"Amount": 1000, "Tag": "Food"}]

        bad_income_response = MagicMock()
        bad_income_response.status_code = 200
        bad_income_response.json.return_value = [{"WrongField": 5000}]

        mock_get.side_effect = [expense_response, bad_income_response]
        result = optimize_budgets("Budget overview")
        self.assertIn("❌ Error parsing income data", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_expense_json_parse_error(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")
        bad_expense_response = MagicMock()
        bad_expense_response.status_code = 200
        bad_expense_response.json.return_value = [{"WrongField": 1000}]

        income_response = MagicMock()
        income_response.status_code = 200
        income_response.json.return_value = [{"Amount": 5000}]

        mock_get.side_effect = [bad_expense_response, income_response]
        result = optimize_budgets("Check budget")
        self.assertIn("❌ Error parsing expense data", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_no_income_data(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")
        expense_response = MagicMock()
        expense_response.status_code = 200
        expense_response.json.return_value = [{"Amount": 1000, "Tag": "Food"}]

        empty_income_response = MagicMock()
        empty_income_response.status_code = 200
        empty_income_response.json.return_value = []

        mock_get.side_effect = [expense_response, empty_income_response]
        result = optimize_budgets("Show my budget")
        self.assertIn("⚠️ No income records found", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_overspending_case(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")

        income_response = MagicMock()
        income_response.status_code = 200
        income_response.json.return_value = [{"Amount": 5000}]

        expense_response = MagicMock()
        expense_response.status_code = 200
        expense_response.json.return_value = [{"Amount": 6000, "Tag": "Food"}]

        mock_get.side_effect = [expense_response, income_response]
        result = optimize_budgets("Budget status")
        self.assertIn("❗ Overspending!", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_high_food_spending(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")

        income_response = MagicMock()
        income_response.status_code = 200
        income_response.json.return_value = [{"Amount": 10000}]

        expense_response = MagicMock()
        expense_response.status_code = 200
        expense_response.json.return_value = [{"Amount": 4000, "Tag": "Food"}, {"Amount": 1000, "Tag": "Other"}]

        mock_get.side_effect = [expense_response, income_response]
        result = optimize_budgets("Optimize")
        self.assertIn("Food expenses are too high", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_high_entertainment_spending(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")

        income_response = MagicMock()
        income_response.status_code = 200
        income_response.json.return_value = [{"Amount": 10000}]

        expense_response = MagicMock()
        expense_response.status_code = 200
        expense_response.json.return_value = [{"Amount": 2000, "Tag": "Entertainment"}, {"Amount": 500, "Tag": "Other"}]

        mock_get.side_effect = [expense_response, income_response]
        result = optimize_budgets("Optimize entertainment")
        self.assertIn("Reduce entertainment costs", result)

    @patch('api.langchainAgent.Tools.optimize_budget.get_current_user_info')
    @patch('api.langchainAgent.Tools.optimize_budget.requests.get')
    def test_api_500_error(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user", "fake_token")
        error_response = MagicMock()
        error_response.status_code = 500
        mock_get.return_value = error_response
        result = optimize_budgets("Check budget")
        self.assertIn("API error 500", result)

if __name__ == '__main__':
    unittest.main()
