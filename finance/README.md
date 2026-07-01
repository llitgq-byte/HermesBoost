# Finance

> Stock research and analysis — from pre-market to post-trade.

Personalized stock research workflows built as Hermes skills: pre-market briefing, intraday tracking, and post-trade review. Every workflow is tailored to personal holdings and investment strategies, turning raw market data into actionable context.

## What This Category Does

The finance pipeline automates the research loop that most investors do manually — scanning overnight news before the open, watching positions during the day, and reviewing decisions after the close. Each stage is a standalone Hermes skill, but together they form a continuous workflow where the output of one stage feeds into the next.

The goal is not to predict the market or generate trade signals. It's to **reduce noise and surface what matters** — so that by the time you sit down to make a decision, the groundwork is already done.

## The Three Stages

### 1. Pre-Market Briefing

Before the opening bell, the briefing pulls together everything that happened while the market was closed and distills it into a structured summary.

**What it covers:**
- **Overnight movers** — significant price action in after-hours and international markets
- **Headlines & catalysts** — earnings releases, macro data, sector-level news, analyst upgrades/downgrades
- **Key levels** — support/resistance zones derived from recent price action and technical patterns
- **Opening bias** — a directional read based on pre-market indicators (futures, gaps, volume)

**Why it matters:** Most of the damage (and opportunity) happens in the first 30 minutes. Starting the day with context instead of scrambling for it changes the quality of every decision that follows.

### 2. Intraday Tracking

During market hours, the tracker monitors positions and market conditions, flagging events that require attention.

**What it watches for:**
- **Volume anomalies** — sudden spikes that often precede or confirm price moves
- **Momentum shifts** — trend acceleration, reversal signals, exhaustion patterns
- **Correlation breaks** — when a position diverges from its sector or broader market
- **Risk thresholds** — price levels that trigger predefined stop-loss or take-profit awareness

**Why it matters:** You can't watch every tick of every position. The tracker acts as a filter — it stays quiet when nothing is happening and speaks up when something is.

### 3. Post-Trade Review

After the close, the review reconstructs the day and evaluates decisions against what actually happened.

**What it examines:**
- **Execution quality** — did you get in/out at reasonable prices, or were you chasing?
- **Catalyst accuracy** — did the pre-market thesis play out, or did something unexpected change the narrative?
- **Process evaluation** — was the decision-making sound even if the outcome wasn't?
- **Action items** — specific adjustments for the next session (position sizing, timing, watchlist changes)

**Why it matters:** Improvement comes from reviewing process, not outcome. A good trade can still teach you something, and a bad trade that followed good process teaches you nothing — the review distinguishes between the two.

## Data Sources

All data originates from **publicly available sources**:

- **Market data** — real-time and delayed quotes from public APIs
- **News & headlines** — aggregated from public financial news feeds
- **Fundamental data** — company filings, analyst reports available through public channels
- **Technical indicators** — calculated from raw OHLCV data

No proprietary data, no insider information, no paid-for-alpha signals. The value isn't in exclusive data — it's in how the data is filtered, structured, and presented.

## Who This Is For

This is built for **individual investors managing their own portfolios** — not day traders chasing every tick, not institutional desks with Bloomberg terminals, but people who want a structured research process without the overhead of building one from scratch.

The workflows are opinionated: they reflect a specific investment style and set of priorities. If your approach is different, the skills serve as templates — the logic is transparent and the structure is modular.

## Design Principles

- **No ticker symbols, no holdings** — the skills are generic and configurable; personal positions are stored locally, never in the repo
- **Process over prediction** — the focus is on preparation and review, not on generating buy/sell signals
- **Minimal and readable** — each skill does one thing well; no bloated multi-purpose tools
- **Honest about limitations** — these workflows help with research hygiene, they don't replace judgment

---

> ⚠️ **Disclaimer:** All analysis produced by these workflows is for **personal reference only** and does not constitute financial advice. Nothing here should be interpreted as a recommendation to buy, sell, or hold any security. Always do your own research and consult qualified professionals before making investment decisions.
