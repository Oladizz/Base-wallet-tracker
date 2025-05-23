# Gas Fee Wallet Tracker - Backend Design

## 1. Main Python Script(s)

*   **`tracker.py`**: This will be the main script responsible for orchestrating the gas fee tracking process. It will likely contain the primary logic for fetching, processing, and displaying gas fee information.
*   **`etherscan_api.py`**: (Optional, but recommended for modularity) This script could encapsulate all interactions with the Etherscan API, such as fetching transactions.
*   **`models.py`**: This script will define the Pydantic models for structuring transaction data.

## 2. Key Functions

### a. Fetching Transaction History

*   **Blockchain:** Ethereum
*   **Method:** Etherscan API (specifically, the `account` action with the `txlist` module)
*   **Function (in `etherscan_api.py` or `tracker.py`):**
    ```python
    def get_transactions(api_key: str, wallet_address: str, start_block: int = 0, end_block: int = 99999999, sort: str = "asc") -> list:
        """
        Fetches transaction history for a given Ethereum wallet address using the Etherscan API.
        
        Args:
            api_key: The Etherscan API key.
            wallet_address: The Ethereum wallet address.
            start_block: The starting block number to fetch transactions from.
            end_block: The ending block number to fetch transactions up to.
            sort: The sorting order of transactions ('asc' or 'desc').

        Returns:
            A list of transactions if successful, otherwise an empty list or raises an exception.
        """
        # Implementation details:
        # - Construct the Etherscan API URL.
        # - Make a GET request using the `requests` library.
        # - Handle API response (check for errors, parse JSON).
        # - Return the list of transactions.
        pass
    ```

### b. Extracting Relevant Information

*   **Function (in `tracker.py`):**
    ```python
    def extract_transaction_details(transactions: list, wallet_address: str) -> list:
        """
        Extracts relevant information (timestamp, gas used, gas price, gas fee, tx hash) 
        from a list of transactions.

        Args:
            transactions: A list of transaction data from Etherscan.
            wallet_address: The wallet address being analyzed (to determine if it's the sender).

        Returns:
            A list of Pydantic Transaction models.
        """
        # Implementation details:
        # - Iterate through each transaction.
        # - For each transaction, extract:
        #   - `timeStamp`
        #   - `gasUsed`
        #   - `gasPrice`
        #   - Calculate `gasFee = gasUsed * gasPrice` (convert to Ether if necessary)
        #   - `hash` (transaction hash)
        #   - Determine if the transaction was outgoing (wallet_address is the sender)
        # - Populate and return a list of Transaction Pydantic models.
        pass
    ```

### c. Calculating Total Gas Fees

*   **Function (in `tracker.py`):**
    ```python
    def calculate_total_gas_fees(processed_transactions: list) -> float:
        """
        Calculates the total gas fees paid for outgoing transactions.

        Args:
            processed_transactions: A list of Pydantic Transaction models.

        Returns:
            The total gas fees paid in Ether.
        """
        # Implementation details:
        # - Initialize total_fees = 0.0.
        # - Iterate through `processed_transactions`.
        # - If the transaction was outgoing (sender == wallet_address), add its `gasFee` to `total_fees`.
        # - Return `total_fees`.
        pass
    ```

## 3. Proposed Data Structures

We will use Pydantic models for data validation and structure.

*   **`models.py`:**
    ```python
    from pydantic import BaseModel
    from datetime import datetime

    class Transaction(BaseModel):
        timestamp: datetime
        gas_used: int
        gas_price: int  # Store in Wei
        gas_fee: float  # Store in Ether
        transaction_hash: str
        is_outgoing: bool 
    ```

## 4. Core Python Libraries

*   **`requests`**: For making HTTP requests to the Etherscan API.
*   **`python-dotenv`**: For managing environment variables (like API keys).
*   **`pydantic`**: For data validation, settings management, and defining data models like `BaseTransaction`.
*   **`web3.py`**: For interacting with Ethereum-compatible blockchains, used here for Base L2 gas price.

## 5. Modules and Key Components

*   **`tracker.py`**: Main executable script. Orchestrates fetching gas prices and transaction data.
*   **`etherscan_api.py`**: Handles communication with the Etherscan API (for Ethereum L1 gas fees).
*   **`base_rpc.py`**: Handles communication with Base L2 RPC endpoints (for Base L2 gas prices using `web3.py`).
*   **`basescan_api.py`**: Handles communication with the Basescan API (for Base L2 transaction history).
*   **`models.py`**: Defines Pydantic data models, currently `BaseTransaction`.
*   **`utils.py`**: Provides utility functions, such as Wei to Ether/Gwei string/Decimal conversions and fiat value calculation.
*   **`graph_generator.py`**: Responsible for generating a Matplotlib graph of daily gas spending.

## 6. Configuration Management

*   **API Keys & URLs:** Stored in a `.env` file. Refer to `.env.example` for all required variables.
    Key variables include:
    ```dotenv
    ETHERSCAN_API_KEY="YOUR_ETHERSCAN_API_KEY"
    BASE_RPC_URL="YOUR_BASE_RPC_URL" 
    BASESCAN_API_KEY="YOUR_BASESCAN_API_KEY"
    TEST_WALLET_ADDRESS="YOUR_TEST_BASE_WALLET_ADDRESS" # Optional, for testing
    ```
*   The `python-dotenv` library is used to load these.

## 7. Features

### 7.1. Fetching Current Gas Prices (Ethereum L1 & Base L2)

The application can fetch and display:
1.  The current suggested base gas fee for **Ethereum (L1)** using the Etherscan API.
2.  The current gas price for **Base (L2)** using a configured RPC URL via `web3.py`.

#### Setup for Gas Prices:

1.  Ensure `.env` file is created from `.env.example`.
2.  Set `ETHERSCAN_API_KEY` for Ethereum L1 gas fees.
3.  Set `BASE_RPC_URL` for Base L2 gas prices.

#### Usage:
Running `python tracker.py` will automatically attempt to fetch and display these prices.

### 7.2. Fetching, Processing, and Analyzing Base L2 Transactions (Including Fiat Conversion & Graph Generation)

The application can retrieve 'Normal' transaction history for a given wallet address on the Base blockchain using the Basescan API. It then processes this data to calculate total gas fees spent over various periods, converts these fees to USD (if ETH price is available), and generates a visual graph of daily spending.

#### Data Model (`models.py:BaseTransaction`):
A Pydantic model `BaseTransaction` is used to structure and validate transaction data. Key fields include:
*   `blockNumber: str`
*   `timeStamp: str` (original string from API)
*   `hash: str`
*   `from_address: str` (alias for 'from')
*   `to_address: str` (alias for 'to')
*   `value: str` (in Wei)
*   `gas: str`, `gasPrice: str`, `gasUsed: str`
*   `isError: str` ("0" for no error, "1" for error)
*   `txreceipt_status: str` (API specific, often "" or "1" for success)
*   **Calculated Fields:**
    *   `gasFeeInWei: Optional[str]` (calculated as `gasUsed * gasPrice`)
    *   `timestamp_dt: Optional[datetime]` (converted from `timeStamp`)

#### API Interaction (`basescan_api.py`):
*   The `get_account_normal_transactions(...)` function queries the Basescan `account txlist` endpoint.
*   It handles API responses, pagination parameters, and basic error checking.

#### Processing (`tracker.py`):
*   The `fetch_and_process_transactions(wallet_address: str)` function:
    *   Retrieves `BASESCAN_API_KEY` from environment variables.
    *   Calls `basescan_api.get_account_normal_transactions`.
    *   Parses each returned raw transaction dictionary into a `BaseTransaction` model instance.
    *   Handles validation errors gracefully (skips and logs warnings).
    *   Prints a summary and details of the first few transactions, now displaying values in Ether/Gwei using `utils.py`.
*   **Gas Fee Aggregation (`tracker.py`)**:
    *   `filter_transactions_by_timeframe(...)`: Filters transactions based on a start and end datetime.
    *   `aggregate_gas_fees(...)`: Sums up `gasFeeInWei` from a list of transactions.
    *   `get_gas_spent_for_period(...)`: Orchestrates filtering and aggregation for predefined periods (e.g., last 7 days, last 30 days) or custom date ranges.

#### Utility Functions (`utils.py`):
*   `wei_to_ether_str(wei_value)`: Converts Wei (str, int, or Decimal) to a formatted Ether string.
*   `wei_to_gwei_str(wei_value_str)`: Converts a Wei string to a formatted Gwei string.
*   `wei_to_gwei_decimal(wei_value_str)`: Converts a Wei string to a Decimal value in Gwei.
*   `calculate_fiat_value(wei_amount_int, eth_to_usd_price)`: Calculates USD value from Wei amount and ETH price.

#### Fiat Currency Conversion:
*   The application now attempts to fetch the current ETH to USD price from the Basescan API (`stats` module, `ethprice` action) once per run using the `BASESCAN_API_KEY`.
*   If successful, the aggregated gas fee totals (for 7-day, 30-day, all-time) are displayed in both ETH and USD.
*   If the ETH price cannot be fetched (e.g., API key issue, network error), a warning is printed, and USD values are omitted.

#### Graph Generation (`graph_generator.py`):
*   The `generate_gas_spending_graph(daily_gas_data, output_filename)` function:
    *   Takes daily aggregated gas data (date -> Wei).
    *   If data is empty, it skips graph generation.
    *   Generates a line chart using Matplotlib:
        *   X-axis: Dates.
        *   Y-axis: Gas spent in Gwei.
    *   Includes axis labels, title, and readable date formatting.
    *   Saves the graph to the specified output file. Matplotlib infers the format (e.g., PNG, PDF) from the filename extension.
*   `tracker.py` calls this function with data from the last 30 days of transactions, first to generate a `.png` file and then, if successful, a `.pdf` file.

#### Setup for Transaction Fetching, Analysis & Graphing:

1.  Ensure `.env` file is created and configured.
2.  Set `BASESCAN_API_KEY` with your Basescan API key.
3.  Set `TEST_WALLET_ADDRESS` in your `.env` file to a Base blockchain address.

#### Usage and Example Output:
When `tracker.py` is run with `TEST_WALLET_ADDRESS` and `BASESCAN_API_KEY` configured:
1.  It fetches and processes transactions.
2.  It then calculates and prints the total gas fees spent by that address on Base for:
    *   The last 7 days.
    *   The last 30 days.
    *   All fetched transactions ("all time").
3.  If transaction data is available, it generates:
    *   A PNG image file (`gas_spending_last_30_days.png`).
    *   A PDF document (`gas_spending_last_30_days.pdf`).
    Both files visualize daily gas expenses over the last 30 days.

Example output snippet for transaction details:
```
Transaction 1:
  Hash: 0xabcdef...
  Timestamp: 2023-10-26 12:30:00 (Original: 1698318600)
  From: 0xfromAddress...
  To: 0xtoAddress...
  Value (Wei): 0.10 ETH (Original Wei: 100000000000000000)
  Gas Used: 21000, Gas Price: 1 Gwei (Original Wei: 1000000000)
  Calculated Gas Fee: 0.000021 ETH (Original Wei: 21000000000000)
  Is Error: 0, TxReceipt Status: 1
```

Example output for gas fee aggregation:
```
==================================================
Calculating Gas Spent Over Different Periods
==================================================
Filtering for period: YYYY-MM-DD to YYYY-MM-DD
Total Gas Spent (Last 7 Days): X.XXXX ETH (Wei: XXXXXXXXXXXXXXX)
Filtering for period: YYYY-MM-DD to YYYY-MM-DD
Total Gas Spent (Last 30 Days): Y.YYYY ETH (Wei: YYYYYYYYYYYYYYY)
Total Gas Spent (All Fetched Transactions): Z.ZZZZ ETH (Wei: ZZZZZZZZZZZZZZZ)

==================================================
Calculating Gas Spent Over Different Periods
==================================================
Fetching current ETH to USD price from Basescan...
Current ETH price: $2000.00 USD 
Total Gas Spent (Last 7 Days): 0.0123 ETH (Wei: 12300000000000000) ($24.60 USD)
Total Gas Spent (Last 30 Days): 0.0456 ETH (Wei: 45600000000000000) ($91.20 USD)
Total Gas Spent (All Fetched Transactions): 0.1234 ETH (Wei: 123400000000000000) ($246.80 USD)

==================================================
Generating Gas Spending Graph
==================================================
Prepared X days of data for the graph.
Gas spending graph (PNG) generated: gas_spending_last_30_days.png
Gas spending graph (PDF) generated: gas_spending_last_30_days.pdf
```
(Actual ETH price and gas amounts will vary. If ETH price cannot be fetched, the USD part will be omitted or show an error.)

If `BASESCAN_API_KEY` or `TEST_WALLET_ADDRESS` are missing, appropriate warnings are shown. Graph generation might be skipped if no data can be fetched/processed.

**Note on `.gitignore`**: Generated image and document files like `*.png` and `*.pdf` are included in the `.gitignore` file.

## 8. Running Unit Tests

The project includes a suite of unit tests to ensure individual components function correctly.

### Setup for Testing

No additional setup beyond installing requirements is generally needed for most tests, as API calls and external services are mocked.

### Running Tests

To run the unit tests, navigate to the root directory of the project in your terminal and execute the following command:

```bash
python -m unittest discover tests
```

This command will automatically discover and run all test cases defined in the `tests/` directory. You should see output indicating the number of tests run and their status (e.g., "OK" if all pass, or details of failures/errors).

Example of a successful test run output:
```
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.123s

OK
```

Details of the first few processed transactions:

Transaction 1:
  Hash: 0xabcdef...
  Timestamp: 2023-10-26 12:30:00 (Original: 1698318600)
  From: 0xfromAddress...
  To: 0xtoAddress...
  Value (Wei): 100000000000000000
  Gas Used: 21000, Gas Price: 1000000000 (Wei)
  Calculated Gas Fee (Wei): 21000000000000
  Is Error: 0, TxReceipt Status: 1
```
(Actual output will depend on the transactions of the `TEST_WALLET_ADDRESS`.)
If `BASESCAN_API_KEY` or `TEST_WALLET_ADDRESS` (if script relies on it solely) are missing, appropriate warnings are shown.
```
