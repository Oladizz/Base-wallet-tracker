import requests
import os
from typing import Optional

# It's good practice to have a way to load environment variables if this module is run directly
# or for testing, but the main application (tracker.py) will handle loading .env
# from dotenv import load_dotenv
# load_dotenv()

ETHERSCAN_API_URL = "https://api.etherscan.io/api"

def get_current_base_fee(api_key: str) -> Optional[str]:
    """
    Fetches the current suggested base gas fee from the Etherscan API.

    Args:
        api_key: Your Etherscan API key.

    Returns:
        The suggested base fee in Gwei as a string, or None if an error occurs.
    """
    params = {
        "module": "gastracker",
        "action": "gasoracle",
        "apikey": api_key,
    }
    try:
        response = requests.get(ETHERSCAN_API_URL, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        data = response.json()
        
        if data.get("status") == "1" and data.get("message") == "OK":
            suggest_base_fee = data.get("result", {}).get("suggestBaseFee")
            if suggest_base_fee:
                return str(suggest_base_fee)
            else:
                print("Error: 'suggestBaseFee' not found in Etherscan API response.")
                return None
        else:
            error_message = data.get("result") or data.get("message", "Unknown API error")
            print(f"Error fetching gas oracle data from Etherscan: {error_message}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error while calling Etherscan API: {e}")
        return None
    except ValueError as e: # Includes JSONDecodeError
        print(f"Error parsing Etherscan API response: {e}")
        return None
    except KeyError as e:
        print(f"Unexpected response format from Etherscan API (missing key): {e}")
        return None

if __name__ == '__main__':
    # This part is for testing the function directly
    # You'll need to set your ETHERSCAN_API_KEY environment variable for this to work
    print("Attempting to fetch current base fee directly using etherscan_api.py...")
    api_key_env = os.getenv("ETHERSCAN_API_KEY")
    if not api_key_env:
        print("Please set the ETHERSCAN_API_KEY environment variable to test.")
    else:
        base_fee = get_current_base_fee(api_key_env)
        if base_fee:
            print(f"Current suggested base fee (from etherscan_api.py direct test): {base_fee} Gwei")
        else:
            print("Failed to retrieve base fee (from etherscan_api.py direct test).")
