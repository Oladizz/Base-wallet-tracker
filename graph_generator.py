import matplotlib
matplotlib.use('Agg') # Use non-interactive backend, important for scripts/servers

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import date
from typing import Dict, List # Added List
from decimal import Decimal # For y-axis values

from utils import wei_to_gwei_decimal # For converting Y-axis values

def generate_gas_spending_graph(daily_gas_data: Dict[date, int], output_filename: str = "gas_spending_graph.png") -> bool:
    """
    Generates a line chart of daily gas spending.

    Args:
        daily_gas_data: A dictionary where keys are date objects and values are total gas fees in Wei for that day.
                        Assumes data is sorted by date if that's desired for the line plot's logical flow.
        output_filename: The filename to save the graph to.

    Returns:
        True if the graph was generated and saved successfully, False otherwise.
    """
    if not daily_gas_data:
        print("No data provided to generate the graph. Skipping graph generation.")
        return False

    dates: List[date] = list(daily_gas_data.keys())
    gas_fees_wei: List[int] = list(daily_gas_data.values())

    # Convert gas fees from Wei (int) to Gwei (Decimal) for plotting
    gas_fees_gwei: List[Decimal] = [wei_to_gwei_decimal(str(fee)) for fee in gas_fees_wei]

    if not any(fee > Decimal(0) for fee in gas_fees_gwei): # Check if all values are zero after conversion
        print("All gas fee values are zero. Graph may be uninformative or skipped.")
        # Decide if you want to generate a graph of all zeros or skip.
        # For now, let's generate it, it might indicate a period of no spending.
        # If you want to skip, return False here.

    try:
        fig, ax = plt.subplots(figsize=(12, 7)) # Adjusted figure size for better readability

        ax.plot(dates, gas_fees_gwei, marker='o', linestyle='-', color='royalblue')

        # Formatting the x-axis to show dates nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10)) # Auto-adjust number of ticks
        plt.xticks(rotation=45, ha="right") # Rotate date labels

        # Formatting the y-axis to show Gwei
        # Using FuncFormatter to format y-axis ticks as numbers (e.g., "100 Gwei")
        def gwei_formatter(x, pos):
            return f'{x:,.0f}' # No decimal places for Gwei on axis, as it's usually large enough
        
        ax.yaxis.set_major_formatter(FuncFormatter(gwei_formatter))

        # Labels and Title
        ax.set_xlabel("Date")
        ax.set_ylabel("Gas Spent (Gwei)")
        
        # Dynamically set title based on date range if possible
        title_date_range = "Daily Gas Spending"
        if dates:
            start_date_str = dates[0].strftime('%Y-%m-%d')
            end_date_str = dates[-1].strftime('%Y-%m-%d')
            title_date_range = f"Daily Gas Spending ({start_date_str} to {end_date_str})"
        ax.set_title(title_date_range)

        plt.grid(True, which='major', linestyle='--', alpha=0.7)
        plt.tight_layout()  # Adjust layout to prevent labels from overlapping

        plt.savefig(output_filename)
        print(f"Graph saved to {output_filename}")
        return True

    except Exception as e:
        print(f"An error occurred during graph generation: {e}")
        return False
    finally:
        # Ensure fig exists before trying to close it, in case subplots() failed
        if 'fig' in locals() and fig is not None:
            plt.close(fig)

if __name__ == '__main__':
    # Example usage of generate_gas_spending_graph
    print("Testing graph_generator.py...")

    # Test Case 1: Some data
    sample_data_1 = {
        date(2023, 10, 1): 1000000000 * 50,  # 50 Gwei
        date(2023, 10, 2): 1000000000 * 75,  # 75 Gwei
        date(2023, 10, 3): 1000000000 * 60,  # 60 Gwei
        date(2023, 10, 4): 1000000000 * 120, # 120 Gwei
        date(2023, 10, 5): 1000000000 * 90   # 90 Gwei
    }
    # Sort sample data by date for logical plotting
    sorted_sample_data_1 = dict(sorted(sample_data_1.items()))
    
    filename_1 = "test_gas_graph_1.png"
    print(f"\nGenerating graph for sample data 1 ({filename_1})...")
    if generate_gas_spending_graph(sorted_sample_data_1, filename_1):
        print(f"Successfully generated {filename_1}. Please check the project directory.")
    else:
        print(f"Failed to generate {filename_1}.")

    # Test Case 2: Empty data
    sample_data_2 = {}
    filename_2 = "test_gas_graph_2_empty.png"
    print(f"\nGenerating graph for empty data ({filename_2})...")
    if generate_gas_spending_graph(sample_data_2, filename_2):
        print(f"Successfully generated {filename_2} (should not happen for empty data).")
    else:
        print(f"Failed to generate {filename_2} (expected behavior for empty data).")

    # Test Case 3: Data with all zero fees
    sample_data_3 = {
        date(2023, 11, 1): 0,
        date(2023, 11, 2): 0,
        date(2023, 11, 3): 0
    }
    filename_3 = "test_gas_graph_3_zeros.png"
    print(f"\nGenerating graph for zero-fee data ({filename_3})...")
    if generate_gas_spending_graph(sample_data_3, filename_3):
        print(f"Successfully generated {filename_3}. Please check the project directory (graph of zeros).")
    else:
        print(f"Failed to generate {filename_3}.")
    
    # Test Case 4: Single data point
    sample_data_4 = {
        date(2023, 12, 1): 1000000000 * 100 # 100 Gwei
    }
    filename_4 = "test_gas_graph_4_single.png"
    print(f"\nGenerating graph for single data point ({filename_4})...")
    if generate_gas_spending_graph(sample_data_4, filename_4):
        print(f"Successfully generated {filename_4}. Please check the project directory.")
    else:
        print(f"Failed to generate {filename_4}.")

    print("\nGraph generator tests complete.")
