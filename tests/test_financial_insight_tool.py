import unittest
from unittest.mock import patch, MagicMock
from api.langchainAgent.Tools.financial_insight_tool import financial_insight

class TestFinancialInsightTool(unittest.TestCase):

    @patch('api.langchainAgent.Tools.financial_insight_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.financial_insight_tool.requests.get')
    def test_yearly_insight_success(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_token")

        # Mock incomes API
        mock_income_response = MagicMock()
        mock_income_response.status_code = 200
        mock_income_response.json.return_value = [
            {"Amount": 50000, "Date": "2025-01-10"},
            {"Amount": 60000, "Date": "2025-05-15"}
        ]

        # Mock expenses API
        mock_expense_response = MagicMock()
        mock_expense_response.status_code = 200
        mock_expense_response.json.return_value = [
            {"Amount": 30000, "Date": "2025-03-05", "Tag": "Food"},
            {"Amount": 20000, "Date": "2025-07-20", "Tag": "Travel"}
        ]

        # Mock API get calls
        mock_get.side_effect = [mock_expense_response, mock_income_response]

        result = financial_insight("Show my 2025 yearly summary")
        self.assertIn("📅 **Financial Summary for 2025:**", result)
        self.assertIn("Total Income", result)
        self.assertIn("Total Expenses", result)

    @patch('api.langchainAgent.Tools.financial_insight_tool.get_current_user_info')
    def test_no_user_context(self, mock_user_info):
        mock_user_info.return_value = (None, None)
        result = financial_insight("Show my summary")
        self.assertIn("❌ Cannot fetch insights", result)

    @patch('api.langchainAgent.Tools.financial_insight_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.financial_insight_tool.requests.get')
    def test_api_unauthorized(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_token")
        mock_unauth = MagicMock()
        mock_unauth.status_code = 401
        mock_get.return_value = mock_unauth
        result = financial_insight("Show my summary")
        self.assertIn("❌ Unable to fetch expenses", result)

    @patch('api.langchainAgent.Tools.financial_insight_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.financial_insight_tool.requests.get')
    def test_invalid_month_input(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_token")
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []
        result = financial_insight("Show me insights for FooberMonth 2025")
        self.assertIn("❌ Invalid month", result)

    @patch('api.langchainAgent.Tools.financial_insight_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.financial_insight_tool.requests.get')
    def test_zero_income_division(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_token")
        mock_income_response = MagicMock()
        mock_income_response.status_code = 200
        mock_income_response.json.return_value = []  # No incomes

        mock_expense_response = MagicMock()
        mock_expense_response.status_code = 200
        mock_expense_response.json.return_value = [
            {"Amount": 5000, "Date": "2025-04-10", "Tag": "Bills"}
        ]

        mock_get.side_effect = [mock_expense_response, mock_income_response]
        result = financial_insight("Give me 2025 yearly summary")
        self.assertIn("Savings Rate: 0.0%", result)

if __name__ == '__main__':
    unittest.main()