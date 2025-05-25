import unittest
from unittest.mock import patch, Mock
from decimal import Decimal
import requests

# Add project root to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from basescan_api import get_account_normal_transactions, get_eth_current_price

class TestBasescanAPI(unittest.TestCase):

    @patch('requests.get')
    def test_get_account_normal_transactions_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": [
                {"hash": "0x1", "from": "0xfrom1", "to": "0xto1", "value": "100"},
                {"hash": "0x2", "from": "0xfrom2", "to": "0xto2", "value": "200"}
            ]
        }
        mock_get.return_value = mock_response

        transactions = get_account_normal_transactions("dummy_api_key", "dummy_wallet_address")
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0]["hash"], "0x1")
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_account_normal_transactions_api_error(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "0",
            "message": "Error!",
            "result": "Some error message"
        }
        mock_get.return_value = mock_response

        # Suppress print warnings during this test
        with patch('builtins.print') as mock_print:
            transactions = get_account_normal_transactions("dummy_api_key", "dummy_wallet_address")
            self.assertEqual(len(transactions), 0)
            mock_print.assert_called() # Check that a warning was printed
        mock_get.assert_called_once()
        
    @patch('requests.get')
    def test_get_account_normal_transactions_no_transactions(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1", # Etherscan-like APIs often return status 1 for "no transactions"
            "message": "No transactions found",
            "result": [] 
        }
        mock_get.return_value = mock_response
        transactions = get_account_normal_transactions("dummy_api_key", "dummy_wallet_address")
        self.assertEqual(len(transactions), 0)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_account_normal_transactions_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with patch('builtins.print') as mock_print:
            transactions = get_account_normal_transactions("dummy_api_key", "dummy_wallet_address")
            self.assertEqual(len(transactions), 0)
            mock_print.assert_called()
        mock_get.assert_called_once()
        
    @patch('requests.get')
    def test_get_account_normal_transactions_json_decode_error(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("JSON decode error") # Simulate JSON decode error
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            transactions = get_account_normal_transactions("dummy_api_key", "dummy_wallet_address")
            self.assertEqual(len(transactions), 0)
            mock_print.assert_called()
        mock_get.assert_called_once()


    @patch('requests.get')
    def test_get_eth_current_price_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": {"ethusd": "2000.50"}
        }
        mock_get.return_value = mock_response

        price = get_eth_current_price("dummy_api_key")
        self.assertEqual(price, Decimal("2000.50"))
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_eth_current_price_api_error(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "0",
            "message": "Error!",
            "result": "Some error message"
        }
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            price = get_eth_current_price("dummy_api_key")
            self.assertIsNone(price)
            mock_print.assert_called()
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_eth_current_price_missing_field(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": {"other_field": "some_value"} # ethusd is missing
        }
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            price = get_eth_current_price("dummy_api_key")
            self.assertIsNone(price)
            mock_print.assert_called()
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_eth_current_price_invalid_price_value(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "message": "OK",
            "result": {"ethusd": "not_a_decimal"} 
        }
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            price = get_eth_current_price("dummy_api_key")
            self.assertIsNone(price)
            mock_print.assert_called()
        mock_get.assert_called_once()


    @patch('requests.get')
    def test_get_eth_current_price_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with patch('builtins.print') as mock_print:
            price = get_eth_current_price("dummy_api_key")
            self.assertIsNone(price)
            mock_print.assert_called()
        mock_get.assert_called_once()

if __name__ == '__main__':
    unittest.main()
