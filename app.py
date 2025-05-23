from flask import Flask, render_template, request, redirect, url_for
import os

# Attempt to import the main report generation function from tracker.py
try:
    from tracker import get_wallet_gas_report
except ImportError:
    # This might happen if tracker.py is not yet created or has issues
    # For now, define a placeholder if tracker is not available
    print("Warning: Could not import get_wallet_gas_report from tracker.py. Using placeholder.")
    def get_wallet_gas_report(wallet_address: str):
        # Placeholder data structure matching what results.html might expect
        return {
            "wallet_address": wallet_address,
            "current_l2_gas_price_gwei": "N/A (tracker not loaded)",
            "current_eth_usd_price": "N/A (tracker not loaded)",
            "gas_summary": {
                "all_time": {"eth": "0 ETH", "usd": "$0 USD", "wei": 0},
                "last_30_days": {"eth": "0 ETH", "usd": "$0 USD", "wei": 0},
                "last_7_days": {"eth": "0 ETH", "usd": "$0 USD", "wei": 0},
            },
            "transactions": [],
            "graph_url": None,
            "error_messages": ["Tracker module could not be loaded. Displaying placeholder data."]
        }

# Create a Flask application instance
# Flask will automatically look for 'static' and 'templates' folders
# in the same directory as this app.py file.
app = Flask(__name__)

# Ensure the static/images directory exists for graph outputs
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
    
    # Call the main logic function from tracker.py
    # This function is expected to return a dictionary with all necessary data
    report_data = get_wallet_gas_report(wallet_address_input)
    
    # The report_data dictionary itself is passed as keyword arguments to render_template.
    # Utility functions like wei_to_ether_str are now applied in tracker.py before this point,
    # so they don't need to be passed to the template context directly for the main data.
    return render_template('results.html', **report_data)


if __name__ == '__main__':
    app.run(debug=True)
