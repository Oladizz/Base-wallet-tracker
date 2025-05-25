from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator, field_validator, computed_field
from datetime import datetime

# Add project root to sys.path to allow direct import of modules
# This is for cases where models.py might be run directly or imported by other scripts in tests
import sys
import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# For direct execution, ensure utils can be found. For app execution, Flask handles paths.
try:
    from .utils import wei_to_ether_str # Changed to relative import
except ImportError:
    # Fallback for cases where utils might not be in path (e.g. direct model testing without full project setup)
    # This is a simple placeholder. A better solution for complex projects might involve proper packaging.
    def wei_to_ether_str(value): return f"{value} Wei (utils.wei_to_ether_str not loaded)"


class BaseTransaction(BaseModel):
    blockNumber: str
    timeStamp: str
    hash: str
    from_address: str = Field(alias='from')
    to_address: str = Field(alias='to')
    value: str
    gas: str
    gasPrice: str
    gasUsed: str
    isError: str
    txreceipt_status: str

    # Calculated fields
    gasFeeInWei: Optional[str] = Field(default=None, validate_default=False) 
    timestamp_dt: Optional[datetime] = Field(default=None, validate_default=False)

    # New fields from transaction receipt
    l1FeeFromReceipt: Optional[str] = None
    gasUsedFromReceipt: Optional[str] = None
    effectiveGasPriceFromReceipt: Optional[str] = None

    # Computed fields for easier template rendering
    @computed_field
    @property
    def value_eth_str(self) -> str:
        return wei_to_ether_str(self.value)

    @computed_field
    @property
    def gas_fee_eth_str(self) -> str:
        if self.gasFeeInWei:
            return wei_to_ether_str(self.gasFeeInWei)
        return "N/A"

    @model_validator(mode='after')
    def calculate_derived_fields(self) -> 'BaseTransaction':
        # Convert timeStamp to datetime first (can be done independently)
        if self.timeStamp is not None:
            try:
                self.timestamp_dt = datetime.fromtimestamp(int(self.timeStamp))
            except ValueError:
                # print(f"Warning: Could not convert timestamp for tx {self.hash}: Invalid timestamp.")
                pass # Keep timestamp_dt as None
        
        # New gas fee calculation logic:
        final_l2_fee_wei = 0
        final_l1_fee_wei = 0

        if self.gasUsedFromReceipt is not None and self.effectiveGasPriceFromReceipt is not None:
            try:
                # Ensure hex strings (like '0x...') are converted correctly if they come from RPC
                gas_used_receipt_int = int(self.gasUsedFromReceipt, 0) if isinstance(self.gasUsedFromReceipt, str) else int(self.gasUsedFromReceipt)
                effective_gas_price_receipt_int = int(self.effectiveGasPriceFromReceipt, 0) if isinstance(self.effectiveGasPriceFromReceipt, str) else int(self.effectiveGasPriceFromReceipt)
                final_l2_fee_wei = gas_used_receipt_int * effective_gas_price_receipt_int
                # print(f"DEBUG BaseTransaction: Using receipt data for L2 fee for tx {self.hash}. L2 fee: {final_l2_fee_wei}")
            except ValueError:
                # print(f"Warning: Could not parse receipt gasUsed/effectiveGasPrice for tx {self.hash} (values: '{self.gasUsedFromReceipt}', '{self.effectiveGasPriceFromReceipt}'). Falling back for L2 fee.")
                # Fallback to original gasUsed and gasPrice if receipt data is invalid
                if self.gasUsed is not None and self.gasPrice is not None:
                    try:
                        final_l2_fee_wei = int(self.gasUsed) * int(self.gasPrice)
                    except ValueError:
                        pass # final_l2_fee_wei remains 0
        elif self.gasUsed is not None and self.gasPrice is not None: # Fallback if no receipt data for L2
            try:
                final_l2_fee_wei = int(self.gasUsed) * int(self.gasPrice)
                # print(f"DEBUG BaseTransaction: Using txlist data for L2 fee for tx {self.hash}. L2 fee: {final_l2_fee_wei}")
            except ValueError:
                # print(f"Warning: Could not parse txlist gasUsed/gasPrice for tx {self.hash}.")
                pass # final_l2_fee_wei remains 0
        
        if self.l1FeeFromReceipt is not None:
            try:
                # Ensure hex strings (like '0x...') are converted correctly
                final_l1_fee_wei = int(self.l1FeeFromReceipt, 0) if isinstance(self.l1FeeFromReceipt, str) else int(self.l1FeeFromReceipt)
                # print(f"DEBUG BaseTransaction: L1 fee for tx {self.hash}: {final_l1_fee_wei}")
            except ValueError:
                # print(f"Warning: Could not parse l1FeeFromReceipt for tx {self.hash} (value: '{self.l1FeeFromReceipt}').")
                pass # final_l1_fee_wei remains 0

        if final_l2_fee_wei > 0 or final_l1_fee_wei > 0:
             self.gasFeeInWei = str(final_l2_fee_wei + final_l1_fee_wei)
        else:
            # If all calculations resulted in zero (e.g. all data missing/invalid), set to "0"
            self.gasFeeInWei = "0" 
        
        # Updated debug print statement
        # print(f"DEBUG BaseTransaction: hash={self.hash}, "
        #       f"orig_gasUsed={self.gasUsed}, orig_gasPrice={self.gasPrice}, "
        #       f"receipt_gasUsed={self.gasUsedFromReceipt}, receipt_effGasPrice={self.effectiveGasPriceFromReceipt}, "
        #       f"l1Fee={self.l1FeeFromReceipt}, calculated_totalGasFeeInWei={self.gasFeeInWei}")

        # Convert timeStamp to datetime (moved to the beginning of the method)
        # if self.timeStamp is not None:
            # try:
            #     self.timestamp_dt = datetime.fromtimestamp(int(self.timeStamp))
            # except ValueError:
            #     # print(f"Warning: Could not convert timestamp for tx {self.hash}: Invalid timestamp.")
            #     pass # Keep timestamp_dt as None
        return self

    # Pydantic V2 field_validator for fields coming from txlist (original source)
    # These primarily handle empty strings by converting them to "0".
    # Receipt fields (l1FeeFromReceipt etc.) are less likely to be empty strings;
    # they'd more likely be None if absent, or hex/int strings if present.
    # The new logic handles None for receipt fields and uses int(value, 0) for hex conversion.
    @field_validator('gasPrice', 'gasUsed', 'value', mode='before') # Added 'value' just in case it can be empty
    def check_txlist_numeric_fields(cls, v: Any, info) -> str:
        if isinstance(v, str) and v.strip() == "":
            # print(f"Info: Converting empty string to '0' for field {info.field_name}")
            return "0" 
        # Check if it's a hex string
        if isinstance(v, str) and v.startswith('0x'):
            try:
                int(v, 16) # Validate hex
                return v # Return hex string as is; int(value, 0) will handle it later
            except ValueError:
                raise ValueError(f"{info.field_name} must be a valid hex string if starting with '0x'. Got: '{v}'")
        # Check if it's a decimal string
        try:
            int(v) # Validate decimal
        except ValueError:
            raise ValueError(f"{info.field_name} must be a string representing an integer. Got: '{v}'")
        return v
    
    # It's important that l1FeeFromReceipt, gasUsedFromReceipt, effectiveGasPriceFromReceipt
    # are correctly handled if they are hex strings. The int(value, 0) in the model_validator
    # is intended for this. If they can also be empty strings from some source (unlikely for RPC receipt),
    # then they might need a specific validator or handling in the model_validator.
    # For now, assuming they are None or valid hex/decimal strings.


if __name__ == '__main__':
    # Example Usage and Test with new fields
    print("Testing BaseTransaction model (Pydantic V2) with new fee logic...")

    # Test 1: Only txlist data (fallback)
    sample_tx_data_txlist_only = {
        "blockNumber": "1", "timeStamp": "1678886400", "hash": "0x1",
        "from": "0xA", "to": "0xB", "value": "1000",
        "gas": "50000", "gasPrice": "20000000000", "gasUsed": "21000", # L2 fee = 0.00042 ETH
        "isError": "0", "txreceipt_status": "1"
    }
    tx1 = BaseTransaction(**sample_tx_data_txlist_only)
    print(f"\nTest 1 (txlist only): Hash: {tx1.hash}, GasFeeInWei: {tx1.gasFeeInWei}, ETH: {tx1.gas_fee_eth_str}")
    assert tx1.gasFeeInWei == str(21000 * 20000000000) # 420000000000000

    # Test 2: Receipt data available (L1 + L2)
    sample_tx_data_with_receipt = {
        "blockNumber": "2", "timeStamp": "1678886500", "hash": "0x2",
        "from": "0xA", "to": "0xB", "value": "0",
        "gas": "0", "gasPrice": "0", "gasUsed": "0", # Original fields ignored if receipt present
        "isError": "0", "txreceipt_status": "1",
        "l1FeeFromReceipt": "100000000000000",             # 0.0001 ETH
        "gasUsedFromReceipt": "25000",                     # L2 part
        "effectiveGasPriceFromReceipt": "10000000000"     # 10 Gwei (L2 part) -> 0.00025 ETH
    } # Total: 0.0001 + 0.00025 = 0.00035 ETH
    tx2 = BaseTransaction(**sample_tx_data_with_receipt)
    print(f"Test 2 (with receipt): Hash: {tx2.hash}, GasFeeInWei: {tx2.gasFeeInWei}, ETH: {tx2.gas_fee_eth_str}")
    expected_total_fee_test2 = (25000 * 10000000000) + 100000000000000 # 250 Gwei + 100 Gwei (in Wei terms)
    assert tx2.gasFeeInWei == str(expected_total_fee_test2) # 350000000000000

    # Test 3: Receipt data has L1 fee, but L2 from txlist (partial receipt)
    sample_tx_data_partial_receipt_l1 = {
        "blockNumber": "3", "timeStamp": "1678886600", "hash": "0x3",
        "from": "0xA", "to": "0xB", "value": "0",
        "gas": "50000", "gasPrice": "20000000000", "gasUsed": "21000", # L2 fallback: 0.00042 ETH
        "isError": "0", "txreceipt_status": "1",
        "l1FeeFromReceipt": "100000000000000"              # 0.0001 ETH
        # gasUsedFromReceipt and effectiveGasPriceFromReceipt are None
    } # Total: 0.0001 + 0.00042 = 0.00052 ETH
    tx3 = BaseTransaction(**sample_tx_data_partial_receipt_l1)
    print(f"Test 3 (L1 from receipt, L2 from txlist): Hash: {tx3.hash}, GasFeeInWei: {tx3.gasFeeInWei}, ETH: {tx3.gas_fee_eth_str}")
    expected_total_fee_test3 = (21000 * 20000000000) + 100000000000000
    assert tx3.gasFeeInWei == str(expected_total_fee_test3)

    # Test 4: Invalid receipt data (e.g., non-numeric string), fallback to txlist
    sample_tx_data_invalid_receipt = {
        "blockNumber": "4", "timeStamp": "1678886700", "hash": "0x4",
        "from": "0xA", "to": "0xB", "value": "0",
        "gas": "50000", "gasPrice": "20000000000", "gasUsed": "21000", # L2 fallback: 0.00042 ETH
        "isError": "0", "txreceipt_status": "1",
        "l1FeeFromReceipt": "100000000000000",             # 0.0001 ETH
        "gasUsedFromReceipt": "not_a_number",              # Invalid
        "effectiveGasPriceFromReceipt": "10000000000"     # Valid, but pair is invalid
    } # Total: 0.0001 + 0.00042 = 0.00052 ETH
    tx4 = BaseTransaction(**sample_tx_data_invalid_receipt)
    print(f"Test 4 (invalid receipt, fallback L2): Hash: {tx4.hash}, GasFeeInWei: {tx4.gasFeeInWei}, ETH: {tx4.gas_fee_eth_str}")
    assert tx4.gasFeeInWei == str(expected_total_fee_test3) # Same as test 3 as L2 part falls back

    # Test 5: All data missing or invalid
    sample_tx_data_all_missing = {
        "blockNumber": "5", "timeStamp": "1678886800", "hash": "0x5",
        "from": "0xA", "to": "0xB", "value": "0",
        "gas": "", "gasPrice": "", "gasUsed": "", # Empty, will be "0" by field_validator
        "isError": "0", "txreceipt_status": "1",
        "l1FeeFromReceipt": None,
        "gasUsedFromReceipt": None,
        "effectiveGasPriceFromReceipt": None
    }
    tx5 = BaseTransaction(**sample_tx_data_all_missing)
    print(f"Test 5 (all missing/invalid): Hash: {tx5.hash}, GasFeeInWei: {tx5.gasFeeInWei}, ETH: {tx5.gas_fee_eth_str}")
    assert tx5.gasFeeInWei == "0"

    # Test 6: Hex values from receipt
    sample_tx_data_hex_receipt = {
        "blockNumber": "6", "timeStamp": "1678886900", "hash": "0x6",
        "from": "0xA", "to": "0xB", "value": "0",
        "gas": "0", "gasPrice": "0", "gasUsed": "0", 
        "isError": "0", "txreceipt_status": "1",
        "l1FeeFromReceipt": "0x174876e800",             # 100000000000000 Wei (0.0001 ETH)
        "gasUsedFromReceipt": "0x61a8",                 # 25000
        "effectiveGasPriceFromReceipt": "0x2540be400"   # 10000000000 Wei (10 Gwei)
    } # L2 = 25000 * 10 Gwei = 250000 Gwei = 0.00025 ETH. Total = 0.00035 ETH
    tx6 = BaseTransaction(**sample_tx_data_hex_receipt)
    print(f"Test 6 (hex receipt): Hash: {tx6.hash}, GasFeeInWei: {tx6.gasFeeInWei}, ETH: {tx6.gas_fee_eth_str}")
    # expected_l2_fee_test6_wei = 25000 * 10000000000
    # expected_l1_fee_test6_wei = 100000000000000
    # expected_total_fee_test6 = expected_l2_fee_test6_wei + expected_l1_fee_test6_wei
    assert tx6.gasFeeInWei == str(expected_total_fee_test2) # Same as test 2

    print("\nBaseTransaction model tests complete.")
