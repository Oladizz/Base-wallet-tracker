from decimal import Decimal, InvalidOperation

from typing import Union, Optional # Added Optional and Union

WEI_IN_ETHER = Decimal("1_000_000_000_000_000_000") # 10^18
WEI_IN_GWEI = Decimal("1_000_000_000")             # 10^9
TWO_PLACES = Decimal("0.01") # For currency rounding

def wei_to_ether_str(wei_value: Union[str, int, Decimal]) -> str:
    """
    Converts a Wei value (string, int, or Decimal) to an Ether string value, formatted nicely.
    e.g., "0.00123 ETH" or "123.00 ETH".

    Args:
        wei_value: The value in Wei as a string, int, or Decimal.

    Returns:
        A string representing the value in Ether, or "Error" if conversion fails.
    """
    if wei_value is None or (isinstance(wei_value, str) and not wei_value.strip()):
        return "0.00 ETH"
    
    try:
        if isinstance(wei_value, (int, str)):
            wei_decimal = Decimal(str(wei_value))
        elif isinstance(wei_value, Decimal):
            wei_decimal = wei_value
        else:
            raise InvalidOperation("Input must be str, int, or Decimal")

        ether_value = wei_decimal / WEI_IN_ETHER
        
        if ether_value == Decimal(0):
            return "0.00 ETH"
        
        if ether_value >= Decimal("1"): # For 1 ETH or more
            return f"{ether_value:,.2f} ETH"
        
        # For values between 0 and 1 (exclusive of 0)
        if ether_value < Decimal("0.000001"): # Very tiny non-zero values
            return f"{ether_value:.18f}".rstrip('0').rstrip('.') + " ETH"
        
        # For other values between 0 and 1 (e.g., 0.5, 0.123, 0.001)
        # Format to 2 decimal places first.
        # If it rounds to "0.00" at 2dp but wasn't actually zero, then use more precision.
        formatted_2dp = f"{ether_value:.2f}"
        if Decimal(formatted_2dp) == Decimal(0) and ether_value != Decimal(0):
            # e.g., 0.00123 ETH will be "0.00" with :.2f, so use more precision.
            # Use up to 8 decimal places, stripping unnecessary trailing zeros.
            return f"{ether_value:.8f}".rstrip('0').rstrip('.') + " ETH"
        else:
            # e.g., 0.5 ETH becomes "0.50", 0.12 ETH becomes "0.12".
            # Also, if ether_value was truly 0 (already handled), or if it became "0.00" and was small but not micro.
            return formatted_2dp + " ETH"
            
    except InvalidOperation:
        return "Error converting Wei to Ether"
    except Exception: 
        return "Error"

def wei_to_gwei_str(wei_value_str: str) -> str:
    """
    Converts a Wei string value to a Gwei string value, formatted nicely.
    e.g., "1234567 Gwei" or "1.23 Gwei" for fractional Gwei from very small Wei.

    Args:
        wei_value_str: The value in Wei as a string.

    Returns:
        A string representing the value in Gwei, or "Error" if conversion fails.
    """
    if not wei_value_str:
        return "0 Gwei"
    try:
        wei_value = Decimal(wei_value_str)
        gwei_value = wei_value / WEI_IN_GWEI
        
        if gwei_value == Decimal(0):
            return "0 Gwei"
        # If gwei_value is a whole number, display as integer. Otherwise, show 2 decimal places.
        if gwei_value % 1 == 0:
            return f"{gwei_value:,.0f} Gwei"
        else:
            return f"{gwei_value:,.2f} Gwei" # Show some precision if it's fractional
    except InvalidOperation:
        return "Error converting Wei to Gwei"
    except Exception:
        return "Error"

def wei_to_gwei_decimal(wei_value_str: str) -> Decimal:
    """
    Converts a Wei string value to a Gwei Decimal value.

    Args:
        wei_value_str: The value in Wei as a string.

    Returns:
        A Decimal representing the value in Gwei, or Decimal(0) if conversion fails.
    """
    if not wei_value_str:
        return Decimal(0)
    try:
        wei_value = Decimal(wei_value_str)
        gwei_value = wei_value / WEI_IN_GWEI
        return gwei_value
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(0)

def calculate_fiat_value(wei_amount_int: int, eth_to_usd_price: Decimal) -> Optional[Decimal]:
    """
    Calculates the USD value of a given Wei amount.

    Args:
        wei_amount_int: The amount in Wei as an integer.
        eth_to_usd_price: The current price of 1 ETH in USD as a Decimal.

    Returns:
        The USD value as a Decimal rounded to 2 decimal places, or None if inputs are invalid.
    """
    if not isinstance(wei_amount_int, int) or eth_to_usd_price is None or not isinstance(eth_to_usd_price, Decimal) or eth_to_usd_price <= Decimal(0):
        # print("Warning: Invalid input for calculate_fiat_value.")
        return None
    
    try:
        wei_decimal = Decimal(wei_amount_int)
        ether_value = wei_decimal / WEI_IN_ETHER
        usd_value = ether_value * eth_to_usd_price
        # Explicitly use ROUND_HALF_UP for common currency rounding (0.005 -> 0.01)
        return usd_value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError):
        # print(f"Error calculating fiat value for wei: {wei_amount_int}, price: {eth_to_usd_price}")
        return None

# Import the rounding constant
from decimal import ROUND_HALF_UP

if __name__ == '__main__':
    print("Testing wei_to_ether_str:")
    print(f"'1000000000000000000' Wei (str) -> {wei_to_ether_str('1000000000000000000')} (Expected: 1.00 ETH)")
    print(f"1000000000000000000 Wei (int) -> {wei_to_ether_str(1000000000000000000)} (Expected: 1.00 ETH)")
    print(f"Decimal('1e18') Wei (Decimal) -> {wei_to_ether_str(Decimal('1e18'))} (Expected: 1.00 ETH)")
    print(f"'1000000000000000000' Wei -> {wei_to_ether_str('1000000000000000000')} (Expected: 1.00 ETH)")
    print(f"'500000000000000000' Wei -> {wei_to_ether_str('500000000000000000')} (Expected: 0.50 ETH)")
    print(f"'1234567890000000' Wei -> {wei_to_ether_str('1234567890000000')} (Expected: 0.0012345679 ETH)")
    print(f"'1000000000' Wei -> {wei_to_ether_str('1000000000')} (Expected: 0.000000001 ETH)")
    print(f"'1' Wei -> {wei_to_ether_str('1')} (Expected: 0.000000000000000001 ETH)")
    print(f"'0' Wei -> {wei_to_ether_str('0')} (Expected: 0.00 ETH)")
    print(f"'' Wei -> {wei_to_ether_str('')} (Expected: 0.00 ETH)")
    print(f"'invalid' Wei -> {wei_to_ether_str('invalid')} (Expected: Error converting Wei to Ether)")
    print(f"'1234567891234567891234' Wei (str) -> {wei_to_ether_str('1234567891234567891234')} (Expected: 1,234.57 ETH)")

    print("\nTesting wei_to_gwei_str:")
    print(f"'1000000000' Wei (str) -> {wei_to_gwei_str('1000000000')} (Expected: 1 Gwei)")
    print(f"'1234567890' Wei -> {wei_to_gwei_str('1234567890')} (Expected: 1.23 Gwei)")
    print(f"'100000000' Wei -> {wei_to_gwei_str('100000000')} (Expected: 0.10 Gwei)")
    print(f"'5000000000' Wei -> {wei_to_gwei_str('5000000000')} (Expected: 5 Gwei)")
    print(f"'0' Wei -> {wei_to_gwei_str('0')} (Expected: 0 Gwei)")
    print(f"'' Wei -> {wei_to_gwei_str('')} (Expected: 0 Gwei)")
    print(f"'invalid' Wei (str) -> {wei_to_gwei_str('invalid')} (Expected: Error converting Wei to Gwei)")
    print(f"'12345678912345' Wei (str) -> {wei_to_gwei_str('12345678912345')} (Expected: 12,345.68 Gwei)")

    print("\nTesting wei_to_gwei_decimal:")
    print(f"'1000000000' Wei -> {wei_to_gwei_decimal('1000000000')} Gwei (Decimal) (Expected: 1)")
    print(f"'1234567890' Wei -> {wei_to_gwei_decimal('1234567890')} Gwei (Decimal) (Expected: 1.23456789)")
    print(f"'invalid' Wei -> {wei_to_gwei_decimal('invalid')} Gwei (Decimal) (Expected: 0)")

    print("\nTesting calculate_fiat_value:")
    eth_price_test = Decimal("2000.00") # $2000 per ETH
    print(f"ETH Price for test: ${eth_price_test}")
    # 1 ETH in Wei
    wei_1_eth = 1000000000000000000 
    print(f"1 ETH ({wei_1_eth} Wei) -> USD: ${calculate_fiat_value(wei_1_eth, eth_price_test)} (Expected: 2000.00)")
    # 0.05 ETH in Wei
    wei_0_05_eth = 50000000000000000 
    print(f"0.05 ETH ({wei_0_05_eth} Wei) -> USD: ${calculate_fiat_value(wei_0_05_eth, eth_price_test)} (Expected: 100.00)")
    # 0 Wei
    print(f"0 Wei -> USD: ${calculate_fiat_value(0, eth_price_test)} (Expected: 0.00)")
    # Invalid ETH price (None)
    print(f"1 ETH, ETH Price None -> USD: {calculate_fiat_value(wei_1_eth, None)} (Expected: None)")
    # Invalid ETH price (zero)
    print(f"1 ETH, ETH Price 0 -> USD: {calculate_fiat_value(wei_1_eth, Decimal(0))} (Expected: None)")
    # Invalid wei amount (not int)
    print(f"Invalid wei, ETH Price {eth_price_test} -> USD: {calculate_fiat_value(None, eth_price_test)} (Expected: None)")
