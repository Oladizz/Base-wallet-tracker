from web3 import Web3
from web3.exceptions import ProviderConnectionError
from requests.exceptions import ConnectionError as RequestsConnectionError # Web3 uses requests internally
from typing import Optional, Dict, Any # Added Dict, Any

import requests # Added
import json # Added


def get_current_base_l2_gas_price(rpc_url: str) -> Optional[float]:
    """
    Fetches the current L2 gas price from the Base blockchain using web3.py.

    Args:
        rpc_url: The RPC URL for the Base blockchain.

    Returns:
        The current gas price in Gwei as a float, or None if an error occurs.
    """
    try:
        # Initialize Web3 instance
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        # Check connection
        if not w3.is_connected():
            print(f"Error: Could not connect to Base RPC URL: {rpc_url}")
            return None

        # Get current gas price in Wei
        gas_price_wei = w3.eth.gas_price

        # Convert gas price from Wei to Gwei
        gas_price_gwei = gas_price_wei / 10**9
        
        return gas_price_gwei

    except ProviderConnectionError as e:
        print(f"Error connecting to Base RPC provider at {rpc_url}: {e}")
        return None
    except RequestsConnectionError as e: # Catching requests.exceptions.ConnectionError
        print(f"Network error while trying to connect to Base RPC URL {rpc_url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching Base L2 gas price: {e}")
        return None

if __name__ == '__main__':
    # This part is for testing the function directly
    # You'll need to set your BASE_RPC_URL environment variable for this to work
    # and ensure the RPC endpoint is accessible.
    import os
    from dotenv import load_dotenv
    load_dotenv() # Load .env file for local testing
    
    print("Attempting to fetch Base L2 gas price directly using base_rpc.py...")
    base_rpc_url_env = os.getenv("BASE_RPC_URL")
    
    if not base_rpc_url_env:
        print("Please set the BASE_RPC_URL environment variable in your .env file to test.")
    else:
        # Example public RPC for Base - replace if you have a specific one
        # Note: Public RPCs might be rate-limited or less reliable for production
        # For testing, a common public one is https://mainnet.base.org
        print(f"Using Base RPC URL: {base_rpc_url_env}")
        gas_price = get_current_base_l2_gas_price(base_rpc_url_env)
        if gas_price is not None:
            print(f"Current Base L2 Gas Price (from base_rpc.py direct test): {gas_price:.2f} Gwei")
        else:
            print("Failed to retrieve Base L2 gas price (from base_rpc.py direct test).")

    # Test for get_transaction_receipt_details
    # print("\nAttempting to fetch transaction receipt details...")
    # sample_tx_hash = "YOUR_TEST_BASE_TRANSACTION_HASH_HERE" # Replace with a real Base transaction hash
    # if not base_rpc_url_env:
    #     print("BASE_RPC_URL not found in .env, skipping receipt test.")
    # elif sample_tx_hash == "YOUR_TEST_BASE_TRANSACTION_HASH_HERE":
    #     print("Please replace YOUR_TEST_BASE_TRANSACTION_HASH_HERE with an actual hash to test.")
    # else:
    #     receipt_details = get_transaction_receipt_details(sample_tx_hash, base_rpc_url_env)
    #     if receipt_details:
    #         print(f"\nReceipt details for {sample_tx_hash}:")
    #         print(f"  L1 Fee: {receipt_details.get('l1Fee')}")
    #         print(f"  Gas Used (from receipt): {receipt_details.get('gasUsed')}")
    #         print(f"  Effective Gas Price (from receipt): {receipt_details.get('effectiveGasPrice')}")
    #     else:
    #         print(f"Failed to retrieve receipt details for {sample_tx_hash}.")

    # Test for get_eth_balance
    # print("\nAttempting to fetch ETH balance...")
    # sample_address_for_balance = "YOUR_TEST_WALLET_ADDRESS_HERE" # Replace with a real Base wallet address
    # if not base_rpc_url_env:
    #     print("BASE_RPC_URL not found in .env, skipping balance test.")
    # elif sample_address_for_balance == "YOUR_TEST_WALLET_ADDRESS_HERE":
    #     print("Please replace YOUR_TEST_WALLET_ADDRESS_HERE with an actual address to test balance.")
    # else:
    #     balance = get_eth_balance(sample_address_for_balance, base_rpc_url_env)
    #     if balance is not None:
    #         # Assuming you have a wei_to_ether_str function for display if balance is large
    #         # from utils import wei_to_ether_str # You'd need to import this if using it here
    #         print(f"Balance for {sample_address_for_balance}: {balance} Wei") # Raw Wei string
    #         # print(f"Formatted Balance: {wei_to_ether_str(balance)}")
    #     else:
    #         print(f"Failed to retrieve balance for {sample_address_for_balance}.")


def get_eth_balance(address: str, rpc_url: str) -> Optional[str]:
    """
    Fetches the ETH balance for a given address.

    Args:
        address: The wallet address.
        rpc_url: The URL of the Base RPC endpoint.

    Returns:
        The balance in Wei as a string if successful, otherwise None.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"], # Get balance at the latest block
        "id": 1 
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(rpc_url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            print(f"RPC Error for eth_getBalance {address}: {data['error']}")
            return None
        
        result = data.get("result") # Balance in hex Wei
        if result is not None:
            # Convert hex Wei to decimal Wei string
            # int(result, 16) converts hex to int. Then str() converts int to string.
            return str(int(result, 16)) 
        else:
            print(f"No result in eth_getBalance for {address}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error fetching balance for {address}: {e}")
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e: # Added ValueError for int conversion
        print(f"Error decoding, parsing, or converting balance for {address}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching balance for {address}: {e}")
        return None

def get_transaction_receipt_details(tx_hash: str, rpc_url: str) -> Optional[Dict[str, str]]:
    """
    Fetches the transaction receipt for a given hash and extracts L1 fee,
    gasUsed (from receipt), and effectiveGasPrice (from receipt).

    Args:
        tx_hash: The transaction hash.
        rpc_url: The URL of the Base RPC endpoint.

    Returns:
        A dictionary with 'l1Fee', 'gasUsed', 'effectiveGasPrice' if successful
        and fields are present, otherwise None. Values are returned as strings.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionReceipt",
        "params": [tx_hash],
        "id": 1  # Standard JSON-RPC request ID
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(rpc_url, json=payload, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        receipt_data = response.json()

        if receipt_data.get("error"):
            print(f"RPC Error for tx {tx_hash}: {receipt_data['error']}")
            return None
        
        result = receipt_data.get("result")
        if not result:
            print(f"No result in receipt for tx {tx_hash}")
            return None

        # Extract fields. Values from RPC are typically hex strings (prefixed with 0x)
        # or already numbers in some cases. We need to return them as strings.
        l1_fee = result.get("l1Fee")
        gas_used_receipt = result.get("gasUsed")
        effective_gas_price_receipt = result.get("effectiveGasPrice")

        # Ensure all critical fields are present before returning
        if l1_fee is not None and gas_used_receipt is not None and effective_gas_price_receipt is not None:
            # Convert hex to string if they are hex, or int/str to str.
            # Pydantic will handle string-to-Decimal/int conversion later if needed.
            return {
                "l1Fee": str(l1_fee),
                "gasUsed": str(gas_used_receipt), # Name consistency with existing model fields
                "effectiveGasPrice": str(effective_gas_price_receipt)
            }
        else:
            # Log which fields might be missing for debugging
            # print(f"DEBUG: Receipt for {tx_hash} missing one or more fields: "
            #       f"l1Fee={l1_fee}, gasUsed={gas_used_receipt}, effectiveGasPrice={effective_gas_price_receipt}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request error fetching receipt for {tx_hash}: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error decoding or parsing receipt for {tx_hash}: {e}")
        return None
    except Exception as e: # Catch any other unexpected errors
        print(f"Unexpected error processing receipt for {tx_hash}: {e}")
        return None
