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
*   **`Flask`**: For serving the web frontend.

## 5. Modules and Key Components

*   **`tracker.py`**: Main executable script. Orchestrates fetching gas prices and transaction data.
*   **`etherscan_api.py`**: Handles communication with the Etherscan API (for Ethereum L1 gas fees).
*   **`base_rpc.py`**: Handles communication with Base L2 RPC endpoints (for Base L2 gas prices using `web3.py`).
*   **`basescan_api.py`**: Handles communication with the Basescan API (for Base L2 transaction history).
*   **`models.py`**: Defines Pydantic data models, currently `BaseTransaction`.
*   **`utils.py`**: Provides utility functions (Wei conversions, fiat calculation).
*   **`graph_generator.py`**: Generates Matplotlib graphs.
*   **`app.py`**: Flask application file, serving the web interface.

### Key Functions Refactoring in `tracker.py`

The core data processing logic in `tracker.py` has been refactored into a main function:
*   `get_wallet_gas_report(wallet_address: str) -> dict`: This function orchestrates all data fetching (transactions, current gas prices, ETH price), processing, summary calculations (ETH and USD values), and graph generation. It saves the graph to `static/images/` with a unique name and returns a dictionary containing all data required by the web frontend.

## 6. Configuration Management

To run the application, you'll need to provide your own API keys and settings. This is done using a `.env` file in the project root.

**Steps to set up your environment:**

1.  **Create a `.env` file**:
    You can create this file by copying either the provided template files. Choose one:
    *   Copy `.env.example`: 
        ```bash
        cp .env.example .env
        ```
    *   Or, copy `configuration.template.env`:
        ```bash
        cp configuration.template.env .env
        ```
    Both template files contain the same placeholder content.

2.  **Edit the `.env` file**:
    Open the newly created `.env` file with a text editor. You will see placeholder values like `YourEtherscanApiKeyTokenHere`. 
    Replace these placeholders with your actual API keys and desired settings. For example:
    ```dotenv
    # Etherscan API Key (if using Ethereum features)
    ETHERSCAN_API_KEY=YOUR_ACTUAL_ETHERSCAN_API_KEY_HERE

    # Base Blockchain RPC URL
    BASE_RPC_URL=https://mainnet.base.org # Or your preferred Base RPC URL

    # Basescan API Key
    BASESCAN_API_KEY=YOUR_ACTUAL_BASESCAN_API_KEY_HERE

    # Test Wallet Address (optional, for testing transaction fetching)
    TEST_WALLET_ADDRESS=YOUR_ACTUAL_TEST_WALLET_ADDRESS_HERE
    ```

3.  **Do Not Commit `.env`**: 
    The `.env` file contains your secret API keys and should **never** be committed to version control (e.g., Git). The project's `.gitignore` file is already configured to ignore `.env` files, so you don't need to do anything extra here, but it's crucial to be aware of this.

The application uses the `python-dotenv` library to automatically load these variables from the `.env` file when it runs.

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
    *   A PDF document (`gas_spending_last_30_days.pdf`). (Note: PDF generation is primarily for CLI use; the web frontend displays the PNG).
    Both files visualize daily gas expenses.

### Web Interface Styling

The web frontend (`index.html`, `results.html`) is styled using `static/style.css`. This CSS file implements a "black and tech blue neon" theme:
*   **Overall Theme**: Dark grey/black backgrounds with light grey or neon blue text.
*   **Font**: Modern sans-serif.
*   **Neon Elements**: Headings, links, borders, and interactive elements use bright neon blue (`#00bfff`, `#00ffff`) with text/box shadows to simulate a glow.
*   **Forms**: Input fields and buttons are styled with dark backgrounds and neon borders/text, including hover effects.
*   **Tables**: Styled with neon blue accents for borders and headers.
*   **Error Messages**: Displayed with a distinct neon red color.
*   **Responsiveness**: Basic media queries are included to improve readability and usability on smaller screens, including a stacked layout for tables.

### Web Interface Routes

*   **`/` (GET)**: Serves the main page (`templates/index.html`) where users can input a wallet address.
*   **`/track` (POST)**:
    *   Accepts a `wallet_address` from the form submission.
    *   Calls `tracker.get_wallet_gas_report(wallet_address)` to get all processed data.
    *   Renders `templates/results.html`, passing the report data (including wallet address, gas summaries in ETH & USD, recent transactions, and the URL to the gas spending graph) to the template.
    *   If no wallet address is provided, it redirects back to the home page.
    *   Includes basic validation for the wallet address format. If validation fails, an error message is displayed on the `index.html` page.

### Error Handling and User Feedback

The application incorporates several mechanisms to provide feedback and report errors:
*   **Input Validation**: The wallet address submitted via the form on `index.html` is validated for basic format (starts with '0x', length 42). If it fails, `index.html` re-renders with an error message.
*   **API/Backend Errors**: If errors occur during backend processing (e.g., API key issues, network problems, inability to fetch data from Basescan/RPC, graph generation failures), these are collected in an `error_messages` list.
*   **Display on Results Page**:
    *   The `results.html` page will always attempt to render.
    *   If any errors were collected in `error_messages` by the backend, they are displayed prominently at the top of the `results.html` page, typically styled in neon red.
    *   Sections for which data could not be fetched (e.g., gas summary, transaction list, graph) will either display default values (like "0.00 ETH", "$0.00 USD"), specific messages like "No transactions found...", "Gas spending graph is not available.", or indicate "N/A" or "Error fetching price" for specific data points.
    *   This ensures the user is informed about any issues without breaking the page.

The `results.html` page displays the following information, structured into sections:
*   **Queried Wallet Address**: The address submitted by the user.
*   **Current L2 Gas Price**: Fetched from Base RPC (e.g., "0.05 Gwei").
*   **Current ETH Price**: Fetched from Basescan (e.g., "$2000.00 USD").
*   **Gas Fee Summary**:
    *   Total gas fees spent "All Time" (based on fetched transactions), "Last 30 Days", and "Last 7 Days".
    *   Each period shows the amount in ETH and its approximate USD equivalent (if ETH price is available).
*   **Gas Spending Graph**: A line graph visualizing daily gas expenses in Gwei over the last 30 days (PNG image). Displayed if data is available.
*   **Recent Transactions (Up to 20)**: A table listing:
    *   **Hash**: Transaction hash, linked to its page on Basescan. Displayed as a shortened string.
    *   **Timestamp**: Date and time of the transaction.
    *   **From**: Sender address, linked to Basescan. Displayed as a shortened string.
    *   **To**: Receiver address or contract, linked to Basescan. Displayed as a shortened string.
    *   **Value (ETH)**: The amount of ETH transferred in the transaction.
    *   **Gas Fee**: The gas fee paid for the transaction, shown in ETH and its approximate USD equivalent (if ETH price is available).
*   **Error/Warning Messages**: Any errors or warnings encountered during data fetching or processing are displayed.
*   A link to return to the home page to track another wallet.

Example output for gas fee aggregation (as seen on the results page):
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
Current ETH price: $2000.00 USD 
Total Gas Spent (Last 7 Days): 0.0123 ETH ($24.60 USD)
Total Gas Spent (Last 30 Days): 0.0456 ETH ($91.20 USD)
Total Gas Spent (All Fetched Transactions): 0.1234 ETH ($246.80 USD)

(Note: The "Wei" part is available in the backend data but not explicitly shown in this summary on the web page to keep it cleaner; the ETH and USD values are the primary display for summaries).

==================================================
Generating Gas Spending Graph (Output shown in CLI if running tracker.py directly)
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

## 9. Deployment

This application is configured for basic deployment on platforms like Render, Heroku, or similar services that support Python WSGI applications.

### Key Deployment Files:

*   **`requirements.txt`**: Lists all Python dependencies. The deployment platform will typically use this file to install the necessary packages (e.g., `pip install -r requirements.txt`). This now includes `gunicorn` which will act as the production WSGI server.
*   **`Procfile`**: Specifies the command that the deployment platform should use to start the web server. For this application, it contains:
    ```
    web: gunicorn app:app
    ```
    This command tells the platform to start a web process by running `gunicorn`, serving the `app` instance found within the `app.py` file.

### Environment Variables on Deployment Platform:

To run successfully in a deployed environment, you **must** configure the following environment variables on your chosen platform (e.g., in Render's "Environment" settings):

*   **`BASESCAN_API_KEY`**: Your API key for Basescan (for fetching Base transactions and ETH price).
*   **`BASE_RPC_URL`**: The RPC URL for the Base blockchain (e.g., `https://mainnet.base.org` or your private RPC).
*   **`ETHERSCAN_API_KEY`**: Your API key for Etherscan (required if you use any features that interact with the Ethereum mainnet, like fetching L1 gas fees).
*   **`PYTHON_ENV` (Optional/Platform Specific)**: Some platforms might use `PYTHON_ENV=production` or similar to enable production optimizations in frameworks. Flask itself often uses `FLASK_ENV` (though `gunicorn` is often run without Flask's debug mode in prod regardless of this). For Render, typically you don't set `FLASK_ENV=production` directly if Gunicorn is handling production mode. The `debug=True` in `app.run()` is only for local development.

The platform automatically installs dependencies from `requirements.txt` and uses the `Procfile` to start the application. Ensure these files are committed to your repository.

## 10. Running the Web Frontend (Development)

The application includes a Flask-based web frontend. For local development:

**Prerequisites:**
*   Ensure all dependencies are installed: `pip install -r requirements.txt`
*   Make sure your `.env` file is configured with the necessary API keys (especially `BASESCAN_API_KEY` if you plan to integrate features that use it on the frontend).

**To run the Flask development server:**

1.  Navigate to the project root directory in your terminal.
2.  Execute the following command:
    ```bash
    python app.py
    ```
3.  The server will typically start on `http://127.0.0.1:5000/`. Open this URL in your web browser.
4.  You should see the main page of the gas tracker, rendered from `templates/index.html`.

The development server will run in debug mode, meaning it will automatically reload if you make changes to `app.py` or other Python files it uses. For production, a proper WSGI server (like Gunicorn) should be used.

### HTML Templates

The frontend uses Flask's templating engine (Jinja2) to render dynamic HTML pages:

*   **`templates/index.html`**: This is the main landing page. It contains a form where users can input a Base blockchain wallet address to track.
*   **`templates/results.html`**: This page displays the gas fee report for the queried wallet address. It includes sections for the current L2 gas price, a summary of gas fees spent over different periods (with ETH and USD values), a graph visualizing daily gas spending, and a list of recent transactions. Placeholders (e.g., `{{ wallet_address }}`) are used for dynamic data that will be passed from the Flask application.

Details of the first few processed transactions (CLI example):

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
