#!/usr/bin/env python3
"""
Quick MT5 API Connection Test
Tests connectivity to your MT5 Gateway API
"""

import sys
import os
sys.path.append('src')

from src.nice_funcs_mt5 import MT5API
from termcolor import colored

def test_mt5_connection():
    """Test MT5 API connection and basic functionality"""

    print(colored("\n" + "="*60, "cyan"))
    print(colored("🧪 MT5 API Connection Test", "cyan", attrs=['bold']))
    print(colored("="*60 + "\n", "cyan"))

    try:
        api = MT5API()

        # Test 1: Health Check
        print(colored("1️⃣ Testing Health Check...", "yellow"))
        health = api.health_check()
        print(colored(f"   ✅ MT5 Connected: {health}", "green"))

        # Test 2: Get Symbols
        print(colored("\n2️⃣ Testing Symbol Retrieval...", "yellow"))
        symbols = api.get_symbols(group='Forex*')
        print(colored(f"   ✅ Found {len(symbols)} forex symbols", "green"))
        print(colored(f"   📊 Sample symbols: {symbols[:5]}", "white"))

        # Test 3: Get EURUSD Price
        print(colored("\n3️⃣ Testing Price Retrieval (EURUSD)...", "yellow"))
        tick = api.get_current_price('EURUSD')
        print(colored(f"   ✅ EURUSD Bid: {tick['bid']}, Ask: {tick['ask']}", "green"))

        # Test 4: Get GOLD Price (if available)
        print(colored("\n4️⃣ Testing Price Retrieval (XAUUSD/GOLD)...", "yellow"))
        try:
            tick_gold = api.get_current_price('XAUUSD')
            print(colored(f"   ✅ GOLD Bid: {tick_gold['bid']}, Ask: {tick_gold['ask']}", "green"))
        except:
            print(colored(f"   ⚠️ XAUUSD not available, trying GOLD...", "yellow"))
            try:
                tick_gold = api.get_current_price('GOLD')
                print(colored(f"   ✅ GOLD Bid: {tick_gold['bid']}, Ask: {tick_gold['ask']}", "green"))
            except:
                print(colored(f"   ❌ GOLD symbol not found on this broker", "red"))

        # Test 5: Get Symbol Info
        print(colored("\n5️⃣ Testing Symbol Info...", "yellow"))
        info = api.get_symbol_info('EURUSD')
        print(colored(f"   ✅ EURUSD Info:", "green"))
        print(colored(f"      - Spread: {info.get('spread', 'N/A')} points", "white"))
        print(colored(f"      - Contract Size: {info.get('contract_size', 'N/A')}", "white"))
        print(colored(f"      - Digits: {info.get('digits', 'N/A')}", "white"))

        # Test 6: Get OHLCV Data
        print(colored("\n6️⃣ Testing OHLCV Data Retrieval...", "yellow"))
        from src.nice_funcs_mt5 import get_ohlcv_data
        df = get_ohlcv_data('EURUSD', '1H', bars=10)
        print(colored(f"   ✅ Retrieved {len(df)} bars of data", "green"))
        print(colored(f"\n{df.head()}", "white"))

        # Test 7: Get Current Positions
        print(colored("\n7️⃣ Testing Position Retrieval...", "yellow"))
        positions = api.get_all_positions()
        print(colored(f"   ✅ Current open positions: {len(positions)}", "green"))
        if positions:
            for pos in positions:
                print(colored(f"      - {pos.get('symbol')}: {pos.get('type')} {pos.get('volume')} lots", "white"))

        # Test 8: Calculate Margin
        print(colored("\n8️⃣ Testing Margin Calculation...", "yellow"))
        margin = api.calculate_margin('EURUSD', 'BUY', volume=0.01)
        print(colored(f"   ✅ Required margin for 0.01 lot EURUSD: {margin['margin']} {margin['currency']}", "green"))

        # Summary
        print(colored("\n" + "="*60, "green"))
        print(colored("✅ ALL TESTS PASSED!", "green", attrs=['bold']))
        print(colored("="*60 + "\n", "green"))
        print(colored("🚀 Your MT5 API is ready to use!", "cyan"))
        print(colored("\nNext steps:", "yellow"))
        print(colored("1. Configure MT5_INSTRUMENTS in src/config.py", "white"))
        print(colored("2. Set MT5_PAPER_TRADING = True for testing", "white"))
        print(colored("3. Run: python src/agents/mt5_trading_agent.py", "white"))
        print(colored("4. Or enable 'mt5': True in main.py and run: python src/main.py\n", "white"))

        return True

    except Exception as e:
        print(colored(f"\n❌ Test Failed: {e}", "red"))
        print(colored("\nTroubleshooting:", "yellow"))
        print(colored("1. Check MT5_API_BASE_URL in .env file", "white"))
        print(colored("2. Ensure MT5 Gateway is running at http://10.0.0.1:8001", "white"))
        print(colored("3. Test connectivity: curl http://10.0.0.1:8001/health/", "white"))
        print(colored("4. Check firewall settings\n", "white"))
        return False

if __name__ == '__main__':
    success = test_mt5_connection()
    sys.exit(0 if success else 1)
