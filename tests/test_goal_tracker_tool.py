import unittest
from unittest.mock import patch, MagicMock
from api.langchainAgent.Tools.goal_tracker_tool import goal_tracker

class TestGoalTrackerTool(unittest.TestCase):

    @patch('api.langchainAgent.Tools.goal_tracker_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.goal_tracker_tool.requests.get')
    def test_goal_tracker_success(self, mock_get, mock_user_info):
        # Mock user info
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")

        # Mock Expenses API response
        mock_expenses_response = MagicMock()
        mock_expenses_response.status_code = 200
        mock_expenses_response.json.return_value = [
            {"Amount": "1000"},
            {"Amount": "2000"}
        ]

        # Mock Incomes API response
        mock_incomes_response = MagicMock()
        mock_incomes_response.status_code = 200
        mock_incomes_response.json.return_value = [
            {"Amount": "5000"},
            {"Amount": "3000"}
        ]

        # Arrange API call order: expenses first, then incomes
        mock_get.side_effect = [mock_expenses_response, mock_incomes_response]

        # Test input string (simulating user message)
        input_query = "I want to save ₹12000 in 6 months"

        # Call the function
        result = goal_tracker(input_query)

        # Assert expected strings in the output
        self.assertIn("🎯 **Savings Goal Insight**", result)
        self.assertIn("-- 📅 Monthly Target: ₹2,000.00", result)  # 12000 / 6 = 2000
        self.assertIn("-- 💰 Monthly Income:", result)
        self.assertIn("-- 💸 Monthly Expenses:", result)

    @patch('api.langchainAgent.Tools.goal_tracker_tool.get_current_user_info')
    def test_goal_tracker_missing_user_info(self, mock_user_info):
        # Simulate missing user session
        mock_user_info.return_value = (None, None)
        result = goal_tracker("I want to save ₹12000 in 6 months")
        self.assertIn("❌ Missing user session info", result)

    @patch('api.langchainAgent.Tools.goal_tracker_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.goal_tracker_tool.requests.get')
    def test_goal_tracker_api_failure(self, mock_get, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")

        # Simulate API returning 500 error
        failed_response = MagicMock()
        failed_response.status_code = 500
        failed_response.text = "Server error"

        # Simulate API failure on expenses call
        mock_get.side_effect = [failed_response]

        result = goal_tracker("I want to save ₹12000 in 6 months")
        self.assertIn("❌ Error fetching expenses", result)

if __name__ == '__main__':
    unittest.main()