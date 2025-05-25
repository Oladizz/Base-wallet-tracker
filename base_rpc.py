from web3 import Web3
from web3.exceptions import ProviderConnectionError
from requests.exceptions import ConnectionError as RequestsConnectionError # Web3 uses requests internally
from typing import Optional

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
