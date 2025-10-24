"""
🌙 Moon Dev's Polymarket Prediction Market Agent
Built with love by Moon Dev 🚀

This agent scans Polymarket trades, saves markets to CSV, and uses AI to make predictions.
NO ACTUAL TRADING - just predictions and analysis for now.
"""

import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from termcolor import cprint

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.models.model_factory import ModelFactory

# ==============================================================================
# CONFIGURATION - Customize these settings
# ==============================================================================

# Trade filtering
MIN_TRADE_SIZE_USD = 100  # Only track trades over this amount

# Agent behavior
SLEEP_BETWEEN_RUNS_MINUTES = 5  # Run cycle interval
MARKETS_TO_ANALYZE = 50  # Number of recent markets to send to AI
MARKETS_TO_DISPLAY = 20  # Number of recent markets to print after each update

# AI Configuration
USE_SWARM_MODE = True  # Use swarm AI (multiple models) instead of single XAI model
AI_MODEL_PROVIDER = "xai"  # Model to use if USE_SWARM_MODE = False
AI_MODEL_NAME = "grok-2-fast-reasoning"  # Model name if not using swarm

# Data paths
DATA_FOLDER = os.path.join(project_root, "src/data/polymarket")
MARKETS_CSV = os.path.join(DATA_FOLDER, "markets.csv")

# Polymarket API
POLYMARKET_API_BASE = "https://data-api.polymarket.com"

# ==============================================================================
# Polymarket Agent
# ==============================================================================

class PolymarketAgent:
    """Agent that tracks Polymarket markets and provides AI predictions"""

    def __init__(self):
        """Initialize the Polymarket agent"""
        cprint("\n" + "="*80, "cyan")
        cprint("🌙 Polymarket Prediction Market Agent - Initializing", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")

        # Create data folder if it doesn't exist
        os.makedirs(DATA_FOLDER, exist_ok=True)

        # Initialize AI models
        if USE_SWARM_MODE:
            cprint("🤖 Using SWARM MODE - Multiple AI models", "green")
            try:
                from src.agents.swarm_agent import get_swarm_consensus
                self.swarm_agent = get_swarm_consensus
                cprint("✅ Swarm agent loaded successfully", "green")
            except Exception as e:
                cprint(f"❌ Failed to load swarm agent: {e}", "red")
                cprint("💡 Falling back to single model mode", "yellow")
                self.swarm_agent = None
                self.model = ModelFactory.create_model(AI_MODEL_PROVIDER, AI_MODEL_NAME)
        else:
            cprint(f"🤖 Using single model: {AI_MODEL_PROVIDER}/{AI_MODEL_NAME}", "green")
            self.model = ModelFactory.create_model(AI_MODEL_PROVIDER, AI_MODEL_NAME)
            self.swarm_agent = None

        # Initialize markets DataFrame
        self.markets_df = self._load_markets()

        cprint(f"📊 Loaded {len(self.markets_df)} existing markets from CSV", "cyan")
        cprint("✨ Initialization complete!\n", "green")

    def _load_markets(self):
        """Load existing markets from CSV or create empty DataFrame"""
        if os.path.exists(MARKETS_CSV):
            try:
                df = pd.read_csv(MARKETS_CSV)
                cprint(f"✅ Loaded existing markets from {MARKETS_CSV}", "green")
                return df
            except Exception as e:
                cprint(f"⚠️ Error loading CSV: {e}", "yellow")
                cprint("Creating new DataFrame", "yellow")

        # Create new DataFrame with required columns
        return pd.DataFrame(columns=[
            'timestamp', 'market_id', 'event_slug', 'title',
            'outcome', 'price', 'size_usd', 'first_seen'
        ])

    def _save_markets(self):
        """Save markets DataFrame to CSV"""
        try:
            self.markets_df.to_csv(MARKETS_CSV, index=False)
            cprint(f"💾 Saved {len(self.markets_df)} markets to CSV", "green")
        except Exception as e:
            cprint(f"❌ Error saving CSV: {e}", "red")

    def fetch_recent_trades(self, hours_back=24):
        """Fetch recent trades from Polymarket API

        Args:
            hours_back: How many hours back to fetch trades

        Returns:
            List of trade dictionaries
        """
        try:
            cprint(f"\n📡 Fetching trades from last {hours_back} hours...", "yellow")

            # Calculate timestamp for X hours ago
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            cutoff_timestamp = int(cutoff_time.timestamp())

            # Fetch trades
            url = f"{POLYMARKET_API_BASE}/trades"
            params = {
                'limit': 1000,  # Get lots of trades
                '_min_timestamp': cutoff_timestamp
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            trades = response.json()
            cprint(f"✅ Fetched {len(trades)} total trades", "green")

            # Filter for trades over MIN_TRADE_SIZE_USD
            filtered_trades = [
                trade for trade in trades
                if float(trade.get('size', 0)) >= MIN_TRADE_SIZE_USD
            ]

            cprint(f"💰 Found {len(filtered_trades)} trades over ${MIN_TRADE_SIZE_USD}", "cyan")

            return filtered_trades

        except Exception as e:
            cprint(f"❌ Error fetching trades: {e}", "red")
            return []

    def process_trades(self, trades):
        """Process trades and add new markets to DataFrame

        Args:
            trades: List of trade dictionaries from API
        """
        new_markets = 0

        for trade in trades:
            try:
                # Extract trade data
                market_id = trade.get('market', '')
                event_slug = trade.get('eventSlug', '')
                title = trade.get('title', 'Unknown Market')
                outcome = trade.get('outcome', '')
                price = float(trade.get('price', 0))
                size_usd = float(trade.get('size', 0))
                timestamp = trade.get('timestamp', '')

                # Check if market already exists
                if market_id in self.markets_df['market_id'].values:
                    continue

                # Add new market
                new_market = {
                    'timestamp': timestamp,
                    'market_id': market_id,
                    'event_slug': event_slug,
                    'title': title,
                    'outcome': outcome,
                    'price': price,
                    'size_usd': size_usd,
                    'first_seen': datetime.now().isoformat()
                }

                self.markets_df = pd.concat([
                    self.markets_df,
                    pd.DataFrame([new_market])
                ], ignore_index=True)

                new_markets += 1

            except Exception as e:
                cprint(f"⚠️ Error processing trade: {e}", "yellow")
                continue

        if new_markets > 0:
            cprint(f"🆕 Added {new_markets} new markets to database", "green", attrs=['bold'])
            self._save_markets()
        else:
            cprint("ℹ️ No new markets to add", "cyan")

    def display_recent_markets(self):
        """Display the most recent markets from CSV"""
        if len(self.markets_df) == 0:
            cprint("\n📊 No markets in database yet", "yellow")
            return

        cprint("\n" + "="*80, "cyan")
        cprint(f"📊 Most Recent {min(MARKETS_TO_DISPLAY, len(self.markets_df))} Markets", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")

        # Get most recent markets
        recent = self.markets_df.tail(MARKETS_TO_DISPLAY)

        for idx, row in recent.iterrows():
            title = row['title'][:60] + "..." if len(row['title']) > 60 else row['title']
            size = row['size_usd']
            outcome = row['outcome']

            cprint(f"\n💵 ${size:,.2f} trade on {outcome}", "yellow")
            cprint(f"📌 {title}", "white")
            cprint(f"🔗 https://polymarket.com/event/{row['event_slug']}", "cyan")

        cprint("\n" + "="*80, "cyan")
        cprint(f"Total markets tracked: {len(self.markets_df)}", "green", attrs=['bold'])
        cprint("="*80 + "\n", "cyan")

    def get_ai_predictions(self):
        """Get AI predictions for recent markets"""
        if len(self.markets_df) == 0:
            cprint("\n⚠️ No markets to analyze yet", "yellow")
            return

        # Get last N markets for analysis
        markets_to_analyze = self.markets_df.tail(MARKETS_TO_ANALYZE)

        if len(markets_to_analyze) == 0:
            cprint("\n⚠️ No markets available for analysis", "yellow")
            return

        cprint("\n" + "="*80, "magenta")
        cprint(f"🤖 AI Analysis - Analyzing {len(markets_to_analyze)} markets", "magenta", attrs=['bold'])
        cprint("="*80, "magenta")

        # Build prompt with market information
        markets_text = "\n\n".join([
            f"Market {i+1}:\n"
            f"Title: {row['title']}\n"
            f"Recent trade: ${row['size_usd']:,.2f} on {row['outcome']}\n"
            f"Link: https://polymarket.com/event/{row['event_slug']}"
            for i, (_, row) in enumerate(markets_to_analyze.iterrows())
        ])

        system_prompt = """You are a prediction market expert analyzing Polymarket markets.
For each market, provide your prediction in this exact format:

MARKET [number]: [decision]
Reasoning: [brief 1-2 sentence explanation]

Decision must be one of: YES, NO, or NO_TRADE
- YES means you would bet on the "Yes" outcome
- NO means you would bet on the "No" outcome
- NO_TRADE means you would not take a position

Be concise and focused on the most promising opportunities."""

        user_prompt = f"""Analyze these {len(markets_to_analyze)} Polymarket markets and provide your predictions:

{markets_text}

Provide predictions for each market in the specified format."""

        if USE_SWARM_MODE and self.swarm_agent:
            # Use swarm mode - get predictions from multiple AIs
            cprint("\n🌊 Getting predictions from AI swarm...\n", "cyan")

            try:
                # Import swarm agent
                from src.agents.swarm_agent import SwarmAgent

                swarm = SwarmAgent()
                result = swarm.get_consensus(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    task_description="polymarket_predictions"
                )

                # Display individual AI responses
                cprint("\n" + "="*80, "yellow")
                cprint("🤖 Individual AI Predictions", "yellow", attrs=['bold'])
                cprint("="*80, "yellow")

                for model_name, response in result['individual_responses'].items():
                    cprint(f"\n{'='*80}", "cyan")
                    cprint(f"🤖 {model_name.upper()}", "cyan", attrs=['bold'])
                    cprint(f"{'='*80}", "cyan")
                    cprint(response, "white")

                # Display consensus
                cprint("\n" + "="*80, "green")
                cprint("🎯 CONSENSUS DECISION", "green", attrs=['bold'])
                cprint("="*80, "green")
                cprint(result['consensus'], "white")
                cprint("="*80 + "\n", "green")

            except Exception as e:
                cprint(f"❌ Error getting swarm predictions: {e}", "red")
                cprint("💡 Falling back to single model", "yellow")
                # Fall back to single model
                response = self.model.generate_response(
                    system_prompt=system_prompt,
                    user_content=user_prompt,
                    temperature=0.7
                )
                cprint(f"\n{response.content}\n", "white")
        else:
            # Use single model
            cprint(f"\n🤖 Getting predictions from {AI_MODEL_PROVIDER}/{AI_MODEL_NAME}...\n", "cyan")

            try:
                response = self.model.generate_response(
                    system_prompt=system_prompt,
                    user_content=user_prompt,
                    temperature=0.7
                )

                cprint("="*80, "green")
                cprint("🎯 AI PREDICTION", "green", attrs=['bold'])
                cprint("="*80, "green")
                cprint(response.content, "white")
                cprint("="*80 + "\n", "green")

            except Exception as e:
                cprint(f"❌ Error getting prediction: {e}", "red")

    def run_cycle(self):
        """Run one complete analysis cycle"""
        cprint("\n" + "="*80, "magenta")
        cprint("🔄 Starting Polymarket Analysis Cycle", "magenta", attrs=['bold'])
        cprint(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "magenta")
        cprint("="*80 + "\n", "magenta")

        # Step 1: Fetch recent trades
        trades = self.fetch_recent_trades(hours_back=24)

        # Step 2: Process and save new markets
        self.process_trades(trades)

        # Step 3: Display recent markets
        self.display_recent_markets()

        # Step 4: Get AI predictions
        self.get_ai_predictions()

        cprint("\n" + "="*80, "green")
        cprint("✅ Cycle complete!", "green", attrs=['bold'])
        cprint("="*80 + "\n", "green")


def main():
    """Main loop - runs continuously"""
    cprint("\n" + "="*80, "cyan")
    cprint("🌙 Moon Dev's Polymarket Agent - Starting Up", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")
    cprint(f"💰 Tracking trades over ${MIN_TRADE_SIZE_USD}", "yellow")
    cprint(f"⏱️  Running every {SLEEP_BETWEEN_RUNS_MINUTES} minutes", "yellow")
    cprint(f"🤖 AI Mode: {'SWARM' if USE_SWARM_MODE else 'Single Model'}", "yellow")
    cprint("="*80 + "\n", "cyan")

    # Initialize agent
    agent = PolymarketAgent()

    # Main loop
    try:
        while True:
            # Run analysis cycle
            agent.run_cycle()

            # Sleep until next cycle
            sleep_seconds = SLEEP_BETWEEN_RUNS_MINUTES * 60
            cprint(f"💤 Sleeping for {SLEEP_BETWEEN_RUNS_MINUTES} minutes...\n", "cyan")
            time.sleep(sleep_seconds)

    except KeyboardInterrupt:
        cprint("\n\n" + "="*80, "yellow")
        cprint("⚠️ Polymarket Agent stopped by user", "yellow", attrs=['bold'])
        cprint("="*80 + "\n", "yellow")
        sys.exit(0)


if __name__ == "__main__":
    main()
