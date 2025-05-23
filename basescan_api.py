import requests
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation

BASESCAN_API_URL = "https://api.basescan.org/api"

def get_eth_current_price(api_key: str) -> Optional[Decimal]:
    """
    Fetches the current ETH to USD price from the Basescan API.

    Args:
        api_key: Your Basescan API key.

    Returns:
        The ETH price in USD as a Decimal, or None if an error occurs.
    """
    params = {
        "module": "stats",
        "action": "ethprice",
        "apikey": api_key,
    }
    try:
        response = requests.get(BASESCAN_API_URL, params=params)
        response.raise_for_status()  # Raises HTTPError for bad responses

        data = response.json()

        if data.get("status") == "1" and data.get("message") == "OK":
            result = data.get("result")
            if result and "ethusd" in result:
                try:
                    eth_usd_price = Decimal(result["ethusd"])
                    return eth_usd_price
                except InvalidOperation:
                    print(f"Warning: Could not convert ETH price '{result['ethusd']}' to Decimal.")
                    return None
            else:
                print("Warning: 'ethusd' not found in Basescan API 'ethprice' result.")
                return None
        else:
            error_message = data.get("result") or data.get("message", "Unknown API error")
            print(f"Warning: Basescan API error for 'ethprice'. Message: {error_message}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Network error while calling Basescan 'ethprice' API: {e}")
        return None
    except ValueError as e:  # Includes JSONDecodeError
        print(f"Error parsing Basescan 'ethprice' API response: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching ETH price: {e}")
        return None

def get_account_normal_transactions(
    api_key: str, 
    wallet_address: str, 
    start_block: int = 0, 
    end_block: int = 99999999, 
    page: int = 1, 
    offset: int = 200, 
    sort: str = 'desc'
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Fetches 'Normal' transaction history for a given wallet address from the Basescan API.

    Args:
        api_key: Your Basescan API key.
        wallet_address: The wallet address to query.
        start_block: The starting block number.
        end_block: The ending block number.
        page: The page number for pagination.
        offset: The number of transactions per page (max 10000 for Basescan).
        sort: The sorting order ('asc' or 'desc').

    Returns:
        A tuple containing:
            - A list of transaction dictionaries if successful.
            - An optional error message string if an API error occurred (excluding "No transactions found" if that's a valid empty response).
    """
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": start_block,
        "endblock": end_block,
        "page": page,
        "offset": offset,
        "sort": sort,
        "apikey": api_key,
    }

    try:
        response = requests.get(BASESCAN_API_URL, params=params)
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
        
        data = response.json()

        # Basescan API returns status "1" for success, message "OK"
        # and result as a list of transactions.
        # If no transactions, status is "1", message "No transactions found", result is an empty list.
        # If API key is invalid, status is "0", message "NOTOK", result is "Invalid API Key".
        if data.get("status") == "1": # Success
            if isinstance(data.get("result"), list):
                return data["result"], None # No error message
            else: # Should not happen if status is "1" and message is "OK"
                err_msg = f"Basescan API reported success but 'result' was not a list: {data.get('result')}"
                print(f"Warning: {err_msg}")
                return [], err_msg
        # Specific check for "No transactions found" which Basescan might return with status "0" or "1"
        elif data.get("message") == "No transactions found": # Covers status "0" or "1" if message is this
            return [], None # Valid empty response, no error message
        else: # Actual API error
            error_message_detail = data.get("result") or data.get("message", "Unknown API error")
            err_msg = f"Basescan API error for address {wallet_address}. Message: {error_message_detail}"
            print(f"Warning: {err_msg}")
            return [], err_msg

    except requests.exceptions.RequestException as e:
        err_msg = f"Network error while calling Basescan API for address {wallet_address}: {e}"
        print(err_msg)
        return [], err_msg
    except ValueError as e:  # Includes JSONDecodeError
        err_msg = f"Error parsing Basescan API response for address {wallet_address}: {e}"
        print(err_msg)
        return [], err_msg
    except Exception as e:
        err_msg = f"An unexpected error occurred while fetching transactions for {wallet_address}: {e}"
        print(err_msg)
        return [], err_msg

if __name__ == '__main__':
    # This part is for testing the function directly
    # You'll need to set your BASESCAN_API_KEY and a TEST_WALLET_ADDRESS 
    # environment variables for this to work.
    import os
    from dotenv import load_dotenv
    load_dotenv() # Load .env file for local testing
    
    basescan_api_key_env = os.getenv("BASESCAN_API_KEY")

    if not basescan_api_key_env:
        print("Please set the BASESCAN_API_KEY environment variable to test API functions.")
    else:
        # Test get_eth_current_price
        print("\nAttempting to fetch current ETH price directly using basescan_api.py...")
        eth_price = get_eth_current_price(basescan_api_key_env)
        if eth_price is not None:
            print(f"Current ETH Price (from basescan_api.py direct test): ${eth_price:.2f} USD")
        else:
            print("Failed to retrieve ETH price (from basescan_api.py direct test).")

        # Test get_account_normal_transactions
        print("\nAttempting to fetch normal transactions directly using basescan_api.py...")
        test_wallet_address_env = os.getenv("TEST_WALLET_ADDRESS")

        if not test_wallet_address_env:
            print("Please set the TEST_WALLET_ADDRESS environment variable to test transaction fetching.")
        else:
            print(f"Fetching transactions for wallet: {test_wallet_address_env} using API key prefix: {basescan_api_key_env[:5]}...")
            transactions, error = get_account_normal_transactions(
                api_key=basescan_api_key_env, 
                wallet_address=test_wallet_address_env,
                offset=2, 
                sort='desc'
            )

            if error:
                print(f"Test Error: {error}")

            if transactions:
                print(f"\nSuccessfully fetched {len(transactions)} transactions:")
                for i, tx in enumerate(transactions[:2]): 
                    print(f"  Transaction {i+1} Hash: {tx.get('hash')}")
            elif not error: # No error, but no transactions
                 print("No transactions found for the address (and no API error).")
            else: # Error and no transactions
                print("Failed to retrieve transactions due to an error (see above).")
