import matplotlib
matplotlib.use('Agg') # Use non-interactive backend, important for scripts/servers

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import date
from typing import Dict, List, Optional
from decimal import Decimal

import io # For in-memory buffer
import base64 # For base64 encoding

from .utils import wei_to_gwei_decimal # For converting Y-axis values

def generate_gas_spending_graph_base64(daily_gas_data: Dict[date, int]) -> Optional[str]:
    """
    Generates a line chart of daily gas spending and returns it as a base64 encoded string.
    Enhanced for better visibility.
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
        # 1. Increase Figure Size
        fig = plt.figure(figsize=(12, 7)) 

        ax = plt.gca() # Get current axes

        ax.plot(dates, gas_fees_gwei, marker='o', linestyle='-', color='deepskyblue', linewidth=2, markersize=5)

        # 2. Adjust Font Sizes & Title
        title_str = "Daily Gas Spending (Last 30 Days)"
        if dates:
            start_date_str = dates[0].strftime('%b %d, %Y')
            end_date_str = dates[-1].strftime('%b %d, %Y')
            if start_date_str == end_date_str:
                 title_str = f"Gas Spending for {start_date_str}"
            else:
                title_str = f"Gas Spending: {start_date_str} to {end_date_str}"
        plt.title(title_str, fontsize=18) # Title font (using 18 from example as it's larger)
        
        plt.xlabel("Date", fontsize=14)
        plt.ylabel("Gas Spent (Gwei)", fontsize=14) # Kept Gwei as per existing logic

        # X-axis tick formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
        plt.xticks(rotation=45, ha="right", fontsize=10)
        
        # Y-axis tick formatting & Gwei Formatter
        def gwei_formatter(x, pos):
            return f'{x:,.0f}' # No decimal places for Gwei
        ax.yaxis.set_major_formatter(FuncFormatter(gwei_formatter))
        plt.yticks(fontsize=10)

        # 3. Add Grid
        plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
        
        # 4. Ensure Tight Layout
        plt.tight_layout()

        buffer = io.BytesIO()
        # Using bbox_inches='tight' as suggested in example for potentially better packing
        plt.savefig(buffer, format='png', bbox_inches='tight') 
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        buffer.close()
        
        return f"data:image/png;base64,{image_base64}"

    except Exception as e:
        print(f"An error occurred during base64 graph generation: {e}")
        return None
    finally:
        if fig:
            plt.close(fig)


def generate_gas_spending_graph(daily_gas_data: Dict[date, int], output_filename: str = "gas_spending_graph.png") -> bool:
    """
    Generates a line chart of daily gas spending and saves to a file.
    (Kept for potential other uses or local testing) - Also enhanced slightly
    """
    if not daily_gas_data:
        print("No data provided to generate the graph. Skipping graph generation.")
        return False

    dates: List[date] = list(daily_gas_data.keys())
    gas_fees_wei: List[int] = list(daily_gas_data.values())
    gas_fees_gwei: List[Decimal] = [wei_to_gwei_decimal(str(fee)) for fee in gas_fees_wei]

    if not any(fee > Decimal(0) for fee in gas_fees_gwei):
        print("All gas fee values are zero. Graph may be uninformative or skipped.")

    fig = None 
    try:
        fig = plt.figure(figsize=(12, 7))
        ax = plt.gca()

        ax.plot(dates, gas_fees_gwei, marker='o', linestyle='-', color='deepskyblue', linewidth=2, markersize=5)
        
        title_str = "Daily Gas Spending (Last 30 Days)"
        if dates:
            start_date_str = dates[0].strftime('%Y-%m-%d')
            end_date_str = dates[-1].strftime('%Y-%m-%d')
            if start_date_str == end_date_str:
                title_str = f"Gas Spending for {start_date_str}"
            else:
                title_str = f"Daily Gas Spending ({start_date_str} to {end_date_str})"
        plt.title(title_str, fontsize=18)
        
        plt.xlabel("Date", fontsize=14)
        plt.ylabel("Gas Spent (Gwei)", fontsize=14)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
        plt.xticks(rotation=45, ha="right", fontsize=10)

        def gwei_formatter(x, pos):
            return f'{x:,.0f}'
        ax.yaxis.set_major_formatter(FuncFormatter(gwei_formatter))
        plt.yticks(fontsize=10)

        plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
        plt.tight_layout()

        plt.savefig(output_filename, bbox_inches='tight')
        print(f"Graph saved to {output_filename}")
        return True

    except Exception as e:
        print(f"An error occurred during file graph generation: {e}")
        return False
    finally:
        if fig:
            plt.close(fig)

if __name__ == '__main__':
    print("Testing graph_generator.py with enhanced visibility...")
    sample_data = {
        date(2023, 10, 1): 1000000000 * 50000,  # 50k Gwei
        date(2023, 10, 2): 1000000000 * 75000,
        date(2023, 10, 3): 1000000000 * 6000, # 6k Gwei
        date(2023, 10, 4): 1000000000 * 120000,
        date(2023, 10, 5): 1000000000 * 900
    }
    # Add more data points for better visual
    for i in range(6, 31):
        sample_data[date(2023, 10, i)] = 1000000000 * (5000 + i*1000)


    sorted_sample_data = dict(sorted(sample_data.items()))

    # Test saving to file (enhanced)
    filename = "test_gas_graph_file_enhanced.png"
    print(f"\nGenerating enhanced graph to file ({filename})...")
    if generate_gas_spending_graph(sorted_sample_data, filename):
        print(f"Successfully generated {filename}.")
    else:
        print(f"Failed to generate {filename}.")

    # Test generating base64 (enhanced)
    print("\nGenerating enhanced base64 encoded graph...")
    base64_image = generate_gas_spending_graph_base64(sorted_sample_data)
    if base64_image:
        print(f"Successfully generated enhanced base64 image string (first 100 chars): {base64_image[:100]}...")
        # To test, you can copy the full base64 string and paste it into a browser's address bar
        # or use an online base64 viewer.
        with open("test_base64_output_enhanced.txt", "w") as f:
           f.write(base64_image)
        print("Full base64 string saved to test_base64_output_enhanced.txt for verification.")

    else:
        print("Failed to generate enhanced base64 image string.")
    
    print("\nGraph generator tests complete.")
