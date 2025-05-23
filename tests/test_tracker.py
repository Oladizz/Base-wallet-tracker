import unittest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch # Added patch

# Add project root to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import BaseTransaction # Needed for type hinting and creating test instances
from tracker import (
    filter_transactions_by_timeframe,
    aggregate_gas_fees,
    get_gas_spent_for_period,
    prepare_daily_gas_data
)

# Helper to create BaseTransaction instances for tests
def create_mock_tx(timestamp_str: str, gas_fee_wei_str: str) -> BaseTransaction:
    # We only need timestamp_dt and gasFeeInWei for these tests.
    # Other fields can be dummy values.
    data = {
        "blockNumber": "1", "hash": "0xhash", "from": "0xfrom", "to": "0xto",
        "value": "0", "gas": "0", "gasPrice": "0", "gasUsed": "0",
        "isError": "0", "txreceipt_status": "1",
        "timeStamp": str(int(datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp())),
        # The model will calculate gasFeeInWei, so we need to provide gasUsed and gasPrice
        # For simplicity in testing aggregation directly, let's assume gasFeeInWei is pre-calculated
        # or ensure the model calculates it as expected.
        # The BaseTransaction model calculates gasFeeInWei from gasUsed * gasPrice.
        # For these tests, let's directly set gasFeeInWei if possible or ensure calculation is correct.
        # The easiest way is to mock the BaseTransaction object's relevant attributes.
    }
    # tx = BaseTransaction(**data) # This would trigger calculations
    
    # For more direct control in testing tracker functions, mock the objects
    tx = MagicMock(spec=BaseTransaction)
    tx.timestamp_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    
    if gas_fee_wei_str is None: # Simulate tx where gasFeeInWei could not be calculated
        tx.gasFeeInWei = None
    elif gas_fee_wei_str == "invalid_string": # Simulate a non-integer string
        tx.gasFeeInWei = "invalid_string"
    else:
        tx.gasFeeInWei = gas_fee_wei_str
    return tx

class TestTrackerDataProcessing(unittest.TestCase):

    def setUp(self):
        # Fixed date for "today" in tests to make them deterministic
        self.fixed_today_str = "2023-11-02 10:00:00"
        self.fixed_today_dt = datetime.strptime(self.fixed_today_str, "%Y-%m-%d %H:%M:%S")
        self.today_tx_fee = "30000000000000000" # 0.03 ETH

        self.transactions_base = [
            create_mock_tx("2023-10-01 10:00:00", "10000000000000000"), # 0.01 ETH
            create_mock_tx("2023-10-15 12:00:00", "20000000000000000"), # 0.02 ETH
            create_mock_tx("2023-10-28 14:00:00", "5000000000000000"),  # 0.005 ETH
            create_mock_tx("2023-11-01 08:00:00", "15000000000000000"), # 0.015 ETH
            create_mock_tx("2023-10-15 16:00:00", None), 
            create_mock_tx("2023-10-16 10:00:00", "invalid_string"),
        ]
        # This transaction will be considered "today's" transaction in tests that mock datetime.now()
        self.today_transaction = create_mock_tx(self.fixed_today_str, self.today_tx_fee)
        
        self.transactions_for_filtering = self.transactions_base + [self.today_transaction]


    def test_filter_transactions_by_timeframe(self):
        start_date = datetime(2023, 10, 15)
        end_date = datetime(2023, 10, 30) 
        # Using self.transactions_for_filtering which includes self.today_transaction (on 2023-11-02)
        # So, transactions within this range are:
        # "2023-10-15 12:00:00"
        # "2023-10-28 14:00:00"
        # "2023-10-15 16:00:00" (None gas fee)
        # "2023-10-16 10:00:00" (invalid gas fee string)
        # self.today_transaction (2023-11-02) is NOT in this range.
        filtered = filter_transactions_by_timeframe(self.transactions_for_filtering, start_date, end_date)
        self.assertEqual(len(filtered), 4) 
        self.assertTrue(all(start_date <= tx.timestamp_dt <= end_date for tx in filtered))

    def test_filter_transactions_no_match(self):
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 31)
        filtered = filter_transactions_by_timeframe(self.transactions_for_filtering, start_date, end_date)
        self.assertEqual(len(filtered), 0)

    def test_aggregate_gas_fees(self):
        # Using self.transactions_for_filtering
        # Expected sum from base: 10^16 + 2*10^16 + 0.5*10^16 + 1.5*10^16 = 5*10^16
        # Plus today_tx_fee: 3*10^16
        # Total: 8*10^16
        # The None and "invalid_string" gasFeeInWei are skipped by aggregate_gas_fees.
        expected_total_wei = int(5 * 10**16) + int(self.today_tx_fee)
        total_gas = aggregate_gas_fees(self.transactions_for_filtering)
        self.assertEqual(total_gas, expected_total_wei)
    
    def test_aggregate_gas_fees_empty_list(self):
        total_gas = aggregate_gas_fees([])
        self.assertEqual(total_gas, 0)

    def test_get_gas_spent_for_period_days(self):
        with patch('tracker.datetime') as mock_datetime_tracker:
            # Mock datetime.now() to return our fixed "today"
            mock_datetime_tracker.now.return_value = self.fixed_today_dt
            mock_datetime_tracker.strptime = datetime.strptime 
            mock_datetime_tracker.date = date 
            mock_datetime_tracker.timedelta = timedelta 
            
            # Test for last 1 day (should only include self.today_transaction)
            # self.fixed_today_dt is 2023-11-02 10:00:00
            # period_days=1 means from 2023-11-01 10:00:00 to 2023-11-02 10:00:00
            # This includes self.today_transaction (2023-11-02 10:00:00).
            # The transaction from "2023-11-01 08:00:00" is NOT included because timeframe_start is 2023-11-01 10:00:00.
            # So, expected is only today_tx_fee (3e16).
            gas_1_day = get_gas_spent_for_period(self.transactions_for_filtering, period_days=1)
            expected_1_day_wei = int(self.today_tx_fee)
            self.assertEqual(gas_1_day, expected_1_day_wei)

            # Test for a period that includes all transactions (e.g., 60 days from self.fixed_today_dt)
            # self.fixed_today_dt is 2023-11-02. 60 days prior is around 2023-09-03.
            # This range should include all transactions in self.transactions_for_filtering.
            all_tx_total_wei = aggregate_gas_fees(self.transactions_for_filtering)
            gas_60_days = get_gas_spent_for_period(self.transactions_for_filtering, period_days=60)
            self.assertEqual(gas_60_days, all_tx_total_wei)
            
    def test_get_gas_spent_for_custom_period(self):
        start_date = datetime(2023, 10, 1)
        end_date = datetime(2023, 10, 31)
        # From self.transactions_for_filtering, transactions in Oct 2023 are:
        # 2023-10-01 (1e16), 2023-10-15 (2e16), 2023-10-28 (0.5e16)
        # None and invalid_string txns are also in Oct but have 0 effective fee.
        # Total: 1e16 + 2e16 + 0.5e16 = 3.5e16
        expected_wei = int(3.5 * 10**16)
        gas_custom = get_gas_spent_for_period(
            self.transactions_for_filtering, custom_start_date=start_date, custom_end_date=end_date
        )
        self.assertEqual(gas_custom, expected_wei)

    def test_get_gas_spent_no_period_all_transactions(self):
        expected_total_wei = aggregate_gas_fees(self.transactions_for_filtering)
        gas_all = get_gas_spent_for_period(self.transactions_for_filtering) # No period specified
        self.assertEqual(gas_all, expected_total_wei)

    def test_prepare_daily_gas_data(self):
        # mock_today_for_test is self.fixed_today_dt (2023-11-02 10:00:00)
        with patch('tracker.datetime') as mock_datetime_tracker:
            mock_datetime_tracker.now.return_value = self.fixed_today_dt
            mock_datetime_tracker.strptime = datetime.strptime
            mock_datetime_tracker.date = date
            mock_datetime_tracker.timedelta = timedelta

            # days_limit = 30. start_date_limit = 2023-11-02 - 29 days = 2023-10-04.
            # Transactions from self.transactions_for_filtering within [2023-10-04, 2023-11-02]:
            # "2023-10-15 12:00:00" (2e16)
            # "2023-10-15 16:00:00" (None) -> 0
            # "2023-10-16 10:00:00" (invalid_string) -> 0
            # "2023-10-28 14:00:00" (0.5e16)
            # "2023-11-01 08:00:00" (1.5e16)
            # self.today_transaction "2023-11-02 10:00:00" (3e16)
            daily_data = prepare_daily_gas_data(self.transactions_for_filtering, days_limit=30)
            
            expected_data = {
                date(2023, 10, 15): 2 * 10**16, 
                # date(2023, 10, 16): 0, # This date will not be in daily_data as the only tx on this day has an invalid fee string
                date(2023, 10, 28): int(0.5 * 10**16),
                date(2023, 11, 1): int(1.5 * 10**16),
                self.fixed_today_dt.date(): int(self.today_tx_fee)
            }
            # The transaction on 2023-10-16 has gasFeeInWei="invalid_string", so int(tx.gasFeeInWei) fails,
            # and it's skipped in prepare_daily_gas_data. Thus, 2023-10-16 should not be a key.
            # The transaction on 2023-10-15 with gasFeeInWei=None is also skipped.
            # So the fee for 2023-10-15 is just from the valid transaction.
            
            self.assertEqual(daily_data, expected_data)
            self.assertEqual(list(daily_data.keys()), sorted(expected_data.keys()))

    def test_prepare_daily_gas_data_empty(self):
        daily_data = prepare_daily_gas_data([], days_limit=30)
        self.assertEqual(daily_data, {})

    def test_prepare_daily_gas_data_no_tx_in_window(self):
        # All transactions are outside the 30-day window relative to a future "today"
        future_today = self.fixed_today_dt + timedelta(days=100)
        with patch('tracker.datetime') as mock_datetime_tracker:
            mock_datetime_tracker.now.return_value = future_today
            mock_datetime_tracker.date = date 
            mock_datetime_tracker.timedelta = timedelta

            daily_data = prepare_daily_gas_data(self.transactions_for_filtering, days_limit=30)
            self.assertEqual(daily_data, {})


if __name__ == '__main__':
    unittest.main()
