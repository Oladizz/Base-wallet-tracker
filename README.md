# Base Blockchain Gas Fee Tracker with Firebase Backend

This application tracks gas fees for a given wallet address on the Base blockchain. The backend logic is implemented as a Firebase Cloud Function, and the frontend is served via a Flask application that interacts with this function.

## Features

- Fetches and displays current Base L2 gas prices and ETH price.
- Summarizes gas fees spent by a wallet (All Time, Last 30 Days, Last 7 Days).
- Displays recent transactions.
- Generates a graph of gas spending over the last 30 days.
- **Backend deployed as a Firebase Cloud Function.**
- **Does not store any user data.** All blockchain data is fetched on-the-fly.

## Project Structure

- `app.py`: Main Flask application that serves the frontend and calls the Firebase Cloud Function.
- `firebase_functions/`: Contains the Python code for the Firebase Cloud Function.
  - `main.py`: The entry point for the Cloud Function (includes a local Flask server for testing this logic).
  - `tracker_logic.py`: Core logic for fetching and processing blockchain data.
  - `models.py`: Pydantic models for data structures.
  - `utils.py`: Utility functions.
  - `*_api.py`: Modules for interacting with Etherscan/Basescan APIs.
  - `graph_generator.py`: Logic for creating the gas spending graph.
  - `requirements.txt`: Python dependencies for the Cloud Function.
  - `.env.example`: Example environment variables for local testing of the function.
- `templates/`: HTML templates for the frontend.
  - `index.html`: Main page for wallet address input.
  - `results.html`: Page to display the gas report.
- `static/`: Static assets (CSS).
- `requirements.txt`: Python dependencies for the main Flask frontend app (`app.py`).

## Setup and Deployment

### 1. Firebase Project Setup

- Create a new Firebase project in the [Firebase Console](https://console.firebase.google.com/).
- Add Python to your Cloud Functions environment.

### 2. Configure Environment Variables for Cloud Function

The Cloud Function requires the following environment variables to be set. You can set these in the Firebase Console or using the Firebase CLI:
`firebase functions:config:set key1="value1" key2="value2"`

- `BASESCAN_API_KEY`: Your API key for Basescan (Base blockchain explorer).
- `ETHERSCAN_API_KEY`: Your API key for Etherscan (used for Ethereum mainnet data).
- `BASE_RPC_URL`: Your RPC URL for the Base blockchain.

Refer to `firebase_functions/.env.example` for these keys.

### 3. Deploy the Cloud Function

- Ensure you have the Firebase CLI installed and are logged in (`firebase login`).
- Navigate to the project root directory.
- Deploy the function:
  ```bash
  # Make sure your firebase.json is configured to look for functions in firebase_functions
  # or deploy specifically from that directory if needed.
  # Example: firebase deploy --only functions
  # If firebase.json `functions.source` is "firebase_functions", then from root:
  firebase deploy --only functions 
  ```
- After deployment, Firebase CLI will provide an HTTP trigger URL for your function (e.g., `https://<region>-<project-id>.cloudfunctions.net/wallet_gas_report_cf` - the actual name might vary based on `main.py`'s function name).

### 4. Configure and Run the Frontend (Flask App)

- **Update Cloud Function URL in `app.py`**:
  Open `app.py` and replace the placeholder `YOUR_CLOUD_FUNCTION_URL_HERE/wallet_gas_report` with the actual HTTP trigger URL of your deployed Cloud Function.
- **Install Dependencies**:
  ```bash
  pip install -r requirements.txt 
  ```
- **Run the Flask App**:
  ```bash
  python app.py
  ```
- Open your browser and go to `http://127.0.0.1:5000/`.

## Local Development and Testing

### Testing the Cloud Function Logic Locally

The `firebase_functions/main.py` file contains a simple Flask server to test the `get_wallet_gas_report` logic without deploying to Firebase.

1.  **Create `.env` file**:
    Copy `firebase_functions/.env.example` to `firebase_functions/.env` and fill in your actual API keys and RPC URL.
2.  **Install Function Dependencies**:
    ```bash
    pip install -r firebase_functions/requirements.txt
    ```
3.  **Run the local test server**:
    ```bash
    python firebase_functions/main.py
    ```
    This will start a server (usually on port 5000, but distinct from the main `app.py`'s server).
4.  **Test the endpoint**:
    Send a GET request to `http://127.0.0.1:5000/wallet_gas_report?wallet_address=YOUR_WALLET_ADDRESS` or a POST request with a JSON body.

### Testing with Firebase Emulators

For a more accurate local testing environment that mimics Firebase:
1. Install the Firebase CLI and set up the [Firebase Local Emulator Suite](https://firebase.google.com/docs/emulator-suite).
2. Run `firebase emulators:start`.
3. Test the local HTTP endpoint provided by the Functions emulator.

## Future Considerations

- **Frontend Deployment**: For a fully serverless deployment, the static frontend assets (HTML, CSS, JS) could be deployed using [Firebase Hosting](https://firebase.google.com/docs/hosting). `index.html` would then need client-side JavaScript to call the Cloud Function.
- **Cleanup**: The original top-level Python files (`tracker.py`, `models.py`, etc.) can be removed if `app.py` is simplified or the frontend is moved to Firebase Hosting.
```
