import unittest
import json
from unittest.mock import patch, MagicMock
from api.langchainAgent.Tools.add_transaction_tool import add_transaction

class TestAddTransactionTool(unittest.TestCase):

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.add_transaction_tool.requests.post')
    def test_add_transaction_json_expense_success(self, mock_post, mock_user_info):
        # Mock user info
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")

        # Mock API POST response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        input_json = json.dumps({
            "transaction_type": "expense",
            "user_id": "test_user_id",
            "title": "Test Expense",
            "amount": 1000,
            "tag": "Food",
            "date": "2025-06-27"
        })

        result = add_transaction(input_json)
        self.assertIn("✅ Expenses added successfully.", result)

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    def test_add_transaction_missing_user_info(self, mock_user_info):
        mock_user_info.return_value = (None, None)

        input_json = json.dumps({
            "transaction_type": "expense",
            "user_id": "test_user_id",
            "title": "Test Expense",
            "amount": 1000,
            "tag": "Food",
            "date": "2025-06-27"
        })
        result = add_transaction(input_json)
        self.assertIn("❌ Cannot add transaction", result)

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.add_transaction_tool.requests.post')
    def test_add_transaction_api_failure(self, mock_post, mock_user_info):
        
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")

        # Mock API error
        mock_post.side_effect = Exception("Server error")
        input_json = json.dumps({
            "transaction_type": "expense",
            "user_id": "test_user_id",
            "title": "Test Expense",
            "amount": 1000,
            "tag": "Food",
            "date": "2025-06-27"
        })
        result = add_transaction(input_json)
        self.assertIn("❌ Failed to add transaction", result)

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    @patch('api.langchainAgent.Tools.add_transaction_tool.requests.post')
    def test_add_transaction_natural_language(self, mock_post, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        input_text = "I spent 600 on groceries yesterday."
        result = add_transaction(input_text)
        self.assertIn("✅ Expenses added successfully.", result)  # Note: your tool returns 'Expenses' for NLP paths

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    def test_add_transaction_invalid_json(self, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")
        invalid_json_input = "{ this is bad json }"
        result = add_transaction(invalid_json_input)
        self.assertIn("❌ Could not determine transaction_type", result)

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    def test_add_transaction_missing_required_fields(self, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")
        incomplete_json = json.dumps({
            "transaction_type": "expense",
            "user_id": "test_user_id"
            # Missing title, amount, date
        })
        result = add_transaction(incomplete_json)
        self.assertIn("❌ Missing required fields.", result)

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    def test_add_transaction_negative_amount(self, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")
        input_json = json.dumps({
            "transaction_type": "expense",
            "user_id": "test_user_id",
            "title": "Test Expense",
            "amount": -500,
            "tag": "Food",
            "date": "2025-06-27"
        })
        result = add_transaction(input_json)
        self.assertIn("❌ Amount must be a positive number.", result)

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    def test_add_transaction_invalid_date(self, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")
        input_json = json.dumps({
            "transaction_type": "expense",
            "user_id": "test_user_id",
            "title": "Test Expense",
            "amount": 500,
            "tag": "Food",
            "date": "2025/06/27"
        })
        result = add_transaction(input_json)
        self.assertIn("❌ Date must be in YYYY-MM-DD format.", result)

    @patch('api.langchainAgent.Tools.add_transaction_tool.get_current_user_info')
    def test_add_transaction_invalid_transaction_type(self, mock_user_info):
        mock_user_info.return_value = ("test_user_id", "fake_auth_token")
        input_json = json.dumps({
            "transaction_type": "invalid_type",
            "user_id": "test_user_id",
            "title": "Test Expense",
            "amount": 500,
            "tag": "Food",
            "date": "2025-06-27"
        })
        result = add_transaction(input_json)
        self.assertIn("❌ JSON input: 'transaction_type' must be", result)

if __name__ == '__main__':
    unittest.main()