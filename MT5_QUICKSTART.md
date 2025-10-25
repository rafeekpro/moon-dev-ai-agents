# 🏆 MetaTrader 5 Integration - Quick Start

## ✅ Co zostało dodane?

Twój projekt AI trading agents teraz obsługuje **MetaTrader 5** przez własne API!

### Nowe pliki:
- `src/nice_funcs_mt5.py` - Wrapper API dla MT5 (podobny do nice_funcs.py dla Solana)
- `src/agents/mt5_trading_agent.py` - AI agent dla GOLD, EURUSD, CFD stocks
- `src/MT5_INTEGRATION.md` - Pełna dokumentacja
- `test_mt5_connection.py` - Test połączenia

### Zmodyfikowane pliki:
- `src/config.py` - Dodano MT5 configuration
- `src/main.py` - Dodano MT5 agent do orkiestracji
- `.env_example` - Dodano MT5_API_BASE_URL

## 🚀 Quick Start (5 minut)

### 1. Dodaj do `.env`

```bash
# MetaTrader 5 API Configuration
MT5_API_BASE_URL=http://10.0.0.1:8001
MT5_API_TIMEOUT=30
```

### 2. Test połączenia

```bash
python test_mt5_connection.py
```

Jeśli widzisz `✅ ALL TESTS PASSED!` - jesteś gotowy!

### 3. Konfiguruj instrumenty w `src/config.py`

```python
# Dodano automatycznie:
MT5_INSTRUMENTS = ['EURUSD', 'XAUUSD', 'GBPUSD']
MT5_DEFAULT_VOLUME = 0.01  # micro lot
MT5_MIN_CONFIDENCE = 70
MT5_PAPER_TRADING = True  # WAŻNE: Testuj najpierw!
```

### 4. Uruchom MT5 Agent

**Opcja A - Standalone:**
```bash
python src/agents/mt5_trading_agent.py
```

**Opcja B - W orkiestracji (z innymi agentami):**

Edytuj `src/main.py`:
```python
ACTIVE_AGENTS = {
    'risk': True,   # Sprawdza limity strat
    'mt5': True,    # <-- WŁĄCZ TO
}
```

Uruchom:
```bash
python src/main.py
```

## 📊 Jak to działa?

### Flow działania:

```
1. MT5 Agent → Pobiera dane (cena, OHLCV, technical indicators)
2. AI Analysis → Claude/GPT/DeepSeek analizuje rynek
3. Decision → {"action": "BUY/SELL/HOLD", "confidence": 75, "reasoning": "..."}
4. Risk Check → Sprawdza confidence > MT5_MIN_CONFIDENCE (70%)
5. Execution → Otwiera pozycję przez MT5 API (jeśli paper_trading=False)
6. Logging → Zapisuje do src/data/mt5_agent/trades.csv
```

### Przykładowy Output:

```
🔍 Analyzing EURUSD...
✅ Analysis complete: BUY (confidence: 82%)
💡 Reasoning: Strong bullish momentum, SMA(20) crossed above SMA(50)
📈 Opening BUY position: 0.01 lots
   SL: 1.0950, TP: 1.1100
✅ Trade executed successfully: Ticket 123456
```

## 🎯 Dostępne Instrumenty (Twoje API)

### Forex (24/5)
- EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF

### Metals
- **GOLD** (XAUUSD) - najpopularniejszy!
- SILVER (XAGUSD)

### CFD Stocks
- AAPL (Apple), TSLA (Tesla), AMZN (Amazon), GOOGL (Google)
- Sprawdź dostępne symbole: `python -c "from src.nice_funcs_mt5 import MT5API; print(MT5API().get_symbols())"`

### Indices
- US30 (Dow Jones), SPX500 (S&P 500), NAS100 (Nasdaq)

## 💡 Przykłady użycia

### Trading z kodu:

```python
from src.nice_funcs_mt5 import market_buy, market_sell, token_price

# Kup GOLD (XAUUSD)
market_buy('XAUUSD', volume=0.01, sl=2650, tp=2700)

# Aktualna cena EURUSD
price = token_price('EURUSD')
print(f"EURUSD: {price}")

# Sprzedaj GBPUSD
market_sell('GBPUSD', volume=0.01, sl=1.2800, tp=1.2700)
```

### Backtesting na MT5 data:

```python
from backtesting import Backtest, Strategy
from src.nice_funcs_mt5 import get_ohlcv_data

# Pobierz 1000 godzinnych barów GOLD
df = get_ohlcv_data('XAUUSD', '1H', bars=1000)

class MyStrategy(Strategy):
    def init(self):
        pass

    def next(self):
        if self.data.Close[-1] > self.data.Open[-1]:
            self.buy()

bt = Backtest(df, MyStrategy, cash=10000)
stats = bt.run()
print(stats)
```

### AI-Driven Trading:

```python
from src.agents.mt5_trading_agent import MT5TradingAgent

agent = MT5TradingAgent()

# Analizuj GOLD
decision = agent.analyze_instrument('XAUUSD')
print(decision)
# {'action': 'BUY', 'confidence': 85, 'reasoning': '...', 'stop_loss': 2650, 'take_profit': 2700}

# Wykonaj (tylko jeśli MT5_PAPER_TRADING = False)
agent.execute_trade('XAUUSD', decision)
```

## 🛡️ Bezpieczeństwo

### 1. ZAWSZE zacznij od Paper Trading

```python
# W src/config.py
MT5_PAPER_TRADING = True  # <-- Zostaw na True dopóki nie przetestujesz!
```

### 2. Użyj małych lotów

```python
MT5_DEFAULT_VOLUME = 0.01  # Micro lot - najmniejsze ryzyko
```

### 3. ZAWSZE używaj Stop Loss

Agent automatycznie generuje SL/TP jeśli `MT5_USE_STOP_LOSS = True`

### 4. Risk Agent Integration

Risk Agent z głównego systemu będzie sprawdzał również pozycje MT5:
```python
ACTIVE_AGENTS = {
    'risk': True,  # Sprawdza MAX_LOSS_USD dla wszystkich pozycji
    'mt5': True,
}
```

## 📈 Position Sizing Guide

### Loty vs Wartość

**Forex (EURUSD):**
- 0.01 lot = $0.10 per pip movement
- 0.1 lot = $1.00 per pip movement
- 1.0 lot = $10.00 per pip movement

**Gold (XAUUSD):**
- 0.01 lot = ~$0.01 per $1 movement
- 0.1 lot = ~$0.10 per $1 movement
- 1.0 lot = ~$1.00 per $1 movement

**Rekomendacja:** Zacznij od 0.01 (micro lot)!

## 🔥 Zaawansowane: Integracja z RBI Agent

RBI Agent może teraz generować strategie dla MT5!

```bash
# 1. Daj RBI agentowi YouTube video o strategii GOLD
python src/agents/rbi_agent.py

# 2. Agent wygeneruje kod strategii
# 3. Pobierze dane z MT5: get_ohlcv_data('XAUUSD', '1H', 1000)
# 4. Uruchomi backtest
# 5. Zwróci performance metrics
```

## 📂 Output Files

Wszystkie transakcje zapisywane w:
```
src/data/mt5_agent/trades.csv
```

Format:
```
timestamp,symbol,action,confidence,reasoning,current_price,stop_loss,take_profit,execution_status,execution_result
2025-01-25 14:30:00,EURUSD,BUY,82,Strong bullish momentum,1.1050,1.0950,1.1100,executed,{"ticket": 123456}
```

## 🐛 Troubleshooting

### "Connection Refused"
```bash
# Test API
curl http://10.0.0.1:8001/health/

# Sprawdź czy MT5 Gateway działa
# Sprawdź firewall
```

### "Symbol not found"
```python
# Lista dostępnych symboli
from src.nice_funcs_mt5 import MT5API
api = MT5API()
print(api.get_symbols())

# Niektóre brokery używają sufiksów
# 'GOLD' vs 'XAUUSD' vs 'GOLD.pro'
```

### "Low confidence - trade skipped"
```python
# Zmniejsz próg w config.py
MT5_MIN_CONFIDENCE = 60  # Zamiast 70
```

## 📚 Więcej Info

- **Pełna dokumentacja:** `src/MT5_INTEGRATION.md`
- **API Docs:** http://10.0.0.1:8001/docs
- **Kod wrapper:** `src/nice_funcs_mt5.py`
- **Kod agent:** `src/agents/mt5_trading_agent.py`

## 🎓 Next Steps

1. ✅ Przetestuj połączenie: `python test_mt5_connection.py`
2. ✅ Skonfiguruj symbole w `config.py`
3. ✅ Uruchom w paper trading mode
4. ✅ Monitor wyniki w `src/data/mt5_agent/trades.csv`
5. ✅ Dostosuj `MT5_MIN_CONFIDENCE` i `MT5_DEFAULT_VOLUME`
6. ✅ Integruj z RBI Agent dla auto-generated strategies
7. ⚠️ Live trading tylko po dokładnych testach!

## 💬 Support

Pytania? Discord: https://discord.gg/8UPuVZ53bh

---

**Built by Moon Dev community 🌙**
**Extended with MT5 integration for GOLD, EURUSD, and CFD trading 🚀**
