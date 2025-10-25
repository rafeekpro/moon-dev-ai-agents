"""
MetaTrader 5 Trading Functions
Professional wrapper for MT5 Windows Gateway API
Supports: GOLD (XAUUSD), EURUSD, CFD stocks, and all MT5 symbols
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# MT5 API Configuration
MT5_API_BASE_URL = os.getenv('MT5_API_BASE_URL', 'http://10.0.0.1:8001')
MT5_API_TIMEOUT = int(os.getenv('MT5_API_TIMEOUT', '30'))


class MT5API:
    """MetaTrader 5 API Client"""

    def __init__(self, base_url: str = MT5_API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method,
                url,
                timeout=MT5_API_TIMEOUT,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ MT5 API Error: {e}")
            raise

    # ===================== HEALTH =====================

    def health_check(self) -> Dict:
        """Check MT5 connection health"""
        return self._request('GET', '/health/')

    # ===================== MARKET DATA =====================

    def get_symbols(self, group: Optional[str] = None) -> List[str]:
        """
        Get all available symbols

        Args:
            group: Filter by group (e.g., 'Forex*', 'Metals*', 'Stocks*')

        Returns:
            List of symbol names
        """
        params = {'group': group} if group else {}
        response = self._request('GET', '/api/market/symbols', params=params)
        return response.get('symbols', [])

    def get_symbol_info(self, symbol: str) -> Dict:
        """
        Get detailed symbol information

        Args:
            symbol: Symbol name (e.g., 'EURUSD', 'GOLD.pro', 'XAUUSD')

        Returns:
            Dict with symbol info (spread, digits, contract_size, etc.)
        """
        return self._request('GET', f'/api/market/symbols/{symbol}')

    def get_current_price(self, symbol: str) -> Dict:
        """
        Get current tick (bid/ask) for symbol

        Args:
            symbol: Symbol name

        Returns:
            Dict with bid, ask, last, time
        """
        return self._request('GET', f'/api/market/symbols/{symbol}/tick')

    def get_ohlcv_data(
        self,
        symbol: str,
        timeframe: Union[str, int] = 'H1',
        start_pos: int = 0,
        count: int = 100
    ) -> pd.DataFrame:
        """
        Get OHLCV data for backtesting

        Args:
            symbol: Symbol name (e.g., 'EURUSD', 'XAUUSD')
            timeframe: 'M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1' or minutes as int
            start_pos: Starting position (0 = most recent)
            count: Number of bars to retrieve (max 10000)

        Returns:
            pandas DataFrame with OHLCV data
        """
        params = {
            'timeframe': timeframe,
            'start_pos': start_pos,
            'count': count
        }
        response = self._request('GET', f'/api/market/rates/{symbol}/from-pos', params=params)

        if 'rates' in response and response['rates']:
            df = pd.DataFrame(response['rates'])
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            return df
        return pd.DataFrame()

    def get_ohlcv_range(
        self,
        symbol: str,
        timeframe: Union[str, int] = 'H1',
        date_from: datetime = None,
        date_to: datetime = None
    ) -> pd.DataFrame:
        """
        Get OHLCV data for specific date range

        Args:
            symbol: Symbol name
            timeframe: Timeframe (M1, H1, etc.)
            date_from: Start date
            date_to: End date

        Returns:
            pandas DataFrame with OHLCV data
        """
        if date_from is None:
            date_from = datetime.now() - timedelta(days=30)
        if date_to is None:
            date_to = datetime.now()

        params = {
            'timeframe': timeframe,
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat()
        }
        response = self._request('GET', f'/api/market/rates/{symbol}/range', params=params)

        if 'rates' in response and response['rates']:
            df = pd.DataFrame(response['rates'])
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            return df
        return pd.DataFrame()

    # ===================== TRADING =====================

    def get_all_positions(self) -> List[Dict]:
        """Get all open positions"""
        return self._request('GET', '/api/trading/positions')

    def get_position(self, ticket: int) -> Dict:
        """
        Get specific position by ticket

        Args:
            ticket: Position ticket number

        Returns:
            Position info
        """
        return self._request('GET', f'/api/trading/positions/{ticket}')

    def open_position(
        self,
        symbol: str,
        action: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "AI Agent Trade"
    ) -> Dict:
        """
        Open a new position (market order)

        Args:
            symbol: Symbol name (e.g., 'EURUSD', 'XAUUSD')
            action: 'BUY' or 'SELL'
            volume: Volume in lots (e.g., 0.01, 0.1, 1.0)
            sl: Stop loss price (optional)
            tp: Take profit price (optional)
            comment: Order comment

        Returns:
            TradeResponse with ticket, status, etc.
        """
        data = {
            'symbol': symbol,
            'action': action.upper(),
            'volume': volume,
            'comment': comment
        }
        if sl is not None:
            data['sl'] = sl
        if tp is not None:
            data['tp'] = tp

        return self._request('POST', '/api/trading/positions', json=data)

    def close_position(self, ticket: int) -> Dict:
        """
        Close position by ticket

        Args:
            ticket: Position ticket number

        Returns:
            TradeResponse
        """
        return self._request('DELETE', f'/api/trading/positions/{ticket}')

    def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict:
        """
        Modify position SL/TP

        Args:
            ticket: Position ticket number
            sl: New stop loss
            tp: New take profit

        Returns:
            TradeResponse
        """
        data = {}
        if sl is not None:
            data['sl'] = sl
        if tp is not None:
            data['tp'] = tp

        return self._request('PUT', f'/api/trading/positions/{ticket}', json=data)

    # ===================== CALCULATIONS =====================

    def calculate_margin(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None
    ) -> Dict:
        """
        Calculate required margin BEFORE opening position

        Args:
            symbol: Symbol name
            order_type: 'BUY' or 'SELL'
            volume: Volume in lots
            price: Price for calculation (uses current if not provided)

        Returns:
            Dict with margin, currency
        """
        data = {
            'symbol': symbol,
            'order_type': order_type.upper(),
            'volume': volume
        }
        if price is not None:
            data['price'] = price

        return self._request('POST', '/api/calculate/margin', json=data)

    def calculate_profit(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price_open: float,
        price_close: float
    ) -> Dict:
        """
        Calculate potential profit/loss BEFORE opening position

        Args:
            symbol: Symbol name
            order_type: 'BUY' or 'SELL'
            volume: Volume in lots
            price_open: Opening price
            price_close: Closing price

        Returns:
            Dict with profit, currency
        """
        data = {
            'symbol': symbol,
            'order_type': order_type.upper(),
            'volume': volume,
            'price_open': price_open,
            'price_close': price_close
        }

        return self._request('POST', '/api/calculate/profit', json=data)

    # ===================== ACCOUNT INFO =====================

    def get_account_info(self) -> Dict:
        """Get account information"""
        return self._request('GET', '/api/account/info')


# ===================== CONVENIENCE FUNCTIONS =====================

def token_price(symbol: str) -> float:
    """
    Get current price for symbol (similar to crypto nice_funcs)

    Args:
        symbol: Symbol name (e.g., 'EURUSD', 'XAUUSD')

    Returns:
        Current price (mid price between bid/ask)
    """
    api = MT5API()
    tick = api.get_current_price(symbol)
    return (tick['bid'] + tick['ask']) / 2


def market_buy(symbol: str, volume: float, sl: float = None, tp: float = None) -> Dict:
    """
    Buy instrument at market price

    Args:
        symbol: Symbol name
        volume: Volume in lots (e.g., 0.01 for micro lot)
        sl: Stop loss price
        tp: Take profit price

    Returns:
        Trade response
    """
    api = MT5API()
    return api.open_position(symbol, 'BUY', volume, sl, tp)


def market_sell(symbol: str, volume: float, sl: float = None, tp: float = None) -> Dict:
    """
    Sell instrument at market price

    Args:
        symbol: Symbol name
        volume: Volume in lots
        sl: Stop loss price
        tp: Take profit price

    Returns:
        Trade response
    """
    api = MT5API()
    return api.open_position(symbol, 'SELL', volume, sl, tp)


def close_all_positions(symbol: str = None) -> List[Dict]:
    """
    Close all positions (optionally filtered by symbol)

    Args:
        symbol: Optional symbol filter

    Returns:
        List of close responses
    """
    api = MT5API()
    positions = api.get_all_positions()
    results = []

    for pos in positions:
        if symbol is None or pos.get('symbol') == symbol:
            result = api.close_position(pos['ticket'])
            results.append(result)

    return results


def get_position_info(symbol: str) -> Optional[Dict]:
    """
    Get current position for symbol

    Args:
        symbol: Symbol name

    Returns:
        Position dict or None if no position
    """
    api = MT5API()
    positions = api.get_all_positions()

    for pos in positions:
        if pos.get('symbol') == symbol:
            return pos

    return None


def get_ohlcv_data(
    symbol: str,
    timeframe: str = '1H',
    bars: int = 100
) -> pd.DataFrame:
    """
    Get OHLCV data for backtesting (compatible with backtesting.py)

    Args:
        symbol: Symbol name
        timeframe: '1m', '5m', '15m', '1H', '4H', '1D'
        bars: Number of bars

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
    """
    # Convert timeframe to MT5 format
    tf_map = {
        '1m': 'M1', '5m': 'M5', '15m': 'M15', '30m': 'M30',
        '1H': 'H1', '4H': 'H4', '1D': 'D1', '1W': 'W1'
    }
    mt5_tf = tf_map.get(timeframe, timeframe)

    api = MT5API()
    df = api.get_ohlcv_data(symbol, mt5_tf, start_pos=0, count=bars)

    # Rename columns to match backtesting.py convention
    if not df.empty:
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'tick_volume': 'Volume'
        }, inplace=True)

    return df[['Open', 'High', 'Low', 'Close', 'Volume']]


# ===================== EXAMPLE USAGE =====================

if __name__ == '__main__':
    """Test MT5 API connection"""

    api = MT5API()

    print("🏥 Health Check:")
    health = api.health_check()
    print(health)

    print("\n📊 Available Forex Symbols:")
    symbols = api.get_symbols(group='Forex*')
    print(symbols[:10])  # Show first 10

    print("\n💰 EURUSD Current Price:")
    tick = api.get_current_price('EURUSD')
    print(f"Bid: {tick['bid']}, Ask: {tick['ask']}")

    print("\n📈 XAUUSD (GOLD) OHLCV Data:")
    df = get_ohlcv_data('XAUUSD', '1H', bars=10)
    print(df)

    print("\n📍 Current Positions:")
    positions = api.get_all_positions()
    print(f"Open positions: {len(positions)}")

    print("\n✅ MT5 API Integration Ready!")
