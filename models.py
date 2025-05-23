from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator, field_validator
from datetime import datetime

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
    gasFeeInWei: Optional[str] = Field(default=None, validate_default=False) # validate_default=False for Pydantic v2 if calculated
    timestamp_dt: Optional[datetime] = Field(default=None, validate_default=False)

    @model_validator(mode='after') # Pydantic V2 equivalent of root_validator(pre=False)
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
    # Example Usage and Test (same as before, should work with Pydantic V2 syntax)
    sample_tx_data_valid = {
        "blockNumber": "12345",
        "timeStamp": "1678886400", 
        "hash": "0xabcdef123456",
        "from": "0xfromAddress",
        "to": "0xtoAddress",
        "value": "1000000000000000000", 
        "gas": "50000",
        "gasPrice": "20000000000", 
        "gasUsed": "21000",
        "isError": "0",
        "txreceipt_status": "1"
    }

    sample_tx_data_error_calc = {
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
        print(f"  Gas Used: {tx1.gasUsed}, Gas Price: {tx1.gasPrice}")
        print(f"  Calculated Gas Fee (Wei): {tx1.gasFeeInWei}")
        assert tx1.gasFeeInWei == str(21000 * 20000000000)
        assert tx1.timestamp_dt == datetime.fromtimestamp(1678886400)
        print("  TX1 Valid data test: PASSED")
    except Exception as e:
        print(f"  TX1 Valid data test: FAILED - {e}")

    # Test 2: Data leading to calculation error for gasFee
    try:
        tx2 = BaseTransaction(**sample_tx_data_error_calc)
        print("\nTransaction with gas calculation issue (tx2):")
        print(f"  Hash: {tx2.hash}")
        print(f"  Timestamp: {tx2.timeStamp}, Converted datetime: {tx2.timestamp_dt}")
        print(f"  Gas Used: {tx2.gasUsed}, Gas Price: {tx2.gasPrice}") 
        print(f"  Calculated Gas Fee (Wei): {tx2.gasFeeInWei}")
        assert tx2.gasFeeInWei is None 
        print("  TX2 Gas calculation error test: PASSED (gasFeeInWei is None as expected)")
    except Exception as e:
        print(f"  TX2 Gas calculation error test: FAILED - {e}")
        
    # Test 3: Data with invalid timestamp
    try:
        tx3 = BaseTransaction(**sample_tx_data_invalid_ts)
        print("\nTransaction with invalid timestamp (tx3):")
        print(f"  Hash: {tx3.hash}")
        print(f"  Timestamp: {tx3.timeStamp}, Converted datetime: {tx3.timestamp_dt}")
        print(f"  Calculated Gas Fee (Wei): {tx3.gasFeeInWei}")
        assert tx3.timestamp_dt is None 
        print("  TX3 Invalid timestamp test: PASSED (timestamp_dt is None as expected)")
    except Exception as e:
        print(f"  TX3 Invalid timestamp test: FAILED - {e}")

    # Test 4: Example with 'isError' indicating a failed transaction
    sample_tx_data_failed_onchain = {
        "blockNumber": "12348",
        "timeStamp": "1678886600",
        "hash": "0xabcdef123459",
        "from": "0xfromAddress4",
        "to": "0xtoAddress4",
        "value": "100000",
        "gas": "50000",
        "gasPrice": "20000000000",
        "gasUsed": "50000", 
        "isError": "1", 
        "txreceipt_status": "0" 
    }
    try:
        tx4 = BaseTransaction(**sample_tx_data_failed_onchain)
        print("\nTransaction with on-chain error (tx4):")
        print(f"  Hash: {tx4.hash}")
        print(f"  isError: {tx4.isError}, txreceipt_status: {tx4.txreceipt_status}")
        print(f"  Calculated Gas Fee (Wei): {tx4.gasFeeInWei}") 
        assert tx4.gasFeeInWei == str(50000 * 20000000000)
        assert tx4.isError == "1"
        print("  TX4 On-chain error test: PASSED")
    except Exception as e:
        print(f"  TX4 On-chain error test: FAILED - {e}")
