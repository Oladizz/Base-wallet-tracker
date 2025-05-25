import matplotlib
matplotlib.use('Agg') # Use non-interactive backend, important for scripts/servers

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import date
from typing import Dict, List, Optional # Added Optional
from decimal import Decimal # For y-axis values

import io # For in-memory buffer
import base64 # For base64 encoding

from .utils import wei_to_gwei_decimal # For converting Y-axis values

def generate_gas_spending_graph_base64(daily_gas_data: Dict[date, int]) -> Optional[str]:
    """
    Generates a line chart of daily gas spending and returns it as a base64 encoded string.

    Args:
        daily_gas_data: A dictionary where keys are date objects and values are total gas fees in Wei for that day.

    Returns:
        A base64 encoded PNG image string if successful, None otherwise.
    """
    if not daily_gas_data:
        print("No data provided for graph generation.")
        return None

    dates: List[date] = list(daily_gas_data.keys())
    gas_fees_wei: List[int] = list(daily_gas_data.values())
    gas_fees_gwei: List[Decimal] = [wei_to_gwei_decimal(str(fee)) for fee in gas_fees_wei]

    if not any(fee > Decimal(0) for fee in gas_fees_gwei):
        print("All gas fee values are zero. Graph might be uninformative but will be generated.")

    fig = None # Initialize fig to None
    try:
        fig, ax = plt.subplots(figsize=(10, 6)) # Slightly adjusted for typical inline display

        ax.plot(dates, gas_fees_gwei, marker='o', linestyle='-', color='royalblue')

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
        plt.xticks(rotation=30, ha="right")

        def gwei_formatter(x, pos):
            return f'{x:,.0f}'
        ax.yaxis.set_major_formatter(FuncFormatter(gwei_formatter))

        ax.set_xlabel("Date")
        ax.set_ylabel("Gas Spent (Gwei)")
        title_date_range = "Daily Gas Spending"
        if dates:
            start_date_str = dates[0].strftime('%b %d, %Y')
            end_date_str = dates[-1].strftime('%b %d, %Y')
            if start_date_str == end_date_str:
                 title_date_range = f"Gas Spending for {start_date_str}"
            else:
                title_date_range = f"Gas Spending: {start_date_str} to {end_date_str}"
        ax.set_title(title_date_range)

        plt.grid(True, which='major', linestyle='--', alpha=0.6)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0) # Rewind buffer to the beginning
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        buffer.close() # Close the buffer
        
        return f"data:image/png;base64,{image_base64}" # Return data URI

    except Exception as e:
        print(f"An error occurred during base64 graph generation: {e}")
        return None
    finally:
        if fig: # Check if fig was created
            plt.close(fig)


def generate_gas_spending_graph(daily_gas_data: Dict[date, int], output_filename: str = "gas_spending_graph.png") -> bool:
    """
    Generates a line chart of daily gas spending and saves to a file.
    (Kept for potential other uses or local testing)
    """
    if not daily_gas_data:
        print("No data provided to generate the graph. Skipping graph generation.")
        return False

    dates: List[date] = list(daily_gas_data.keys())
    gas_fees_wei: List[int] = list(daily_gas_data.values())
    gas_fees_gwei: List[Decimal] = [wei_to_gwei_decimal(str(fee)) for fee in gas_fees_wei]

    if not any(fee > Decimal(0) for fee in gas_fees_gwei):
        print("All gas fee values are zero. Graph may be uninformative or skipped.")

    fig = None # Initialize fig to None
    try:
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(dates, gas_fees_gwei, marker='o', linestyle='-', color='royalblue')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
        plt.xticks(rotation=45, ha="right")

        def gwei_formatter(x, pos):
            return f'{x:,.0f}'
        ax.yaxis.set_major_formatter(FuncFormatter(gwei_formatter))

        ax.set_xlabel("Date")
        ax.set_ylabel("Gas Spent (Gwei)")
        title_date_range = "Daily Gas Spending"
        if dates:
            start_date_str = dates[0].strftime('%Y-%m-%d')
            end_date_str = dates[-1].strftime('%Y-%m-%d')
            title_date_range = f"Daily Gas Spending ({start_date_str} to {end_date_str})"
        ax.set_title(title_date_range)

        plt.grid(True, which='major', linestyle='--', alpha=0.7)
        plt.tight_layout()

        plt.savefig(output_filename)
        print(f"Graph saved to {output_filename}")
        return True

    except Exception as e:
        print(f"An error occurred during file graph generation: {e}")
        return False
    finally:
        if fig: # Check if fig was created
            plt.close(fig)

if __name__ == '__main__':
    print("Testing graph_generator.py...")
    sample_data = {
        date(2023, 10, 1): 1000000000 * 50, date(2023, 10, 2): 1000000000 * 75,
        date(2023, 10, 3): 1000000000 * 60, date(2023, 10, 4): 1000000000 * 120,
        date(2023, 10, 5): 1000000000 * 90
    }
    sorted_sample_data = dict(sorted(sample_data.items()))

    # Test saving to file
    filename = "test_gas_graph_file.png"
    print(f"\nGenerating graph to file ({filename})...")
    if generate_gas_spending_graph(sorted_sample_data, filename):
        print(f"Successfully generated {filename}.")
    else:
        print(f"Failed to generate {filename}.")

    # Test generating base64
    print("\nGenerating base64 encoded graph...")
    base64_image = generate_gas_spending_graph_base64(sorted_sample_data)
    if base64_image:
        print(f"Successfully generated base64 image string (first 100 chars): {base64_image[:100]}...")
        # To test, you can copy the full base64 string and paste it into a browser's address bar
        # or use an online base64 viewer.
        # with open("test_base64_output.txt", "w") as f:
        # f.write(base64_image)
        # print("Full base64 string saved to test_base64_output.txt for verification.")
    else:
        print("Failed to generate base64 image string.")

    # Test with empty data for base64
    print("\nGenerating base64 encoded graph with empty data...")
    base64_image_empty = generate_gas_spending_graph_base64({})
    if base64_image_empty:
        print(f"Generated base64 image string from empty data (should not happen).")
    else:
        print("Failed to generate base64 image string from empty data (expected).")
    
    print("\nGraph generator tests complete.")
