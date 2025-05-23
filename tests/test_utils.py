import unittest
from decimal import Decimal, InvalidOperation

# Add project root to sys.path to allow direct import of modules
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import (
    wei_to_ether_str, 
    wei_to_gwei_str, 
    wei_to_gwei_decimal, 
    calculate_fiat_value,
    WEI_IN_ETHER,
    WEI_IN_GWEI
)

class TestUtils(unittest.TestCase):

    def test_wei_to_ether_str(self):
        self.assertEqual(wei_to_ether_str("1000000000000000000"), "1.00 ETH")
        self.assertEqual(wei_to_ether_str(1000000000000000000), "1.00 ETH") # Test with int
        self.assertEqual(wei_to_ether_str(Decimal("1e18")), "1.00 ETH") # Test with Decimal
        self.assertEqual(wei_to_ether_str("500000000000000000"), "0.50 ETH")
        self.assertEqual(wei_to_ether_str("1234567890000000"), "0.00123457 ETH") # Check rounding and stripping
        self.assertEqual(wei_to_ether_str("1000000000"), "0.000000001 ETH")
        self.assertEqual(wei_to_ether_str("1"), "0.000000000000000001 ETH")
        self.assertEqual(wei_to_ether_str("0"), "0.00 ETH")
        self.assertEqual(wei_to_ether_str(""), "0.00 ETH")
        self.assertEqual(wei_to_ether_str(None), "0.00 ETH")
        self.assertEqual(wei_to_ether_str("invalid_input"), "Error converting Wei to Ether")
        self.assertEqual(wei_to_ether_str("1234567891234567891234"), "1,234.57 ETH") # Test large number formatting

    def test_wei_to_gwei_str(self):
        self.assertEqual(wei_to_gwei_str("1000000000"), "1 Gwei")
        self.assertEqual(wei_to_gwei_str("1234567890"), "1.23 Gwei") # Check rounding
        self.assertEqual(wei_to_gwei_str("100000000"), "0.10 Gwei")
        self.assertEqual(wei_to_gwei_str("5000000000"), "5 Gwei")
        self.assertEqual(wei_to_gwei_str("0"), "0 Gwei")
        self.assertEqual(wei_to_gwei_str(""), "0 Gwei")
        self.assertEqual(wei_to_gwei_str("invalid_input"), "Error converting Wei to Gwei")
        self.assertEqual(wei_to_gwei_str("12345678912345"), "12,345.68 Gwei") # Test large number formatting

    def test_wei_to_gwei_decimal(self):
        self.assertEqual(wei_to_gwei_decimal("1000000000"), Decimal("1"))
        self.assertEqual(wei_to_gwei_decimal("1234567890"), Decimal("1.23456789"))
        self.assertEqual(wei_to_gwei_decimal("100000000"), Decimal("0.1"))
        self.assertEqual(wei_to_gwei_decimal("0"), Decimal("0"))
        self.assertEqual(wei_to_gwei_decimal(""), Decimal("0"))
        self.assertEqual(wei_to_gwei_decimal("invalid_input"), Decimal("0")) # Expect 0 on error

    def test_calculate_fiat_value(self):
        eth_price = Decimal("2000.00")
        
        # 1 ETH
        self.assertEqual(calculate_fiat_value(1 * 10**18, eth_price), Decimal("2000.00"))
        # 0.5 ETH
        self.assertEqual(calculate_fiat_value(int(0.5 * 10**18), eth_price), Decimal("1000.00"))
        # 0.00000001 ETH (10 Gwei) -> 10e-9 ETH * $2000/ETH = $0.00002 -> rounds to $0.00
        self.assertEqual(calculate_fiat_value(10 * 10**9, eth_price), Decimal("0.00")) 
        # Small value leading to less than $0.01 (1 Gwei) -> 1e-9 ETH * $2000/ETH = $0.000002 -> rounds to $0.00
        self.assertEqual(calculate_fiat_value(1 * 10**9, eth_price), Decimal("0.00")) 
        # 0.0000025 ETH -> 0.0000025 * $2000 = $0.005 -> rounds to $0.01
        self.assertEqual(calculate_fiat_value(int(0.0000025 * 10**18), eth_price), Decimal("0.01")) 

        # Zero Wei
        self.assertEqual(calculate_fiat_value(0, eth_price), Decimal("0.00"))
        
        # Edge cases for price
        self.assertIsNone(calculate_fiat_value(1 * 10**18, None))
        self.assertIsNone(calculate_fiat_value(1 * 10**18, Decimal("0")))
        self.assertIsNone(calculate_fiat_value(1 * 10**18, Decimal("-2000")))

        # Invalid wei amount
        self.assertIsNone(calculate_fiat_value(None, eth_price))
        # self.assertIsNone(calculate_fiat_value("invalid_wei", eth_price)) # Current function expects int

if __name__ == '__main__':
    unittest.main()
