#!/usr/bin/env python3
"""
MT5 Basic Usage Examples
Demonstrates basic MT5 API functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nice_funcs_mt5 import (
    MT5API,
    token_price,
    market_buy,
    market_sell,
    get_position_info,
    get_ohlcv_data
)
from termcolor import colored


def example_1_price_check():
    """Example 1: Check current prices"""
    print(colored("\n📊 Example 1: Price Check", "cyan", attrs=['bold']))
    print(colored("─" * 60, "white"))

    symbols = ['EURUSD', 'XAUUSD', 'GBPUSD']

    for symbol in symbols:
        try:
            price = token_price(symbol)
            print(colored(f"{symbol}: {price:.5f}", "green"))
        except Exception as e:
            print(colored(f"{symbol}: Error - {e}", "red"))


def example_2_symbol_info():
    """Example 2: Get detailed symbol information"""
    print(colored("\n📋 Example 2: Symbol Information", "cyan", attrs=['bold']))
    print(colored("─" * 60, "white"))

    api = MT5API()
    symbol = 'EURUSD'

    info = api.get_symbol_info(symbol)
    print(colored(f"\n{symbol} Details:", "yellow"))
    print(colored(f"  Spread: {info.get('spread', 'N/A')} points", "white"))
    print(colored(f"  Contract Size: {info.get('contract_size', 'N/A')}", "white"))
    print(colored(f"  Digits: {info.get('digits', 'N/A')}", "white"))
    print(colored(f"  Point: {info.get('point', 'N/A')}", "white"))


def example_3_ohlcv_data():
    """Example 3: Get OHLCV historical data"""
    print(colored("\n📈 Example 3: OHLCV Data", "cyan", attrs=['bold']))
    print(colored("─" * 60, "white"))

    symbol = 'EURUSD'
    df = get_ohlcv_data(symbol, timeframe='1H', bars=10)

    print(colored(f"\nLast 10 hourly bars for {symbol}:", "yellow"))
    print(df.to_string())

    # Calculate simple statistics
    print(colored(f"\n📊 Statistics:", "yellow"))
    print(colored(f"  High: {df['High'].max():.5f}", "green"))
    print(colored(f"  Low: {df['Low'].min():.5f}", "red"))
    print(colored(f"  Average Volume: {df['Volume'].mean():.0f}", "white"))


def example_4_margin_calculation():
    """Example 4: Calculate required margin before trading"""
    print(colored("\n💰 Example 4: Margin Calculation", "cyan", attrs=['bold']))
    print(colored("─" * 60, "white"))

    api = MT5API()
    symbol = 'EURUSD'
    volumes = [0.01, 0.1, 1.0]  # micro, mini, standard lot

    print(colored(f"\nMargin requirements for {symbol}:", "yellow"))
    for volume in volumes:
        margin = api.calculate_margin(symbol, 'BUY', volume)
        lot_type = {0.01: "Micro", 0.1: "Mini", 1.0: "Standard"}[volume]
        print(colored(
            f"  {lot_type} lot ({volume}): {margin['margin']:.2f} {margin['currency']}",
            "white"
        ))


def example_5_profit_calculation():
    """Example 5: Calculate potential profit/loss"""
    print(colored("\n💵 Example 5: Profit Calculation", "cyan", attrs=['bold']))
    print(colored("─" * 60, "white"))

    api = MT5API()
    symbol = 'EURUSD'

    # Scenario: Buy at 1.1000, sell at different prices
    scenarios = [
        (1.1000, 1.1050, "50 pips profit"),
        (1.1000, 1.1100, "100 pips profit"),
        (1.1000, 1.0950, "50 pips loss"),
    ]

    print(colored(f"\nProfit scenarios for {symbol} (0.1 lot):", "yellow"))
    for open_price, close_price, description in scenarios:
        profit = api.calculate_profit(
            symbol=symbol,
            order_type='BUY',
            volume=0.1,
            price_open=open_price,
            price_close=close_price
        )
        color = "green" if profit['profit'] > 0 else "red"
        print(colored(
            f"  {description}: {profit['profit']:+.2f} {profit['currency']}",
            color
        ))


def example_6_check_positions():
    """Example 6: Check current open positions"""
    print(colored("\n📍 Example 6: Current Positions", "cyan", attrs=['bold']))
    print(colored("─" * 60, "white"))

    api = MT5API()
    positions = api.get_all_positions()

    if positions:
        print(colored(f"\nOpen positions: {len(positions)}", "yellow"))
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            pos_type = pos.get('type', 'N/A')
            volume = pos.get('volume', 0)
            profit = pos.get('profit', 0)
            color = "green" if profit > 0 else "red"

            print(colored(
                f"  {symbol}: {pos_type} {volume} lots | P/L: {profit:+.2f}",
                color
            ))
    else:
        print(colored("No open positions", "yellow"))


def example_7_paper_trade():
    """Example 7: Simulate a paper trade (NO REAL EXECUTION)"""
    print(colored("\n📝 Example 7: Paper Trade Simulation", "cyan", attrs=['bold']))
    print(colored("─" * 60, "white"))

    symbol = 'EURUSD'
    volume = 0.01

    # Get current price
    current_price = token_price(symbol)

    # Calculate stop loss and take profit
    sl = current_price - 0.0050  # 50 pips below
    tp = current_price + 0.0100  # 100 pips above

    print(colored(f"\n📊 Trade Setup:", "yellow"))
    print(colored(f"  Symbol: {symbol}", "white"))
    print(colored(f"  Action: BUY", "white"))
    print(colored(f"  Volume: {volume} lot (micro)", "white"))
    print(colored(f"  Entry: {current_price:.5f}", "white"))
    print(colored(f"  Stop Loss: {sl:.5f}", "red"))
    print(colored(f"  Take Profit: {tp:.5f}", "green"))

    # Calculate potential outcomes
    api = MT5API()

    # If TP hit
    tp_profit = api.calculate_profit(symbol, 'BUY', volume, current_price, tp)
    print(colored(
        f"\n✅ If TP hit: +{tp_profit['profit']:.2f} {tp_profit['currency']}",
        "green"
    ))

    # If SL hit
    sl_loss = api.calculate_profit(symbol, 'BUY', volume, current_price, sl)
    print(colored(
        f"❌ If SL hit: {sl_loss['profit']:.2f} {sl_loss['currency']}",
        "red"
    ))

    # Risk/Reward ratio
    rr = abs(tp_profit['profit'] / sl_loss['profit'])
    print(colored(f"\n📊 Risk/Reward Ratio: 1:{rr:.2f}", "cyan"))

    print(colored(
        "\n⚠️ This is a SIMULATION - set MT5_PAPER_TRADING=False for real trades",
        "yellow"
    ))


def example_8_multi_timeframe_analysis():
    """Example 8: Analyze multiple timeframes"""
    print(colored("\n⏱️ Example 8: Multi-Timeframe Analysis", "cyan", attrs=['bold']))
    print(colored("─" * 60, "white"))

    symbol = 'XAUUSD'  # GOLD
    timeframes = ['15m', '1H', '4H']

    print(colored(f"\n{symbol} Analysis:", "yellow"))

    for tf in timeframes:
        df = get_ohlcv_data(symbol, timeframe=tf, bars=50)

        # Calculate simple moving averages
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()

        latest = df.iloc[-1]

        # Determine trend
        if latest['SMA20'] > latest['SMA50']:
            trend = "Bullish ↗"
            color = "green"
        else:
            trend = "Bearish ↘"
            color = "red"

        print(colored(f"  {tf}: {trend} (Price: {latest['Close']:.2f})", color))


def main():
    """Run all examples"""
    print(colored("\n" + "="*60, "cyan"))
    print(colored("🎓 MT5 API - Basic Usage Examples", "cyan", attrs=['bold']))
    print(colored("="*60, "cyan"))

    try:
        # Test connection first
        api = MT5API()
        health = api.health_check()
        print(colored(f"\n✅ MT5 Connected: {health}\n", "green"))

        # Run examples
        example_1_price_check()
        example_2_symbol_info()
        example_3_ohlcv_data()
        example_4_margin_calculation()
        example_5_profit_calculation()
        example_6_check_positions()
        example_7_paper_trade()
        example_8_multi_timeframe_analysis()

        # Summary
        print(colored("\n" + "="*60, "green"))
        print(colored("✅ All examples completed!", "green", attrs=['bold']))
        print(colored("="*60 + "\n", "green"))

        print(colored("Next steps:", "yellow"))
        print(colored("1. Read: src/MT5_INTEGRATION.md", "white"))
        print(colored("2. Read: MT5_QUICKSTART.md", "white"))
        print(colored("3. Run: python src/agents/mt5_trading_agent.py", "white"))
        print(colored("4. Build your own strategies!\n", "white"))

    except Exception as e:
        print(colored(f"\n❌ Error: {e}", "red"))
        print(colored("\nMake sure:", "yellow"))
        print(colored("1. MT5 Gateway API is running (http://10.0.0.1:8001)", "white"))
        print(colored("2. MT5_API_BASE_URL is set in .env", "white"))
        print(colored("3. Run: python test_mt5_connection.py\n", "white"))


if __name__ == '__main__':
    main()
