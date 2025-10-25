# MetaTrader 5 Integration Guide

## Overview

Integracja z MetaTrader 5 Gateway API umożliwia handel na:
- **Forex**: EURUSD, GBPUSD, USDJPY, etc.
- **Metals**: GOLD (XAUUSD), Silver (XAGUSD)
- **CFD Stocks**: Apple, Tesla, Amazon, etc.
- **Indices**: US30, SPX500, NAS100
- **Crypto CFDs**: BTCUSD, ETHUSD

## Konfiguracja

### 1. Dodaj do `.env`

```bash
# MetaTrader 5 API Configuration
MT5_API_BASE_URL=http://10.0.0.1:8001
MT5_API_TIMEOUT=30
```

### 2. Skonfiguruj w `src/config.py`

```python
# MT5 Configuration
MT5_INSTRUMENTS = ['EURUSD', 'XAUUSD', 'GBPUSD']  # Instrumenty do handlu
MT5_DEFAULT_VOLUME = 0.01  # 0.01 = micro lot, 0.1 = mini lot, 1.0 = standard lot
MT5_MIN_CONFIDENCE = 70  # Minimalna pewność AI (0-100)
MT5_PAPER_TRADING = True  # True = symulacja, False = live trading
MT5_USE_STOP_LOSS = True  # Zawsze używaj stop loss
MT5_USE_TAKE_PROFIT = True  # Zawsze używaj take profit
```

### 3. Aktywuj MT5 Agent w `main.py`

```python
ACTIVE_AGENTS = {
    'risk': True,
    'mt5': True,  # <-- WŁĄCZ
    # ... other agents
}
```

## Użycie

### Standalone - Uruchom tylko MT5 Agent

```bash
python src/agents/mt5_trading_agent.py
```

### W Orkiestracji - Razem z innymi agentami

```bash
python src/main.py
```

## Przykłady Kodu

### Podstawowe Funkcje Trading

```python
from src.nice_funcs_mt5 import market_buy, market_sell, token_price, get_position_info

# Kup EURUSD
result = market_buy('EURUSD', volume=0.01, sl=1.0900, tp=1.1100)

# Sprzedaj GOLD
result = market_sell('XAUUSD', volume=0.01, sl=2700, tp=2600)

# Sprawdź aktualną cenę
price = token_price('EURUSD')
print(f"EURUSD: {price}")

# Sprawdź pozycję
position = get_position_info('EURUSD')
if position:
    print(f"Otwarta pozycja: {position}")
```

### Zaawansowane - Użyj MT5API

```python
from src.nice_funcs_mt5 import MT5API

api = MT5API()

# Health check
health = api.health_check()
print(health)

# Pobierz wszystkie symbole forex
symbols = api.get_symbols(group='Forex*')
print(symbols)

# Pobierz informacje o symbolu
info = api.get_symbol_info('XAUUSD')
print(f"Spread: {info['spread']}, Contract Size: {info['contract_size']}")

# Pobierz OHLCV dla backtestów
import pandas as pd
df = api.get_ohlcv_data('EURUSD', timeframe='H1', count=100)
print(df.head())

# Oblicz margin przed otwarciem pozycji
margin = api.calculate_margin('XAUUSD', 'BUY', volume=0.01)
print(f"Required margin: {margin['margin']} {margin['currency']}")

# Oblicz potencjalny profit
profit = api.calculate_profit(
    symbol='EURUSD',
    order_type='BUY',
    volume=0.1,
    price_open=1.1000,
    price_close=1.1050
)
print(f"Potential profit: {profit['profit']} {profit['currency']}")
```

### Backtesting z MT5 Data

```python
from backtesting import Backtest, Strategy
from src.nice_funcs_mt5 import get_ohlcv_data

# Pobierz dane GOLD
df = get_ohlcv_data('XAUUSD', timeframe='1H', bars=1000)

class GoldStrategy(Strategy):
    def init(self):
        pass

    def next(self):
        if self.data.Close[-1] > self.data.Open[-1]:
            self.buy()
        elif self.position:
            self.position.close()

bt = Backtest(df, GoldStrategy, cash=10000, commission=0.002)
stats = bt.run()
print(stats)
```

## Dostępne Endpointy

### Trading
- `POST /api/trading/positions` - Otwórz pozycję
- `GET /api/trading/positions` - Wszystkie otwarte pozycje
- `GET /api/trading/positions/{ticket}` - Konkretna pozycja
- `DELETE /api/trading/positions/{ticket}` - Zamknij pozycję
- `PUT /api/trading/positions/{ticket}` - Modyfikuj SL/TP

### Market Data
- `GET /api/market/symbols` - Lista symboli
- `GET /api/market/symbols/{symbol}` - Info o symbolu
- `GET /api/market/symbols/{symbol}/tick` - Aktualny tick (bid/ask)
- `GET /api/market/rates/{symbol}/from-pos` - OHLCV od pozycji
- `GET /api/market/rates/{symbol}/range` - OHLCV dla zakresu dat

### Calculations
- `POST /api/calculate/margin` - Oblicz wymagany margin
- `POST /api/calculate/profit` - Oblicz potencjalny profit

### Orders (Pending)
- `POST /api/orders` - Utwórz pending order (LIMIT/STOP)
- `GET /api/orders` - Lista pending orders
- `DELETE /api/orders/{ticket}` - Usuń pending order
- `PUT /api/orders/{ticket}` - Modyfikuj pending order

## Timeframes

Dostępne timeframy:
- `M1` - 1 minuta
- `M5` - 5 minut
- `M15` - 15 minut
- `M30` - 30 minut
- `H1` - 1 godzina
- `H4` - 4 godziny
- `D1` - 1 dzień
- `W1` - 1 tydzień
- `MN1` - 1 miesiąc

Lub jako liczba minut: `1, 5, 15, 30, 60, 240, 1440`

## Position Sizing (Loty)

- **Micro lot**: 0.01 (1,000 units)
- **Mini lot**: 0.1 (10,000 units)
- **Standard lot**: 1.0 (100,000 units)

Przykład dla EURUSD:
- 0.01 lot = $0.10 per pip
- 0.1 lot = $1.00 per pip
- 1.0 lot = $10.00 per pip

Przykład dla XAUUSD (GOLD):
- 0.01 lot = ~$0.01 per point
- 0.1 lot = ~$0.10 per point
- 1.0 lot = ~$1.00 per point

## Bezpieczeństwo

### ZAWSZE używaj Stop Loss
```python
# ✅ DOBRZE - z SL i TP
market_buy('EURUSD', volume=0.01, sl=1.0900, tp=1.1100)

# ❌ ŹLE - bez SL
market_buy('EURUSD', volume=0.01)
```

### Paper Trading Mode
```python
# Testuj strategie bez ryzyka
MT5_PAPER_TRADING = True  # w config.py
```

### Risk Management
```python
# Oblicz margin przed otwarciem
margin = api.calculate_margin('XAUUSD', 'BUY', 0.1)
if margin['margin'] > account_balance * 0.02:  # Max 2% margin
    print("Position too large!")
```

## Integracja z Innymi Agentami

### MT5 + Risk Agent
```python
# Risk Agent sprawdza MAX_LOSS_USD również dla MT5
ACTIVE_AGENTS = {
    'risk': True,  # Sprawdza wszystkie pozycje (Solana + MT5)
    'mt5': True,
}
```

### MT5 + RBI Agent (Strategy Generator)
```python
# 1. Wygeneruj strategię z YouTube video
python src/agents/rbi_agent.py

# 2. Strategy zostanie przetestowana na danych MT5
df = get_ohlcv_data('XAUUSD', '1H', 1000)

# 3. Deploy na live trading
```

### MT5 + Sentiment Agent
```python
# Sentiment Agent analizuje social media
# MT5 Agent wykonuje decyzje handlowe na GOLD/EURUSD
ACTIVE_AGENTS = {
    'sentiment': True,
    'mt5': True,
}
```

## Przykładowe Strategie

### Simple Moving Average Cross
```python
from src.nice_funcs_mt5 import get_ohlcv_data, market_buy, market_sell

df = get_ohlcv_data('EURUSD', '1H', 100)
df['SMA20'] = df['Close'].rolling(20).mean()
df['SMA50'] = df['Close'].rolling(50).mean()

if df['SMA20'].iloc[-1] > df['SMA50'].iloc[-1]:
    # Bullish cross
    market_buy('EURUSD', 0.01, sl=df['Low'].tail(10).min(), tp=df['Close'].iloc[-1] * 1.01)
```

### AI-Driven Strategy
```python
from src.agents.mt5_trading_agent import MT5TradingAgent

agent = MT5TradingAgent()
decision = agent.analyze_instrument('XAUUSD')

if decision['action'] == 'BUY' and decision['confidence'] > 75:
    agent.execute_trade('XAUUSD', decision)
```

## Troubleshooting

### Connection Refused
```bash
# Sprawdź czy API działa
curl http://10.0.0.1:8001/health/

# Sprawdź firewall
# Sprawdź czy MT5 Gateway jest uruchomiony
```

### Invalid Symbol
```python
# Sprawdź dostępne symbole
api = MT5API()
symbols = api.get_symbols()
print(symbols)

# Niektóre brokery używają sufiksów: 'GOLD.pro', 'EURUSD.raw'
```

### Low Confidence Trades Skipped
```python
# Zmniejsz próg pewności w config.py
MT5_MIN_CONFIDENCE = 60  # Zamiast 70
```

## Output Files

Agent zapisuje wszystkie decyzje i wykonania w:
```
src/data/mt5_agent/trades.csv
```

Format:
```
timestamp,symbol,action,confidence,reasoning,current_price,stop_loss,take_profit,execution_status,execution_result
```

## Next Steps

1. **Testuj na Paper Trading** - Ustaw `MT5_PAPER_TRADING = True`
2. **Monitor Performance** - Analizuj `src/data/mt5_agent/trades.csv`
3. **Dostosuj Confidence Threshold** - `MT5_MIN_CONFIDENCE` w config.py
4. **Dodaj Własne Symbole** - `MT5_INSTRUMENTS` w config.py
5. **Integruj z RBI Agent** - Generuj strategie z YouTube
6. **Live Trading** - Ustaw `MT5_PAPER_TRADING = False` (ostrożnie!)

## Support

- API Docs: http://10.0.0.1:8001/docs
- Project README: /src/README.md
- Moon Dev Discord: (link in main README)
