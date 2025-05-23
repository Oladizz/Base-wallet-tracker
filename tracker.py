import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pydantic import ValidationError
from datetime import datetime, timedelta, date
from collections import OrderedDict
from decimal import Decimal

# Assuming other modules are in the same directory or accessible via PYTHONPATH
from etherscan_api import get_current_base_fee
from base_rpc import get_current_base_l2_gas_price
from basescan_api import get_account_normal_transactions, get_eth_current_price
from models import BaseTransaction
from utils import wei_to_ether_str, wei_to_gwei_str, calculate_fiat_value, wei_to_gwei_decimal
# graph_generator might be imported later or within specific functions

# Initial load_dotenv at module level for CLI or if functions are called directly
load_dotenv()

def fetch_and_display_gas_prices():
    """
    Fetches and displays:
    1. Ethereum current suggested base gas fee from Etherscan.
    2. Base L2 current gas price using a configured RPC URL.
    (This function is more for CLI use now, as get_wallet_gas_report handles this for web)
    """
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


def fetch_and_process_transactions(wallet_address: str) -> tuple[List[BaseTransaction], Optional[str]]:
    """
    Fetches normal transactions for a wallet from Basescan, processes them into
    BaseTransaction models.
    Returns a list of BaseTransaction objects and an optional error message string.
    """
    basescan_api_key = os.getenv("BASESCAN_API_KEY")
    if not basescan_api_key:
        # This case should ideally be caught before calling this function by get_wallet_gas_report
        return [], "BASESCAN_API_KEY not found in environment variables."

    # print(f"\nFetching normal transactions for wallet: {wallet_address} from Basescan...") # Reduce console noise for web
    raw_tx_data_list, api_error_msg = get_account_normal_transactions(
        api_key=basescan_api_key,
        wallet_address=wallet_address,
        offset=100 # Fetch more for better summary
    )

    processed_transactions: List[BaseTransaction] = []
    if api_error_msg:
        # print(f"API Error from get_account_normal_transactions: {api_error_msg}") # Reduce noise
        return [], api_error_msg 

    if not raw_tx_data_list:
        # print("No transactions found for this address (according to API).") # Reduce noise
        return [], None # No data, but no direct API error to report upwards

    # print(f"Retrieved {len(raw_tx_data_list)} raw transactions. Processing...") # Reduce noise
    for tx_data in raw_tx_data_list:
        try:
            transaction = BaseTransaction(**tx_data)
            processed_transactions.append(transaction)
        except ValidationError as e:
            print(f"Warning: Could not validate transaction data for tx hash {tx_data.get('hash', 'N/A')}: {e.errors()}")
        except Exception as e:
            print(f"Warning: An unexpected error occurred processing tx hash {tx_data.get('hash', 'N/A')}: {e}")
    
    # CLI display removed from here, will be handled by CLI specific part in __main__ if needed
            
    return processed_transactions, None


def filter_transactions_by_timeframe(
    transactions: List[BaseTransaction], 
    timeframe_start: datetime, 
    timeframe_end: datetime
) -> List[BaseTransaction]:
    filtered_txs = []
    for tx in transactions:
        if tx.timestamp_dt and timeframe_start <= tx.timestamp_dt <= timeframe_end:
            filtered_txs.append(tx)
    return filtered_txs

def aggregate_gas_fees(transactions: List[BaseTransaction]) -> int:
    total_gas_fee_wei = 0
    for tx in transactions:
        if tx.gasFeeInWei:
            try:
                total_gas_fee_wei += int(tx.gasFeeInWei)
            except (ValueError, TypeError):
                pass 
    return total_gas_fee_wei

def get_gas_spent_for_period(
    transactions: List[BaseTransaction], 
    period_days: Optional[int] = None, 
    custom_start_date: Optional[datetime] = None, 
    custom_end_date: Optional[datetime] = None
) -> int:
    if not transactions:
        return 0
    target_transactions = transactions
    if period_days is not None:
        now = datetime.now()
        timeframe_end = now
        timeframe_start = now - timedelta(days=period_days)
        # print(f"Filtering for period: {timeframe_start.strftime('%Y-%m-%d')} to {timeframe_end.strftime('%Y-%m-%d')}") # Reduce noise
        target_transactions = filter_transactions_by_timeframe(transactions, timeframe_start, timeframe_end)
    elif custom_start_date and custom_end_date:
        # print(f"Filtering for custom period: {custom_start_date.strftime('%Y-%m-%d')} to {custom_end_date.strftime('%Y-%m-%d')}") # Reduce noise
        target_transactions = filter_transactions_by_timeframe(transactions, custom_start_date, custom_end_date)
    
    if not target_transactions:
        # print("No transactions found in the specified period for gas calculation.") # Reduce noise
        return 0
    return aggregate_gas_fees(target_transactions)

def prepare_daily_gas_data(transactions: List[BaseTransaction], days_limit: int = 30) -> Dict[date, int]:
    daily_gas: Dict[date, int] = {}
    if not transactions:
        return daily_gas
    today = datetime.now().date()
    start_date_limit = today - timedelta(days=days_limit - 1)
    # print(f"Preparing daily gas data from {start_date_limit} to {today} ({days_limit} days period)") # Reduce noise
    for tx in transactions:
        if tx.timestamp_dt and tx.gasFeeInWei:
            tx_date = tx.timestamp_dt.date()
            if start_date_limit <= tx_date <= today:
                try:
                    gas_fee_wei = int(tx.gasFeeInWei)
                    daily_gas[tx_date] = daily_gas.get(tx_date, 0) + gas_fee_wei
                except (ValueError, TypeError):
                    pass
    if not daily_gas:
        return {}
    return dict(OrderedDict(sorted(daily_gas.items())))

# --- Main Orchestration Function ---
def get_wallet_gas_report(wallet_address: str) -> Dict:
    report_data = {
        "wallet_address": wallet_address,
        "current_l2_gas_price_gwei": "N/A",
        "current_eth_usd_price": "N/A",
        "gas_summary": {
            "all_time": {"eth": "0.00 ETH", "usd": "$0.00 USD", "wei": 0},
            "last_30_days": {"eth": "0.00 ETH", "usd": "$0.00 USD", "wei": 0},
            "last_7_days": {"eth": "0.00 ETH", "usd": "$0.00 USD", "wei": 0},
        },
        "transactions": [], # This will be list of dicts for template
        "graph_url": None,
        "error_messages": []
    }
    # load_dotenv() already called at module level

    # 1. Fetch current L2 gas price
    base_rpc_url = os.getenv("BASE_RPC_URL")
    if base_rpc_url:
        l2_gas_price_gwei_decimal = get_current_base_l2_gas_price(base_rpc_url)
        if l2_gas_price_gwei_decimal is not None:
            report_data["current_l2_gas_price_gwei"] = f"{l2_gas_price_gwei_decimal:.2f} Gwei"
        else:
            report_data["error_messages"].append("Failed to retrieve Base L2 gas price.")
            report_data["current_l2_gas_price_gwei"] = "Error fetching L2 price" # Shorter for UI
    else:
        report_data["error_messages"].append("BASE_RPC_URL not found in .env.")
        report_data["current_l2_gas_price_gwei"] = "RPC URL not configured"

    # 2. Fetch current ETH to USD price
    basescan_api_key = os.getenv("BASESCAN_API_KEY")
    eth_usd_price_decimal: Optional[Decimal] = None
    if basescan_api_key:
        eth_usd_price_decimal = get_eth_current_price(basescan_api_key)
        if eth_usd_price_decimal:
            report_data["current_eth_usd_price"] = f"${eth_usd_price_decimal:.2f} USD"
        else:
            report_data["error_messages"].append("Failed to retrieve current ETH to USD price.")
            report_data["current_eth_usd_price"] = "Error fetching ETH price" # Shorter for UI
    else:
        report_data["error_messages"].append("BASESCAN_API_KEY not found. ETH price and transactions cannot be fetched.")
        report_data["current_eth_usd_price"] = "API Key missing"

    # 3. Fetch and process transactions
    raw_transactions_from_api: List[BaseTransaction] = []
    if basescan_api_key: 
        fetched_tx_list, tx_api_error_msg = fetch_and_process_transactions(wallet_address)
        if tx_api_error_msg:
            report_data["error_messages"].append(f"Could not fetch transactions: {tx_api_error_msg}")
        raw_transactions_from_api = fetched_tx_list
        if not raw_transactions_from_api and not tx_api_error_msg:
            report_data["error_messages"].append(f"No transactions found for wallet {wallet_address}.")
    # else: BASESCAN_API_KEY missing message already added to error_messages

    template_transactions = []
    for tx in raw_transactions_from_api[:20]: 
        gas_fee_usd_str = "$--.-- USD"
        if tx.gasFeeInWei and eth_usd_price_decimal:
            try:
                gas_fee_wei_int = int(tx.gasFeeInWei)
                fiat_val = calculate_fiat_value(gas_fee_wei_int, eth_usd_price_decimal)
                if fiat_val is not None: gas_fee_usd_str = f"${fiat_val:.2f} USD"
            except (ValueError, TypeError): gas_fee_usd_str = "$Error USD"
        template_transactions.append({
            "hash": tx.hash,
            "timestamp_dt_str": tx.timestamp_dt.strftime('%Y-%m-%d %H:%M:%S') if tx.timestamp_dt else tx.timeStamp,
            "from_address": tx.from_address, "to_address": tx.to_address,
            "value_eth_str": tx.value_eth_str, "gas_fee_eth_str": tx.gas_fee_eth_str,
            "gas_fee_usd_str": gas_fee_usd_str
        })
    report_data["transactions"] = template_transactions

    # 4. Calculate gas summaries
    periods = {
        "all_time": get_gas_spent_for_period(raw_transactions_from_api),
        "last_30_days": get_gas_spent_for_period(raw_transactions_from_api, period_days=30),
        "last_7_days": get_gas_spent_for_period(raw_transactions_from_api, period_days=7),
    }
    for period_name, wei_amount in periods.items():
        eth_str = wei_to_ether_str(wei_amount)
        usd_str = "$--.-- USD"
        if eth_usd_price_decimal:
            fiat_val = calculate_fiat_value(wei_amount, eth_usd_price_decimal)
            if fiat_val is not None: usd_str = f"${fiat_val:.2f} USD"
        report_data["gas_summary"][period_name] = {"eth": eth_str, "usd": usd_str, "wei": wei_amount}
    
    # 5. Prepare data for and generate graph
    if raw_transactions_from_api:
        daily_data_for_graph = prepare_daily_gas_data(raw_transactions_from_api, days_limit=30)
        if daily_data_for_graph:
            static_images_dir = os.path.join('static', 'images')
            os.makedirs(static_images_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            short_wallet = wallet_address[:6] + "_" + wallet_address[-4:]
            png_filename_base = f"gas_graph_{short_wallet}_{timestamp}.png"
            png_filepath = os.path.join(static_images_dir, png_filename_base)
            try:
                from graph_generator import generate_gas_spending_graph
                if generate_gas_spending_graph(daily_data_for_graph, png_filepath):
                    report_data["graph_url"] = f"/static/images/{png_filename_base}"
                else:
                    report_data["error_messages"].append("Graph generation failed (PNG).")
            except ImportError:
                report_data["error_messages"].append("Graph generator module not found.")
            except Exception as e:
                report_data["error_messages"].append(f"An error occurred during graph generation: {e}")
        elif raw_transactions_from_api: 
             report_data["error_messages"].append("No recent transactions in the last 30 days to generate a graph.")
            
    return report_data

# --- Main Execution (for CLI usage) ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Gas Tracker CLI Mode")
    print("="*50)

    fetch_and_display_gas_prices() 

    test_wallet_cli = os.getenv("TEST_WALLET_ADDRESS")
    if not test_wallet_cli:
        print("\nWarning: TEST_WALLET_ADDRESS not found in .env for CLI mode.")
        test_wallet_cli = input("Enter wallet address to track (or press Enter to skip): ").strip()

    if test_wallet_cli:
        print(f"\nFetching full report for wallet: {test_wallet_cli}...")
        report = get_wallet_gas_report(test_wallet_cli)

        print("\n--- CLI Wallet Report ---")
        print(f"Wallet Address: {report['wallet_address']}")
        print(f"Current Base L2 Gas Price: {report['current_l2_gas_price_gwei']}")
        print(f"Current ETH Price: {report['current_eth_usd_price']}")
        
        print("\nGas Spending Summary:")
        for period, data in report['gas_summary'].items():
            print(f"  {period.replace('_', ' ').title()}: {data['eth']} ({data['usd']})")

        if report['graph_url']:
            print(f"\nGas Spending Graph (Last 30 Days): {report['graph_url']} (Run app.py to view via web)")
        
        if report['transactions']: 
            print(f"\nDisplaying up to {len(report['transactions'])} recent transactions (details pre-formatted for web):")
            for i, tx_dict in enumerate(report['transactions']):
                print(f"\n  Transaction {i+1}:")
                print(f"    Hash: {tx_dict['hash']}")
                print(f"    Timestamp: {tx_dict['timestamp_dt_str']}")
                print(f"    From: {tx_dict['from_address']}")
                print(f"    To: {tx_dict['to_address']}")
                print(f"    Value: {tx_dict['value_eth_str']}")
                print(f"    Gas Fee: {tx_dict['gas_fee_eth_str']} ({tx_dict['gas_fee_usd_str']})")
        
        if report['error_messages']:
            print("\nErrors/Warnings during report generation:")
            for msg in report['error_messages']:
                print(f"- {msg}")
        print("\n--- End of CLI Report ---")
    else:
        print("\nNo wallet address provided for CLI report. Skipping.")
