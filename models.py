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
    from utils import wei_to_ether_str
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
        # Calculate gasFeeInWei
        if self.gasUsed is not None and self.gasPrice is not None:
            try:
                gas_used_int = int(self.gasUsed)
                gas_price_int = int(self.gasPrice)
                self.gasFeeInWei = str(gas_used_int * gas_price_int)
            except ValueError:
                # print(f"Warning: Could not calculate gasFeeInWei for tx {self.hash}: Invalid gasUsed or gasPrice.")
                pass # Keep gasFeeInWei as None

        # Convert timeStamp to datetime
        if self.timeStamp is not None:
            try:
                self.timestamp_dt = datetime.fromtimestamp(int(self.timeStamp))
            except ValueError:
                # print(f"Warning: Could not convert timestamp for tx {self.hash}: Invalid timestamp.")
                pass # Keep timestamp_dt as None
        return self

    # Pydantic V2 field_validator
    @field_validator('gasPrice', 'gasUsed', mode='before')
    def check_convertible_to_int(cls, v: Any, info) -> str: # info is FieldValidationInfo
        if isinstance(v, str) and v.strip() == "":
            return "0" 
        try:
            int(v) 
        except ValueError:
            # Use info.field_name for the field name
            raise ValueError(f"{info.field_name} must be a string representing an integer, or an empty string. Got: '{v}'")
        return v


if __name__ == '__main__':
    # Example Usage and Test
    sample_tx_data_valid = {
        "blockNumber": "12345", "timeStamp": "1678886400", "hash": "0xabcdef123456",
        "from": "0xfromAddress", "to": "0xtoAddress", "value": "1000000000000000000", # 1 ETH
        "gas": "50000", "gasPrice": "20000000000", "gasUsed": "21000", # Results in 0.00042 ETH fee
        "isError": "0", "txreceipt_status": "1"
    }

    sample_tx_data_zero_value = {
        "blockNumber": "12345", "timeStamp": "1678886400", "hash": "0xabcdef123456",
        "from": "0xfromAddress", "to": "0xtoAddress", "value": "0", # 0 ETH
        "gas": "50000", "gasPrice": "20000000000", "gasUsed": "21000",
        "isError": "0", "txreceipt_status": "1"
    }
    
    sample_tx_data_no_gas_fee = { # e.g. if gasUsed or gasPrice were such that gasFeeInWei is None
        "blockNumber": "12345", "timeStamp": "1678886400", "hash": "0xabcdef123456",
        "from": "0xfromAddress", "to": "0xtoAddress", "value": "100",
        "gas": "50000", "gasPrice": "0", "gasUsed": "0", # Results in 0 gasFeeInWei
        "isError": "0", "txreceipt_status": "1"
    }


    sample_tx_data_error_calc = { # This test name might be misleading now due to field_validator
        "blockNumber": "12346",
        "timeStamp": "1678886500",
        "hash": "0xabcdef123457",
        "from": "0xfromAddress2",
        "to": "0xtoAddress2",
        "value": "0",
        "gas": "50000",
        "gasPrice": "", 
        "gasUsed": "21000",
        "isError": "0",
        "txreceipt_status": "1"
    }
    
    sample_tx_data_invalid_ts = {
        "blockNumber": "12347",
        "timeStamp": "invalid_timestamp", 
        "hash": "0xabcdef123458",
        "from": "0xfromAddress3",
        "to": "0xtoAddress3",
        "value": "0",
        "gas": "50000",
        "gasPrice": "20000000000",
        "gasUsed": "21000",
        "isError": "0",
        "txreceipt_status": "1"
    }

    print("Testing BaseTransaction model (Pydantic V2)...")

    # Test 1: Valid data
    try:
        tx1 = BaseTransaction(**sample_tx_data_valid)
        print("\nValid Transaction (tx1):")
        print(f"  Hash: {tx1.hash}")
        print(f"  Timestamp: {tx1.timeStamp}, Converted datetime: {tx1.timestamp_dt}")
        print(f"  Value ETH: {tx1.value_eth_str}")
        print(f"  Gas Fee ETH: {tx1.gas_fee_eth_str}")
        assert tx1.gasFeeInWei == str(21000 * 20000000000)
        assert tx1.timestamp_dt == datetime.fromtimestamp(1678886400)
        assert tx1.value_eth_str == "1.00 ETH"
        assert tx1.gas_fee_eth_str == "0.00042 ETH" # 21000 * 20 Gwei = 420000 Gwei = 0.00042 ETH
        print("  TX1 Valid data test: PASSED")
    except Exception as e:
        print(f"  TX1 Valid data test: FAILED - {e}")

    # Test 2: Data with empty gasPrice string (field_validator converts to "0")
    try:
        tx2 = BaseTransaction(**sample_tx_data_error_calc)
        print("\nTransaction with empty gasPrice (tx2):")
        print(f"  Gas Price: {tx2.gasPrice}, Gas Used: {tx2.gasUsed}") 
        print(f"  Calculated Gas Fee (Wei): {tx2.gasFeeInWei}")
        print(f"  Gas Fee ETH: {tx2.gas_fee_eth_str}")
        assert tx2.gasFeeInWei == "0" # Because gasPrice becomes "0"
        assert tx2.gas_fee_eth_str == "0.00 ETH"
        print("  TX2 Empty gasPrice test: PASSED")
    except Exception as e:
        print(f"  TX2 Empty gasPrice test: FAILED - {e}")
        
    # Test 3: Data with invalid timestamp
    try:
        tx3 = BaseTransaction(**sample_tx_data_invalid_ts)
        print("\nTransaction with invalid timestamp (tx3):")
        print(f"  Timestamp: {tx3.timeStamp}, Converted datetime: {tx3.timestamp_dt}")
        assert tx3.timestamp_dt is None 
        print("  TX3 Invalid timestamp test: PASSED (timestamp_dt is None as expected)")
    except Exception as e:
        print(f"  TX3 Invalid timestamp test: FAILED - {e}")

    # Test 4: Transaction with zero value
    try:
        tx4 = BaseTransaction(**sample_tx_data_zero_value)
        print("\nTransaction with zero value (tx4):")
        print(f"  Value: {tx4.value}, Value ETH: {tx4.value_eth_str}")
        assert tx4.value == "0"
        assert tx4.value_eth_str == "0.00 ETH"
        print("  TX4 Zero value test: PASSED")
    except Exception as e:
        print(f"  TX4 Zero value test: FAILED - {e}")

    # Test 5: Transaction with zero gas fee (e.g. gasPrice=0)
    try:
        tx5 = BaseTransaction(**sample_tx_data_no_gas_fee)
        print("\nTransaction with zero gas fee (tx5):")
        print(f"  GasFeeInWei: {tx5.gasFeeInWei}, Gas Fee ETH: {tx5.gas_fee_eth_str}")
        assert tx5.gasFeeInWei == "0"
        assert tx5.gas_fee_eth_str == "0.00 ETH"
        print("  TX5 Zero gas fee test: PASSED")
    except Exception as e:
        print(f"  TX5 Zero gas fee test: FAILED - {e}")
