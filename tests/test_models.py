import unittest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

# Add project root to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import BaseTransaction

class TestBaseTransactionModel(unittest.TestCase):

    def test_valid_transaction_data(self):
        data = {
            "blockNumber": "123",
            "timeStamp": "1609459200",  # 2021-01-01 00:00:00 UTC
            "hash": "0x123abc",
            "from": "0xfromAddress",
            "to": "0xtoAddress",
            "value": "1000000000000000000",  # 1 ETH
            "gas": "50000",
            "gasPrice": "20000000000",  # 20 Gwei
            "gasUsed": "21000",
            "isError": "0",
            "txreceipt_status": "1"
        }
        transaction = BaseTransaction(**data)
        self.assertEqual(transaction.blockNumber, "123")
        self.assertEqual(transaction.timeStamp, "1609459200")
        self.assertEqual(transaction.hash, "0x123abc")
        self.assertEqual(transaction.from_address, "0xfromAddress") # Test aliasing
        self.assertEqual(transaction.to_address, "0xtoAddress")   # Test aliasing
        self.assertEqual(transaction.value, "1000000000000000000")
        self.assertEqual(transaction.gas, "50000")
        self.assertEqual(transaction.gasPrice, "20000000000")
        self.assertEqual(transaction.gasUsed, "21000")
        self.assertEqual(transaction.isError, "0")
        self.assertEqual(transaction.txreceipt_status, "1")

        # Test calculated fields
        expected_gas_fee_wei = str(21000 * 20000000000)
        self.assertEqual(transaction.gasFeeInWei, expected_gas_fee_wei)
        self.assertEqual(transaction.timestamp_dt, datetime.fromtimestamp(1609459200))

    def test_missing_gas_price(self):
        data = {
            "blockNumber": "124", "timeStamp": "1609459300", "hash": "0x124abc",
            "from": "0xfromAddress", "to": "0xtoAddress", "value": "0",
            "gas": "50000", "gasPrice": "", "gasUsed": "21000", # Empty gasPrice
            "isError": "0", "txreceipt_status": "1"
        }
        # The field_validator converts empty string to "0"
        transaction = BaseTransaction(**data)
        self.assertEqual(transaction.gasPrice, "0") 
        # gasFeeInWei should be "0" because gasPrice is "0"
        self.assertEqual(transaction.gasFeeInWei, "0")


    def test_missing_gas_used(self):
        data = {
            "blockNumber": "125", "timeStamp": "1609459400", "hash": "0x125abc",
            "from": "0xfromAddress", "to": "0xtoAddress", "value": "0",
            "gas": "50000", "gasPrice": "20000000000", "gasUsed": "", # Empty gasUsed
            "isError": "0", "txreceipt_status": "1"
        }
        # The field_validator converts empty string to "0"
        transaction = BaseTransaction(**data)
        self.assertEqual(transaction.gasUsed, "0")
        # gasFeeInWei should be "0" because gasUsed is "0"
        self.assertEqual(transaction.gasFeeInWei, "0")

    def test_invalid_gas_price_string(self):
        # Non-integer string for gasPrice
        data = {
            "blockNumber": "126", "timeStamp": "1609459500", "hash": "0x126abc",
            "from": "0xfromAddress", "to": "0xtoAddress", "value": "0",
            "gas": "50000", "gasPrice": "not_a_number", "gasUsed": "21000",
            "isError": "0", "txreceipt_status": "1"
        }
        with self.assertRaises(ValidationError) as context:
            BaseTransaction(**data)
        self.assertTrue("gasPrice must be a string representing an integer" in str(context.exception))


    def test_invalid_gas_used_string(self):
        # Non-integer string for gasUsed
        data = {
            "blockNumber": "127", "timeStamp": "1609459600", "hash": "0x127abc",
            "from": "0xfromAddress", "to": "0xtoAddress", "value": "0",
            "gas": "50000", "gasPrice": "20000000000", "gasUsed": "not_a_number",
            "isError": "0", "txreceipt_status": "1"
        }
        with self.assertRaises(ValidationError) as context:
            BaseTransaction(**data)
        self.assertTrue("gasUsed must be a string representing an integer" in str(context.exception))


    def test_invalid_timestamp(self):
        data = {
            "blockNumber": "128", "timeStamp": "invalid_timestamp", "hash": "0x128abc",
            "from": "0xfromAddress", "to": "0xtoAddress", "value": "0",
            "gas": "50000", "gasPrice": "20000000000", "gasUsed": "21000",
            "isError": "0", "txreceipt_status": "1"
        }
        transaction = BaseTransaction(**data)
        self.assertIsNone(transaction.timestamp_dt) # Expect None due to conversion error
        # gasFeeInWei should still be calculated if gasPrice and gasUsed are valid
        expected_gas_fee_wei = str(21000 * 20000000000)
        self.assertEqual(transaction.gasFeeInWei, expected_gas_fee_wei)

    def test_transaction_with_error_status(self):
        data = {
            "blockNumber": "129", "timeStamp": "1609459700", "hash": "0x129abc",
            "from": "0xfromAddress", "to": "0xtoAddress", "value": "0",
            "gas": "50000", "gasPrice": "20000000000", "gasUsed": "50000", # Full gas used
            "isError": "1", # Transaction error
            "txreceipt_status": "0" # Receipt status indicates failure
        }
        transaction = BaseTransaction(**data)
        self.assertEqual(transaction.isError, "1")
        self.assertEqual(transaction.txreceipt_status, "0")
        # Gas fee is still paid for failed transactions
        expected_gas_fee_wei = str(50000 * 20000000000)
        self.assertEqual(transaction.gasFeeInWei, expected_gas_fee_wei)

if __name__ == '__main__':
    unittest.main()
