import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pydantic import ValidationError
from datetime import datetime, timedelta, date # Added date
from collections import OrderedDict # For sorted dict

from decimal import Decimal # New import

from etherscan_api import get_current_base_fee
from base_rpc import get_current_base_l2_gas_price
from basescan_api import get_account_normal_transactions, get_eth_current_price # Modified import
from models import BaseTransaction
from utils import wei_to_ether_str, wei_to_gwei_str, calculate_fiat_value # Modified import

def fetch_and_display_gas_prices():
    """
    Fetches and displays:
    1. Ethereum current suggested base gas fee from Etherscan.
    2. Base L2 current gas price using a configured RPC URL.
    """
    # This function is already loaded by load_dotenv() if called after/from main execution block
    # load_dotenv() # Keep it here if this function could be called independently

    # Fetch and display Ethereum base fee from Etherscan
    etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
    if not etherscan_api_key:
        print("Warning: ETHERSCAN_API_KEY not found. Skipping Ethereum gas fee.")
    else:
        print("\nFetching current Ethereum base gas fee from Etherscan...")
        eth_base_fee = get_current_base_fee(etherscan_api_key)
        if eth_base_fee is not None:
            print(f"Current Ethereum suggested base fee: {eth_base_fee} Gwei")
        else:
            print("Failed to retrieve the Ethereum current base gas fee.")

    # Fetch and display Base L2 gas price
    base_rpc_url = os.getenv("BASE_RPC_URL")
    if not base_rpc_url:
        print("\nWarning: BASE_RPC_URL not found. Skipping Base L2 gas price.")
    else:
        print(f"\nFetching current Base L2 gas price from {base_rpc_url}...")
        base_l2_gas_price = get_current_base_l2_gas_price(base_rpc_url)
        if base_l2_gas_price is not None:
            print(f"Current Base L2 Gas Price: {base_l2_gas_price:.2f} Gwei")
        else:
            print("Failed to retrieve the Base L2 gas price.")

def fetch_and_process_transactions(wallet_address: str) -> List[BaseTransaction]:
    """
    Fetches normal transactions for a wallet from Basescan, processes them into
    BaseTransaction models, and prints some information.
    """
    # load_dotenv() will be called in main, ensuring env vars are loaded
    basescan_api_key = os.getenv("BASESCAN_API_KEY")

    if not basescan_api_key:
        print("Error: BASESCAN_API_KEY not found in environment variables.")
        print("Please set it in your .env file to fetch Base transactions.")
        return []

    if not wallet_address:
        print("Error: No wallet address provided for transaction fetching.")
        return []

    print(f"\nFetching normal transactions for wallet: {wallet_address} from Basescan...")
    raw_transactions = get_account_normal_transactions(
        api_key=basescan_api_key,
        wallet_address=wallet_address,
        offset=10 # Fetching fewer transactions for demo purposes
    )

    processed_transactions: List[BaseTransaction] = []
    if not raw_transactions:
        print("No transactions found or API error occurred.")
        return processed_transactions

    print(f"Retrieved {len(raw_transactions)} raw transactions. Processing...")

    for i, tx_data in enumerate(raw_transactions):
        try:
            transaction = BaseTransaction(**tx_data)
            processed_transactions.append(transaction)
        except ValidationError as e:
            print(f"Warning: Could not validate transaction data for tx hash {tx_data.get('hash', 'N/A')}: {e.errors()}")
            # Optionally, print problematic data: print(f"Problematic data: {tx_data}")
        except Exception as e:
            print(f"Warning: An unexpected error occurred processing tx hash {tx_data.get('hash', 'N/A')}: {e}")

    print(f"\nSuccessfully processed {len(processed_transactions)} transactions.")

    if processed_transactions:
        print("\nDetails of the first few processed transactions:")
        for i, tx_model in enumerate(processed_transactions[:3]): # Display first 3
            print(f"\nTransaction {i+1}:")
            print(f"  Hash: {tx_model.hash}")
            print(f"  Timestamp: {tx_model.timestamp_dt} (Original: {tx_model.timeStamp})")
            print(f"  From: {tx_model.from_address}")
            print(f"  To: {tx_model.to_address}")
            print(f"  Value (Wei): {wei_to_ether_str(tx_model.value)} (Original Wei: {tx_model.value})")
            print(f"  Gas Used: {tx_model.gasUsed}, Gas Price: {wei_to_gwei_str(tx_model.gasPrice)} (Original Wei: {tx_model.gasPrice})")
            if tx_model.gasFeeInWei:
                print(f"  Calculated Gas Fee: {wei_to_ether_str(tx_model.gasFeeInWei)} (Original Wei: {tx_model.gasFeeInWei})")
            else:
                print(f"  Calculated Gas Fee (Wei): None")
            print(f"  Is Error: {tx_model.isError}, TxReceipt Status: {tx_model.txreceipt_status}")
    
    return processed_transactions

def filter_transactions_by_timeframe(
    transactions: List[BaseTransaction], 
    timeframe_start: datetime, 
    timeframe_end: datetime
) -> List[BaseTransaction]:
    """
    Filters transactions whose timestamp_dt falls within the [timeframe_start, timeframe_end] range (inclusive).
    """
    filtered_txs = []
    for tx in transactions:
        if tx.timestamp_dt and timeframe_start <= tx.timestamp_dt <= timeframe_end:
            filtered_txs.append(tx)
    return filtered_txs

def aggregate_gas_fees(transactions: List[BaseTransaction]) -> int:
    """
    Sums up the gasFeeInWei for all transactions in the provided list.
    Handles potential None or invalid values for gasFeeInWei by treating them as 0.
    Returns the total gas fee in Wei as an integer.
    """
    total_gas_fee_wei = 0
    for tx in transactions:
        if tx.gasFeeInWei:
            try:
                total_gas_fee_wei += int(tx.gasFeeInWei)
            except (ValueError, TypeError):
                # print(f"Warning: Could not parse gasFeeInWei '{tx.gasFeeInWei}' for tx {tx.hash}. Skipping.")
                pass # Treat as 0 if not a valid integer string
    return total_gas_fee_wei

def get_gas_spent_for_period(
    transactions: List[BaseTransaction], 
    period_days: Optional[int] = None, 
    custom_start_date: Optional[datetime] = None, 
    custom_end_date: Optional[datetime] = None
) -> int:
    """
    Calculates total gas spent in Wei for a given period.
    """
    if not transactions:
        return 0

    target_transactions = transactions

    if period_days is not None:
        now = datetime.now()
        timeframe_end = now
        timeframe_start = now - timedelta(days=period_days)
        print(f"Filtering for period: {timeframe_start.strftime('%Y-%m-%d')} to {timeframe_end.strftime('%Y-%m-%d')}")
        target_transactions = filter_transactions_by_timeframe(transactions, timeframe_start, timeframe_end)
    elif custom_start_date and custom_end_date:
        print(f"Filtering for custom period: {custom_start_date.strftime('%Y-%m-%d')} to {custom_end_date.strftime('%Y-%m-%d')}")
        target_transactions = filter_transactions_by_timeframe(transactions, custom_start_date, custom_end_date)
    # If no period or custom dates, process all transactions (target_transactions remains as all transactions)
    
    if not target_transactions: # After filtering, if no transactions match
        print("No transactions found in the specified period.")
        return 0
        
    total_gas_spent_wei = aggregate_gas_fees(target_transactions)
    return total_gas_spent_wei

def prepare_daily_gas_data(transactions: List[BaseTransaction], days_limit: int = 30) -> Dict[date, int]:
    """
    Aggregates total gasFeeInWei for each day for transactions within the last 'days_limit'.

    Args:
        transactions: A list of BaseTransaction objects.
        days_limit: The number of past days to consider transactions from (e.g., 30 for last 30 days).

    Returns:
        A dictionary where keys are date objects and values are total gas fees in Wei for that day,
        sorted by date.
    """
    daily_gas: Dict[date, int] = {}
    if not transactions:
        return daily_gas

    # Determine the date limit
    today = datetime.now().date()
    start_date_limit = today - timedelta(days=days_limit -1) # -1 to include today in the 30 days period

    print(f"Preparing daily gas data from {start_date_limit} to {today} ({days_limit} days period)")

    for tx in transactions:
        if tx.timestamp_dt and tx.gasFeeInWei:
            tx_date = tx.timestamp_dt.date()
            if tx_date >= start_date_limit and tx_date <= today : # Ensure tx is within the desired window
                try:
                    gas_fee_wei = int(tx.gasFeeInWei)
                    daily_gas[tx_date] = daily_gas.get(tx_date, 0) + gas_fee_wei
                except (ValueError, TypeError):
                    # print(f"Warning: Could not parse gasFeeInWei '{tx.gasFeeInWei}' for tx {tx.hash} in daily aggregation. Skipping.")
                    pass
    
    # Sort the dictionary by date
    # Using OrderedDict to maintain insertion order after sorting if needed, 
    # but dicts maintain insertion order in Python 3.7+ anyway.
    # For clarity or older Pythons, OrderedDict is explicit.
    if not daily_gas: # If no transactions fell into the date range
        return {}

    sorted_daily_gas = OrderedDict(sorted(daily_gas.items()))
    
    return dict(sorted_daily_gas) # Return as standard dict


if __name__ == "__main__":
    load_dotenv()

    fetch_and_display_gas_prices()

    print("\n" + "="*50)
    print("Starting Transaction Fetching & Processing")
    print("="*50)
    
    test_wallet = os.getenv("TEST_WALLET_ADDRESS")
    all_fetched_transactions: List[BaseTransaction] = []

    if not test_wallet:
        print("\nWarning: TEST_WALLET_ADDRESS not found in .env. Set it to test transaction fetching.")
        test_wallet = "0x0000000000000000000000000000000000000000" # Use placeholder
        print(f"Using placeholder address for transaction fetching: {test_wallet}")

    if test_wallet and test_wallet != "0x0000000000000000000000000000000000000000":
        all_fetched_transactions = fetch_and_process_transactions(test_wallet)
        if all_fetched_transactions:
            print(f"\nTotal of {len(all_fetched_transactions)} transactions processed for wallet {test_wallet}.")
        else:
            # This message will print if API fails or if wallet truly has no transactions
            print(f"\nNo transactions were processed or returned for wallet {test_wallet} (this could be due to API errors, no transactions, or filters).")
    else: # This case handles if test_wallet was initially empty and then set to placeholder
        print("\nSkipping actual transaction fetching as TEST_WALLET_ADDRESS was not meaningfully set.")

    # --- Gas Aggregation (always attempt to run, even if all_fetched_transactions is empty) ---
    print("\n" + "="*50)
    print("Calculating Gas Spent Over Different Periods")
    print("="*50)

    # Fetch current ETH price once
    basescan_api_key_env = os.getenv("BASESCAN_API_KEY") # Re-fetch for clarity, or pass from above
    eth_usd_price: Optional[Decimal] = None
    if basescan_api_key_env: # Ensure API key exists before trying to fetch price
        print("Fetching current ETH to USD price from Basescan...")
        eth_usd_price = get_eth_current_price(basescan_api_key_env)
        if eth_usd_price:
            print(f"Current ETH price: ${eth_usd_price:.2f} USD")
        else:
            print("Could not retrieve current ETH price. USD values will not be calculated.")
    else:
        print("BASESCAN_API_KEY not found in .env. Skipping ETH price fetch and USD calculations for gas totals.")


    if not all_fetched_transactions:
        print("No transactions available for gas calculation (either fetching failed, TEST_WALLET_ADDRESS was not set, or it has no transactions). Reporting 0 ETH spent.")

    # Helper function to format output string with optional USD value
    def format_gas_output(label: str, wei_amount: int, eth_price: Optional[Decimal]) -> str:
        # Ensure wei_amount is an int for calculate_fiat_value.
        # get_gas_spent_for_period already returns int.
        # wei_to_ether_str was updated to accept int.
        eth_str = wei_to_ether_str(wei_amount) 
        output = f"Total Gas Spent ({label}): {eth_str} (Wei: {wei_amount})"
        if eth_price: # Check if eth_usd_price was successfully fetched
            usd_value = calculate_fiat_value(wei_amount, eth_price)
            if usd_value is not None:
                output += f" (${usd_value:.2f} USD)"
            else:
                # This case might happen if wei_amount is huge and causes overflow with price, though unlikely with Decimal
                output += " ($--.-- USD - calculation error)"
        # If eth_price is None, USD part is implicitly skipped by the if eth_price: condition.
        # Adding an explicit message if price wasn't available for clarity.
        elif not basescan_api_key_env or not eth_usd_price: # Check original reason for no price
             output += " (USD conversion not available - ETH price not fetched)"
        return output

    # Last 7 days
    gas_7_days_wei = get_gas_spent_for_period(all_fetched_transactions, period_days=7)
    print(format_gas_output("Last 7 Days", gas_7_days_wei, eth_usd_price))
    
    # Last 30 days
    gas_30_days_wei = get_gas_spent_for_period(all_fetched_transactions, period_days=30)
    print(format_gas_output("Last 30 Days", gas_30_days_wei, eth_usd_price))

    # All time (based on fetched transactions)
    gas_all_time_wei = get_gas_spent_for_period(all_fetched_transactions) # No period specified
    print(format_gas_output("All Fetched Transactions", gas_all_time_wei, eth_usd_price))
    
    # Example for a custom period - kept commented out as it requires specific data
    # ... (custom period example code remains unchanged) ...

    # --- Graph Generation (New) ---
    print("\n" + "="*50)
    print("Generating Gas Spending Graph")
    print("="*50)

    # Prepare data for the graph (e.g., last 30 days)
    # This uses all_fetched_transactions which might be empty if API calls failed
    # The prepare_daily_gas_data and generate_gas_spending_graph functions should handle empty data.
    daily_data_for_graph = prepare_daily_gas_data(all_fetched_transactions, days_limit=30)
    
    if daily_data_for_graph:
        print(f"Prepared {len(daily_data_for_graph)} days of data for the graph.")
        # Dynamically import here or at the top if preferred
        try:
            from graph_generator import generate_gas_spending_graph
            
            # Generate PNG graph
            png_graph_filename = "gas_spending_last_30_days.png"
            png_generated = generate_gas_spending_graph(daily_data_for_graph, png_graph_filename)
            if png_generated:
                print(f"Gas spending graph (PNG) generated: {png_graph_filename}")
            else:
                print("PNG graph generation failed or was skipped due to no data.")

            # Generate PDF graph if PNG was successful
            if png_generated: # Only attempt PDF if data was good enough for PNG
                pdf_graph_filename = "gas_spending_last_30_days.pdf"
                if generate_gas_spending_graph(daily_data_for_graph, pdf_graph_filename):
                    print(f"Gas spending graph (PDF) generated: {pdf_graph_filename}")
                else:
                    # This might happen if, for some reason, PDF saving fails while PNG worked,
                    # or if the function itself has an issue specifically with PDF.
                    print(f"PDF graph generation failed for {pdf_graph_filename}.")
            
        except ImportError:
            print("Could not import graph_generator. Skipping graph generation. Ensure graph_generator.py exists.")
        except Exception as e:
            print(f"An error occurred during graph generation: {e}")
    else:
        print("No daily gas data available to generate a graph (transactions might be outside the 30-day window or fetching failed).")
