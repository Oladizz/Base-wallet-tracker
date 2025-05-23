import unittest
from unittest.mock import patch, MagicMock, ANY # ANY for some arguments
from datetime import date, datetime

# Add project root to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from graph_generator import generate_gas_spending_graph
# utils.py is used by graph_generator, ensure it's available
# but we don't need to directly test utils functions here.

class TestGraphGenerator(unittest.TestCase):

    @patch('graph_generator.plt') # Patching plt where it's used in graph_generator.py
    def test_generate_gas_spending_graph_success(self, mock_plt):
        # Mock the figure and axes objects that would be created by plt.subplots()
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        sample_data = {
            date(2023, 10, 1): 1000000000 * 50,  # 50 Gwei in Wei
            date(2023, 10, 2): 1000000000 * 75,
        }
        output_filename = "test_graph.png"

        result = generate_gas_spending_graph(sample_data, output_filename)

        self.assertTrue(result)
        mock_plt.subplots.assert_called_once_with(figsize=(12, 7))
        
        # Check calls on the Axes object
        mock_ax.plot.assert_called_once() # Check if plot was called
        mock_ax.set_xlabel.assert_called_with("Date")
        mock_ax.set_ylabel.assert_called_with("Gas Spent (Gwei)")
        mock_ax.set_title.assert_called_once() # Title can be complex, check it was called
        
        # Check date formatting calls (these are on the axis, not the ax object directly in current code)
        mock_ax.xaxis.set_major_formatter.assert_called_once()
        mock_ax.xaxis.set_major_locator.assert_called_once()
        mock_plt.xticks.assert_called_once_with(rotation=45, ha="right")

        mock_ax.yaxis.set_major_formatter.assert_called_once() # Check y-axis formatter
        
        mock_plt.grid.assert_called_with(True, which='major', linestyle='--', alpha=0.7)
        mock_plt.tight_layout.assert_called_once()
        mock_plt.savefig.assert_called_with(output_filename)
        mock_plt.close.assert_called_with(mock_fig)


    @patch('graph_generator.plt')
    def test_generate_gas_spending_graph_empty_data(self, mock_plt):
        with patch('builtins.print') as mock_print: # Suppress "No data provided" print
            result = generate_gas_spending_graph({}, "empty_graph.png")
            self.assertFalse(result)
            mock_print.assert_called_with("No data provided to generate the graph. Skipping graph generation.")
        
        mock_plt.subplots.assert_not_called()
        mock_plt.savefig.assert_not_called()

    @patch('graph_generator.plt')
    def test_generate_gas_spending_graph_all_zero_fees(self, mock_plt):
        # Mock the figure and axes objects
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        sample_data_zeros = {
            date(2023, 11, 1): 0,
            date(2023, 11, 2): 0
        }
        output_filename = "zero_fees_graph.png"
        
        with patch('builtins.print') as mock_print: # Suppress "All gas fee values are zero" print
            result = generate_gas_spending_graph(sample_data_zeros, output_filename)
            self.assertTrue(result) # Should still generate a graph of zeros
            mock_print.assert_any_call("All gas fee values are zero. Graph may be uninformative or skipped.")

        mock_plt.subplots.assert_called_once()
        mock_ax.plot.assert_called_once() # Plot should be called even with zeros
        mock_plt.savefig.assert_called_with(output_filename)
        mock_plt.close.assert_called_with(mock_fig)

    @patch('graph_generator.plt')
    def test_generate_gas_spending_graph_exception_during_plotting(self, mock_plt):
        mock_plt.subplots.side_effect = Exception("Matplotlib internal error")

        sample_data = {date(2023, 10, 1): 1000000000 * 50}
        output_filename = "error_graph.png"

        with patch('builtins.print') as mock_print:
            result = generate_gas_spending_graph(sample_data, output_filename)
            self.assertFalse(result)
            mock_print.assert_any_call(f"An error occurred during graph generation: Matplotlib internal error")
        
        mock_plt.savefig.assert_not_called() # Savefig should not be called if an error occurs before it

if __name__ == '__main__':
    unittest.main()
