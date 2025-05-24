import os
import json
from flask import Flask, request # Using Flask for local testing, Firebase will use https_fn

# Attempt to use relative imports for packaged context (Firebase)
try:
    from .tracker_logic import get_wallet_gas_report
except ImportError:
    # Fallback for direct execution (e.g., python firebase_functions/main.py)
    from tracker_logic import get_wallet_gas_report

# Firebase specific lines (to be uncommented/used in Firebase environment)
# import firebase_functions
# from firebase_functions import https_fn

# @https_fn.on_request(cors=True) # Enable CORS directly if needed
# def wallet_gas_report_cf(req: https_fn.HttpsRequest) -> https_fn.Response:
#     wallet_address = None
#     if req.method == 'POST':
#         try:
#             data = req.get_json(silent=True)
#             if data and 'wallet_address' in data:
#                 wallet_address = data['wallet_address']
#         except Exception:
#             pass # Error in parsing JSON
#
#     if not wallet_address and req.args: # Check query parameters for GET
#         wallet_address = req.args.get('wallet_address')
#
#     if not wallet_address:
#         return https_fn.Response(
#             json.dumps({"error": "wallet_address is required"}),
#             status=400,
#             mimetype='application/json'
#         )
#
#     # Logic execution
#     report_data = get_wallet_gas_report(wallet_address)
#
#     return https_fn.Response(
#         json.dumps(report_data),
#         status=200,
#         mimetype='application/json'
#     )

# --- Flask app for local testing ---
app = Flask(__name__)

@app.route('/wallet_gas_report', methods=['POST', 'GET'])
def local_wallet_gas_report_endpoint():
    wallet_address = None
    if request.method == 'POST':
        data = request.get_json(silent=True)
        wallet_address = data.get('wallet_address') if data else None
    elif request.method == 'GET':
        wallet_address = request.args.get('wallet_address')

    if not wallet_address:
        return json.dumps({"error": "wallet_address is required"}), 400, {'Content-Type': 'application/json'}

    # Load .env file from firebase_functions directory for local testing
    from dotenv import load_dotenv
    # Construct the path to .env relative to this main.py file
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    print(f"Local test: Received wallet address: {wallet_address}")
    report_data = get_wallet_gas_report(wallet_address)
    return json.dumps(report_data), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    print("Starting local Flask server for testing Cloud Function logic...")
    print("Make sure firebase_functions/.env file exists with API keys.")
    print("Test URL: http://127.0.0.1:5000/wallet_gas_report?wallet_address=YOUR_WALLET_ADDRESS")
    app.run(debug=True, port=5000)
