from flask import Flask, render_template, request, redirect, url_for
import os
# import requests # Removed
# import json # Removed
from dotenv import load_dotenv # Added
from firebase_functions.tracker_logic import get_wallet_gas_report # Added

# Load environment variables from .env file at the project root
# This is for running app.py locally.
# The firebase_functions/tracker_logic.py itself also calls load_dotenv(),
# which is fine; subsequent calls don't overwrite existing env vars by default.
# If firebase_functions/.env exists, it might be loaded by tracker_logic.
# If a root .env exists, it's loaded here for app.py context.
load_dotenv()


# Create a Flask application instance
# Flask will automatically look for 'static' and 'templates' folders
# in the same directory as this app.py file.
app = Flask(__name__)

# Ensure the static/images directory exists for graph outputs (if still needed by any part)
# Graph is now base64, so direct file saving to static/images from tracker_logic might be removed.
# However, keeping this doesn't hurt if other static assets are planned.
static_images_dir = os.path.join(app.static_folder, 'images')
os.makedirs(static_images_dir, exist_ok=True)


@app.route('/')
def home_route(): # Renamed for clarity with url_for
    """
    Root route for the Flask application.
    Serves the index.html page.
    """
    return render_template('index.html')

@app.route('/track', methods=['POST'])
def track_wallet_route():
    """
    Handles the wallet address submission, calls the tracker logic,
    and renders the results page.
    """
    wallet_address_input = request.form.get('wallet_address', '').strip()

    if not wallet_address_input:
        # Optionally, add a flash message here to inform the user why they were redirected
        # from flask import flash
        # flash('Wallet address is required!', 'error')
        return redirect(url_for('home_route'))

    # Basic validation for wallet address format (very simple check)
    # A more robust validation (e.g., regex, checksum) would be better for a real app.
    if not (wallet_address_input.startswith('0x') and len(wallet_address_input) == 42):
        # flash('Invalid wallet address format.', 'error')
        # For now, we can render index with an error or just redirect
        # Or, pass an error message to index.html if you modify it to display errors
        return render_template('index.html', error="Invalid wallet address format. Please try again.")


    print(f"Received wallet address: {wallet_address_input}") # For debugging
    
    try:
        # Call the local backend logic directly
        # The get_wallet_gas_report function in firebase_functions.tracker_logic
        # already handles loading .env from within its own directory if needed
        # via its own load_dotenv() call.
        # The load_dotenv() at the top of app.py is for app.py's own potential env var needs
        # or to ensure a root .env is loaded if tracker_logic doesn't find firebase_functions/.env
        report_data = get_wallet_gas_report(wallet_address_input)
    except Exception as e:
        print(f"Error calling get_wallet_gas_report directly: {e}")
        # Create a basic error structure similar to what was expected before
        report_data = {
            "wallet_address": wallet_address_input,
            "current_l2_gas_price_gwei": "N/A",
            "current_eth_usd_price": "N/A",
            "gas_summary": {
                "all_time": {"eth": "0 ETH", "usd": "$0 USD", "wei": 0},
                "last_30_days": {"eth": "0 ETH", "usd": "$0 USD", "wei": 0},
                "last_7_days": {"eth": "0 ETH", "usd": "$0 USD", "wei": 0},
            },
            "transactions": [],
            "graph_data_base64": None, # Ensure this matches what results.html expects
            "error_messages": [f"Error processing your request: {str(e)}"]
        }
    
    # The report_data dictionary itself is passed as keyword arguments to render_template.
    # Utility functions like wei_to_ether_str are now applied in tracker_logic.py before this point,
    # so they don't need to be passed to the template context directly for the main data.
    return render_template('results.html', **report_data)


if __name__ == '__main__':
    app.run(debug=True)
