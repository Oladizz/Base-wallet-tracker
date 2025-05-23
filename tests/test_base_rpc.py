import unittest
from unittest.mock import patch, MagicMock # Changed from Mock to MagicMock for w3 instance
from decimal import Decimal
from web3.exceptions import ProviderConnectionError
from requests.exceptions import ConnectionError as RequestsConnectionError


# Add project root to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from base_rpc import get_current_base_l2_gas_price

class TestBaseRPC(unittest.TestCase):

    @patch('base_rpc.Web3') # Patch Web3 in the context of the base_rpc module
    def test_get_current_base_l2_gas_price_success(self, mock_web3_constructor):
        # Mock the Web3 instance and its methods
        mock_w3_instance = MagicMock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.gas_price = 10 * 10**9  # 10 Gwei in Wei
        
        # Configure the constructor to return our mocked instance
        mock_web3_constructor.return_value = mock_w3_instance

        rpc_url = "http://dummy-rpc-url.com"
        gas_price_gwei = get_current_base_l2_gas_price(rpc_url)

        self.assertIsNotNone(gas_price_gwei)
        self.assertEqual(gas_price_gwei, Decimal("10")) # Expected 10 Gwei
        mock_web3_constructor.assert_called_once_with(mock_web3_constructor.HTTPProvider(rpc_url))
        mock_w3_instance.is_connected.assert_called_once()
        # self.assertTrue(mock_w3_instance.eth.gas_price.called) # Not directly callable, it's an attribute

    @patch('base_rpc.Web3')
    def test_get_current_base_l2_gas_price_connection_failed(self, mock_web3_constructor):
        mock_w3_instance = MagicMock()
        mock_w3_instance.is_connected.return_value = False # Simulate connection failure
        mock_web3_constructor.return_value = mock_w3_instance

        rpc_url = "http://dummy-rpc-url.com"
        with patch('builtins.print') as mock_print:
            gas_price_gwei = get_current_base_l2_gas_price(rpc_url)
            self.assertIsNone(gas_price_gwei)
            mock_print.assert_called_with(f"Error: Could not connect to Base RPC URL: {rpc_url}")
        mock_web3_constructor.assert_called_once_with(mock_web3_constructor.HTTPProvider(rpc_url))

    @patch('base_rpc.Web3')
    def test_get_current_base_l2_gas_price_provider_connection_error(self, mock_web3_constructor):
        # Simulate Web3 constructor raising ProviderConnectionError
        mock_web3_constructor.side_effect = ProviderConnectionError("RPC connection error")

        rpc_url = "http://dummy-rpc-url.com"
        with patch('builtins.print') as mock_print:
            gas_price_gwei = get_current_base_l2_gas_price(rpc_url)
            self.assertIsNone(gas_price_gwei)
            mock_print.assert_called_with(f"Error connecting to Base RPC provider at {rpc_url}: RPC connection error")

    @patch('base_rpc.Web3')
    def test_get_current_base_l2_gas_price_requests_connection_error(self, mock_web3_constructor):
        # Simulate HTTPProvider raising RequestsConnectionError
        mock_http_provider = MagicMock()
        mock_http_provider.side_effect = RequestsConnectionError("Network issue")
        mock_web3_constructor.HTTPProvider.return_value = mock_http_provider
        # Make the Web3 constructor itself raise the error when it tries to use the provider
        mock_web3_constructor.side_effect = RequestsConnectionError("Network issue on constructor")


        rpc_url = "http://dummy-rpc-url.com"
        # This test setup is a bit tricky. If HTTPProvider itself fails during init, Web3() might fail.
        # Or if Web3() succeeds but is_connected() or eth.gas_price fails due to it.
        # Let's assume the error happens during the Web3() call due to provider init issues.
        with patch('builtins.print') as mock_print:
            gas_price_gwei = get_current_base_l2_gas_price(rpc_url)
            self.assertIsNone(gas_price_gwei)
            # The error message might vary slightly based on where exactly it's caught.
            # The current implementation catches ProviderConnectionError first if Web3 init fails that way,
            # or RequestsConnectionError if it's raised by the constructor directly.
            # If the constructor raises RequestsConnectionError, the message will be:
            # "Network error while trying to connect to Base RPC URL {rpc_url}: Network issue on constructor"
            # If it raises ProviderConnectionError (e.g. if RequestsConnectionError is wrapped), it's different.
            # The current code in base_rpc.py has a specific catch for ProviderConnectionError.
            # Let's refine this test to specifically target the RequestsConnectionError during the Web3() call.
            # This requires the constructor itself to raise it or be wrapped.
            # Given the current try-except block, ProviderConnectionError is more likely if it's an init issue.

            # Re-simulate: HTTPProvider init is fine, but a method call on w3 fails with RequestsConnectionError
            mock_w3_instance = MagicMock()
            mock_w3_instance.is_connected.side_effect = RequestsConnectionError("Network issue during is_connected")
            mock_web3_constructor.return_value = mock_w3_instance
            mock_web3_constructor.side_effect = None # Reset side_effect for constructor

            gas_price_gwei = get_current_base_l2_gas_price(rpc_url) # Call again with new mock setup
            self.assertIsNone(gas_price_gwei)
            mock_print.assert_any_call(f"Network error while trying to connect to Base RPC URL {rpc_url}: Network issue during is_connected")


    @patch('base_rpc.Web3')
    def test_get_current_base_l2_gas_price_generic_exception(self, mock_web3_constructor):
        mock_w3_instance = MagicMock()
        mock_w3_instance.is_connected.return_value = True
        mock_w3_instance.eth.gas_price = "should_be_int_but_is_str" # This would cause TypeError internally
        # More directly, simulate eth.gas_price raising an unhandled error
        type(mock_w3_instance.eth).gas_price = MagicMock(side_effect=Exception("Unexpected error"))

        mock_web3_constructor.return_value = mock_w3_instance
        
        rpc_url = "http://dummy-rpc-url.com"
        with patch('builtins.print') as mock_print:
            gas_price_gwei = get_current_base_l2_gas_price(rpc_url)
            self.assertIsNone(gas_price_gwei)
            # The actual error message will be the string representation of the TypeError
            expected_error_msg = "unsupported operand type(s) for /: 'str' and 'int'"
            mock_print.assert_called_with(f"An unexpected error occurred while fetching Base L2 gas price: {expected_error_msg}")

if __name__ == '__main__':
    unittest.main()
