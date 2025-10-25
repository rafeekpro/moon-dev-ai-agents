"""
MT5 Trading Agent
AI-powered trading agent for MetaTrader 5 instruments
Supports: GOLD (XAUUSD), EURUSD, CFD stocks, forex, metals, indices
"""

import os
import sys
from datetime import datetime
from termcolor import colored
import pandas as pd
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.model_factory import ModelFactory
from nice_funcs_mt5 import (
    MT5API,
    token_price,
    market_buy,
    market_sell,
    get_position_info,
    close_all_positions,
    get_ohlcv_data
)
import config


class MT5TradingAgent:
    """AI Trading Agent for MT5 Instruments"""

    def __init__(self):
        self.api = MT5API()
        self.model = ModelFactory.create_model(config.AI_MODEL.split('-')[0])  # Extract provider
        self.output_dir = 'src/data/mt5_agent'
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_instrument(self, symbol: str) -> dict:
        """
        Analyze instrument using AI and technical data

        Args:
            symbol: MT5 symbol (e.g., 'EURUSD', 'XAUUSD', 'BTCUSD')

        Returns:
            dict with action, confidence, reasoning
        """
        print(colored(f"\n🔍 Analyzing {symbol}...", "cyan"))

        try:
            # Get market data
            current_price = token_price(symbol)
            symbol_info = self.api.get_symbol_info(symbol)
            position = get_position_info(symbol)
            ohlcv = get_ohlcv_data(symbol, '1H', bars=100)

            # Calculate simple technical indicators
            if not ohlcv.empty:
                ohlcv['SMA_20'] = ohlcv['Close'].rolling(window=20).mean()
                ohlcv['SMA_50'] = ohlcv['Close'].rolling(window=50).mean()
                latest = ohlcv.iloc[-1]
                prev = ohlcv.iloc[-2]

                # Price vs moving averages
                price_vs_sma20 = ((current_price - latest['SMA_20']) / latest['SMA_20']) * 100
                price_vs_sma50 = ((current_price - latest['SMA_50']) / latest['SMA_50']) * 100
                sma_cross = "bullish" if latest['SMA_20'] > latest['SMA_50'] else "bearish"

                # Recent price action
                recent_change = ((current_price - prev['Close']) / prev['Close']) * 100

                technical_summary = f"""
Symbol: {symbol}
Current Price: {current_price}
Spread: {symbol_info.get('spread', 'N/A')} points
Contract Size: {symbol_info.get('contract_size', 'N/A')}

Technical Analysis (1H timeframe):
- Price vs SMA(20): {price_vs_sma20:.2f}%
- Price vs SMA(50): {price_vs_sma50:.2f}%
- SMA Cross: {sma_cross}
- Recent 1H change: {recent_change:.2f}%
- 24H High: {ohlcv['High'].tail(24).max()}
- 24H Low: {ohlcv['Low'].tail(24).min()}

Current Position: {position if position else 'No open position'}
"""
            else:
                technical_summary = f"Symbol: {symbol}, Price: {current_price}, No historical data available"

            # AI Analysis
            system_prompt = f"""You are a professional trader analyzing {symbol} for trading decisions.
Analyze the market data and provide a trading recommendation.

Return ONLY valid JSON in this format:
{{
    "action": "BUY" or "SELL" or "HOLD" or "CLOSE",
    "confidence": 0-100,
    "reasoning": "Brief explanation of your decision",
    "stop_loss": suggested SL price or null,
    "take_profit": suggested TP price or null
}}

Rules:
- BUY: Strong bullish signals, clear uptrend
- SELL: Strong bearish signals, clear downtrend
- HOLD: Wait for better entry, unclear signals
- CLOSE: Exit existing position if open
- Confidence >70 required for BUY/SELL
- Always suggest stop_loss and take_profit for safety
"""

            user_content = f"""Market Data:
{technical_summary}

Account Risk Settings:
- Max loss per trade: ${config.MAX_LOSS_USD}
- Position sizing: conservative

Provide your trading recommendation as JSON."""

            response = self.model.generate_response(
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=config.AI_TEMPERATURE,
                max_tokens=config.AI_MAX_TOKENS
            )

            # Parse AI response
            try:
                # Extract JSON from response
                response_text = response.strip()
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]

                decision = json.loads(response_text)
            except json.JSONDecodeError:
                print(colored(f"⚠️ Failed to parse AI response as JSON", "yellow"))
                decision = {
                    "action": "HOLD",
                    "confidence": 0,
                    "reasoning": "Failed to parse AI response",
                    "stop_loss": None,
                    "take_profit": None
                }

            # Add metadata
            decision['symbol'] = symbol
            decision['current_price'] = current_price
            decision['timestamp'] = datetime.now().isoformat()

            print(colored(f"✅ Analysis complete: {decision['action']} (confidence: {decision['confidence']}%)", "green"))
            print(colored(f"💡 Reasoning: {decision['reasoning']}", "yellow"))

            return decision

        except Exception as e:
            print(colored(f"❌ Error analyzing {symbol}: {e}", "red"))
            return {
                "symbol": symbol,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def execute_trade(self, symbol: str, decision: dict) -> dict:
        """
        Execute trade based on AI decision

        Args:
            symbol: MT5 symbol
            decision: AI decision dict

        Returns:
            Execution result
        """
        action = decision['action']
        confidence = decision.get('confidence', 0)

        # Safety checks
        if confidence < config.MT5_MIN_CONFIDENCE:
            print(colored(f"⚠️ Confidence too low ({confidence}% < {config.MT5_MIN_CONFIDENCE}%), skipping trade", "yellow"))
            return {"status": "skipped", "reason": "low confidence"}

        if action == "HOLD":
            print(colored("⏸️ AI recommends HOLD, no action taken", "yellow"))
            return {"status": "hold"}

        try:
            # Get position info
            position = get_position_info(symbol)

            # CLOSE existing position
            if action == "CLOSE" and position:
                print(colored(f"🔻 Closing position {position['ticket']}...", "magenta"))
                result = self.api.close_position(position['ticket'])
                print(colored(f"✅ Position closed: {result}", "green"))
                return {"status": "closed", "result": result}

            # BUY/SELL - check if position already exists
            if position:
                print(colored(f"⚠️ Position already open for {symbol}, skipping new trade", "yellow"))
                return {"status": "skipped", "reason": "position already open"}

            # Calculate position size (volume in lots)
            volume = config.MT5_DEFAULT_VOLUME

            # Optional: Calculate margin requirement
            margin_calc = self.api.calculate_margin(symbol, action, volume)
            required_margin = margin_calc.get('margin', 0)
            print(colored(f"💰 Required margin: {required_margin} {margin_calc.get('currency', 'USD')}", "cyan"))

            # Open position
            sl = decision.get('stop_loss')
            tp = decision.get('take_profit')

            print(colored(f"📈 Opening {action} position: {volume} lots", "cyan"))
            print(colored(f"   SL: {sl}, TP: {tp}", "cyan"))

            result = self.api.open_position(
                symbol=symbol,
                action=action,
                volume=volume,
                sl=sl,
                tp=tp,
                comment="AI Agent Trade"
            )

            if result.get('retcode') == 10009:  # TRADE_RETCODE_DONE
                print(colored(f"✅ Trade executed successfully: Ticket {result.get('order')}", "green"))
            else:
                print(colored(f"⚠️ Trade result: {result}", "yellow"))

            return {"status": "executed", "result": result}

        except Exception as e:
            print(colored(f"❌ Trade execution error: {e}", "red"))
            return {"status": "error", "error": str(e)}

    def save_results(self, symbol: str, decision: dict, execution: dict):
        """Save analysis and execution results to CSV"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        result = {
            'timestamp': timestamp,
            'symbol': symbol,
            'action': decision.get('action'),
            'confidence': decision.get('confidence'),
            'reasoning': decision.get('reasoning'),
            'current_price': decision.get('current_price'),
            'stop_loss': decision.get('stop_loss'),
            'take_profit': decision.get('take_profit'),
            'execution_status': execution.get('status'),
            'execution_result': str(execution.get('result', ''))
        }

        # Append to CSV
        df = pd.DataFrame([result])
        csv_path = f"{self.output_dir}/trades.csv"

        if os.path.exists(csv_path):
            df.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            df.to_csv(csv_path, mode='w', header=True, index=False)

        print(colored(f"💾 Results saved to {csv_path}", "green"))

    def run(self, symbols: list = None):
        """
        Run MT5 trading agent for specified symbols

        Args:
            symbols: List of MT5 symbols to trade (defaults to config.MT5_INSTRUMENTS)
        """
        if symbols is None:
            symbols = config.MT5_INSTRUMENTS

        print(colored("\n" + "=" * 60, "cyan"))
        print(colored("🤖 MT5 Trading Agent Started", "cyan", attrs=['bold']))
        print(colored("=" * 60 + "\n", "cyan"))

        # Health check
        try:
            health = self.api.health_check()
            print(colored(f"✅ MT5 Connection: {health}", "green"))
        except Exception as e:
            print(colored(f"❌ MT5 Connection Failed: {e}", "red"))
            return

        # Analyze and trade each instrument
        for symbol in symbols:
            print(colored(f"\n{'─' * 60}", "white"))
            print(colored(f"📊 Processing: {symbol}", "cyan", attrs=['bold']))

            # Analyze
            decision = self.analyze_instrument(symbol)

            # Execute (if not in paper trading mode)
            if config.MT5_PAPER_TRADING:
                print(colored("📝 Paper trading mode - no real execution", "yellow"))
                execution = {"status": "paper_trade", "result": "simulated"}
            else:
                execution = self.execute_trade(symbol, decision)

            # Save results
            self.save_results(symbol, decision, execution)

        print(colored("\n" + "=" * 60, "cyan"))
        print(colored("✅ MT5 Trading Agent Completed", "green", attrs=['bold']))
        print(colored("=" * 60 + "\n", "cyan"))


# ===================== STANDALONE EXECUTION =====================

if __name__ == '__main__':
    """Run MT5 trading agent standalone"""

    agent = MT5TradingAgent()

    # Test with common instruments
    test_symbols = ['EURUSD', 'XAUUSD']  # Forex and Gold

    agent.run(symbols=test_symbols)
