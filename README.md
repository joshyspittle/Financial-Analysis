# Financial Analysis

A personal quantitative finance framework built in Python for multi-asset data ingestion, feature engineering, statistical modelling, performance analysis, and interactive charting. Designed around clean architectural principles — separation of concerns, incremental data updates, and a scalable data structure — with the goal of eventually supporting systematic strategy research and asset pricing.

---

## Contents

1. [Project Overview](#project-overview)
2. [Architecture & Design Decisions](#architecture--design-decisions)
3. [Project Structure](#project-structure)
   - [Root Files](#root-files)
   - [src/](#src)
   - [watchlist/](#watchlist)
   - [data/](#data)
4. [Data Pipeline](#data-pipeline)
5. [Modules In Depth](#modules-in-depth)
   - [features.py](#featurespy)
   - [metrics.py](#metricspy)
   - [models.py](#modelspy)
6. [To-Do & Roadmap](#to-do--roadmap)
7. [Dependencies](#dependencies)
8. [Disclaimer](#disclaimer)

---

## Project Overview

This framework provides an end-to-end pipeline for quantitative financial analysis across multiple asset classes — currently crypto, equities, and macro. It is structured to support:

- **Automated data ingestion** from Yahoo Finance and FRED with incremental updates
- **Feature engineering** — technical indicators, return series, volatility measures
- **Statistical modelling** — stochastic processes, return distributions, simulation
- **Performance & risk metrics** — Sharpe ratio, drawdown, volatility, Value at Risk
- **Interactive charting** — candlestick charts via `lightweight-charts`

The project is intentionally built from scratch rather than wrapping a third-party toolkit, both as a learning exercise in quantitative finance and to maintain full control over assumptions, implementations, and data structures.

---

## Architecture & Design Decisions

### Category-per-file Parquet storage

Data is stored as one `.parquet` file per asset category (e.g. `crypto_data.parquet`, `equities_data.parquet`). This was chosen over:

- **One file per asset** — creates thousands of files at scale, slow directory listings, and sequential I/O when building cross-asset panels
- **CSV** — no native MultiIndex support, verbose text format, slower reads at scale
- **JSON** — not designed for tabular time series; poor read performance and awkward orientation handling with pandas

Parquet handles MultiIndex columns natively, compresses efficiently, and reads significantly faster than CSV at scale.

### MultiIndex column structure `(Asset, Field)`

Each parquet file stores a pandas DataFrame with a two-level column MultiIndex:

```
            BTC                              ETH
            Open   High   Low    Close  Vol  Open   High   Low    Close  Vol
Date
2024-01-01  ...
```

This allows clean cross-asset operations (`panel.xs('Close', axis=1, level=1)`) while keeping all data for a category in a single file. FRED macro assets only carry a `Close` column since FRED returns a single scalar value per date — the `Close` label is a convention applied in `fetch_data()`.

### Separation of fetch vs load vs build

Three distinct responsibilities are kept separate:

- `fetch_data()` — fetches a single asset from a single source, returns a standardised OHLCV DataFrame
- `load_data()` — reads a category parquet into memory with session-level caching
- `build_panel()` — slices a subset of assets from a loaded panel for cross-asset analysis

This avoids mixing I/O, API calls, and analysis logic in the same functions.

### Incremental updates

`run_updates.py` checks the last valid date per asset before fetching, so only new rows are downloaded on subsequent runs. Macro data pulls an extra 90-day overlap to account for data revisions. This keeps API calls minimal and run time fast regardless of watchlist size.

### Pass exactly what the function needs

Functions in `features.py` and `metrics.py` accept either a Close series or a full OHLCV DataFrame depending on what they actually require — not always the full panel. The caller is responsible for extracting the right data before passing it in. This keeps function signatures honest and avoids scattering `df['Close']` extraction logic throughout every function.

---

## Project Structure

```
Financial-Analysis/
│
├── dev.py                  # Development entry point
├── run_updates.py          # Data ingestion and incremental update pipeline
│
├── src/
|   ├── __init__.py
│   ├── config_loader.py
│   ├── data_getter.py
│   ├── features.py
│   ├── metrics.py
│   ├── models.py
│   ├── paths.py
│   ├── portfolio.py
│   ├── utils.py
│   └── visualisation.py
|
├── logs/
│
├── watchlist/
│   ├── crypto.csv
│   ├── equities.csv
│   ├── macro.csv
│   └── ...
│
└── data/
    ├── crypto_data.parquet
    ├── equities_data.parquet
    ├── macro_data.parquet
    └── ...
```

---

## Root Files

### `dev.py`
Development entry point. Used for testing functions, running analysis, and producing charts during development. Not a production script — imports from `src/` and exercises whatever is currently being worked on.

```python
if __name__ == '__main__':
    vis.price_chart(crypto_data['BTC'], 'BTC')
```

Note: chart calls must be inside `if __name__ == '__main__'` on Windows due to `lightweight-charts` spawning a subprocess for the chart window.

### `run_updates.py`
Automated data ingestion pipeline. Iterates through all configured asset categories and assets, determines whether a full fetch or incremental update is needed, merges new data with existing stored data, applies forward-fill rules by category, and saves the updated panel to parquet.

Forward-fill rules applied before saving:
- `crypto` — `ffill(limit=1)` — fills single missing days (weekends not relevant but brief exchange outages)
- `macro` — `ffill()` — no limit, macro series update infrequently and values persist until revised
- `equities` / others — `ffill(limit=4)` — fills up to a trading week of missing data

---

## `src/`

### `paths.py`
Centralised path definitions. All file paths used across the project are defined here as constants, avoiding hardcoded strings scattered through multiple files. Includes data directory paths, watchlist directory, and parquet file paths per category.

```python
CRYPTO_DATA_PARQUET = os.path.join(DATA_DIR, 'crypto_data.parquet')
```

### `config_loader.py`
Loads asset watchlists from the `watchlist/` directory. Returns a dictionary keyed by category, where each value is a dict of assets with their metadata (ticker, source, full name, etc.). Used by `run_updates.py` to drive the data ingestion loop.

### `data_getter.py`
Core data access module. Contains:

**`fetch_data(ticker, source, identifier, start_date)`**
Fetches a single asset from a supported data source. Returns a MultiIndex OHLCV DataFrame with `(identifier, field)` columns. Supported sources:
- `yfinance` — returns full OHLCV (`Open`, `High`, `Low`, `Close`, `Volume`)
- `FRED` — returns `Close` only (single scalar value per date, labelled as `Close` by convention)

Handles MultiIndex flattening from yfinance, empty series guards for FRED, and explicit datetime index casting.

**`load_data(path, start_date, end_date)`**
Reads a category parquet file with session-level in-memory caching. On first call, reads from disk and stores in `_cache`. Subsequent calls return the cached DataFrame sliced to the requested date range. Call `clear_cache()` after running updates to avoid stale data within the same session.

**`get_close(category, identifiers, start_date, end_date)`**
Convenience wrapper — returns a flat DataFrame of Close prices for all (or a specified subset of) assets in a category.

**`build_panel(category, identifiers, start_date, end_date)`**
Returns a MultiIndex sub-panel for a specified list of assets.

### `features.py`
Technical feature engineering functions. Each function accepts either a Close price Series or a full OHLCV DataFrame depending on the fields required, and returns a Series or DataFrame of the computed feature.

Current and planned features include:

| Feature | Input | Description |
|---|---|---|
| `returns` | Close | Simple period returns |
| `log_returns` | Close | Log returns — preferred for statistical modelling |
| `rolling_volatility` | Close | Annualised rolling standard deviation of log returns |
| `sma` / `ema` | Close | Simple and exponential moving averages |


### `metrics.py`
Performance and risk metric functions. Accept Close price Series and return scalar values or Series. Used for evaluating strategies, assets, and portfolios.

Current and planned metrics include:

| Metric | Description |
|---|---|
| `sharpe_ratio` | Annualised excess return per unit of volatility |
| `sortino_ratio` | Sharpe variant penalising only downside volatility |


### `models.py`
Statistical and stochastic models for return simulation and asset pricing.

**Geometric Brownian Motion (GBM)**

GBM is the stochastic process underpinning the Black-Scholes options pricing model. It models the log-price of an asset as a Wiener process with drift:

```
dS = μS dt + σS dW
```

Where:
- `S` — asset price
- `μ` — drift (expected return per unit time, estimated from historical log returns)
- `σ` — volatility (standard deviation of log returns, annualised)
- `dW` — Wiener process increment ~ N(0, dt)

Key assumptions:
- Log returns are normally distributed
- Volatility and drift are constant over the simulation horizon
- No jumps, fat tails, or mean reversion
- Continuous trading, no transaction costs

In practice these assumptions are violated — financial returns exhibit fat tails, volatility clustering (GARCH effects), and occasional jumps — but GBM remains a useful baseline for price path simulation and options pricing. Parameters `μ` and `σ` are estimated from historical data passed into the model.

The discrete-time exact solution (planned — avoids Euler-Maruyama discretisation error):

```python
S(t+dt) = S(t) * exp((μ - 0.5σ²)dt + σ√dt * Z)
```

where `Z ~ N(0,1)`. Currently the model is stubbed; simulation and Monte Carlo are on the roadmap.

### `visualisation.py`
Interactive charting using `lightweight-charts`. Currently provides:

**`price_chart(ohlcv, identifier)`**
Renders an interactive candlestick chart with volume bars for a given asset. Accepts a standard OHLCV DataFrame (capital column names, datetime index) and handles column lowercasing and index reset internally before passing to the chart library.

Chart styling: dark background (`#0f0f0f`), teal/red candle colours (`#26a69a` / `#ef5350`), semi-transparent volume bars.

---

## `watchlist/`

CSV files defining the assets to track, one file per category. Each row defines an asset with columns for its identifier, full name, data source, and source-specific ticker. The config loader reads these at runtime — adding a new asset means adding a row to the relevant watchlist file and running `run_updates.py`.

Example row:
```
Identifier, Full_Name,  Source,    Ticker
BTC,        Bitcoin,    yfinance,  BTC-USD
CPI,        US CPI,     FRED,      CPIAUCSL
```

---

## `data/`

Parquet files, one per category. Not committed to version control (`.gitignore`). Regenerated by running `run_updates.py`. Each file contains a MultiIndex DataFrame with `(Asset, Field)` columns and a `Date` datetime index.

---

## To-Do & Roadmap

### Simulation
- [ ] **Monte Carlo simulation** — run N price path simulations using GBM, plot fan chart of percentile paths, compute probability of reaching a price target or falling below a threshold
- [ ] **Jump-diffusion model (Merton)** — extend GBM with a Poisson jump process to better capture fat tails and sudden price dislocations
- [ ] **Heston stochastic volatility model** — model volatility as a mean-reverting process correlated with returns, addressing GBM's constant-volatility assumption

### Asset Pricing & Prediction
- [ ] **CAPM** — compute alpha and beta relative to configurable benchmarks (SPY, BTC etc.)
- [ ] **Fama-French factor model** — decompose returns into market, size, and value factors
- [ ] **GARCH(1,1)** — model volatility clustering for more realistic risk estimates and VaR
- [ ] **VAR (Vector Autoregression)** — model interdependencies between macro variables and asset returns
- [ ] **Cointegration testing** — identify long-run equilibrium relationships between asset pairs (pairs trading foundation)

### Features & Indicators
- [x] **RSI** — Relative Strength Index; momentum oscillator bounded 0–100, flags overbought (>70) and oversold (<30) conditions
- [x] **MACD** — Moving Average Convergence Divergence; difference between fast and slow EMAs with a signal line, used for trend and momentum signals
- [ ] **ATR** — Average True Range; volatility measure using High/Low/Close, useful for position sizing and stop placement
- [ ] **Bollinger Bands** — upper/lower bands at N standard deviations from a rolling mean; identifies volatility expansion and mean-reversion setups
- [ ] **OBV** — On-Balance Volume; cumulative volume-price momentum indicator
- [ ] **Ichimoku Cloud** — trend, momentum, and support/resistance in one indicator
- [ ] **Volume profile** — price levels with highest traded volume
- [ ] **Regime detection** — Hidden Markov Model to identify bull/bear/neutral market regimes
- [ ] **Realised vs implied volatility spread** — compare historical vol to options-implied vol where available
- [ ] **Macro factor overlays** — correlate asset performance with yield curve slope, DXY, credit spreads

### Metrics
- [x] **Max drawdown** — largest peak-to-trough decline in a return series
- [ ] **Calmar ratio** — annualised return divided by maximum drawdown
- [ ] **Value at Risk (VaR)** — estimated loss at a given confidence level; both parametric (assumes normality) and historical (empirical distribution) methods
- [ ] **Conditional VaR (CVaR)** — expected loss beyond the VaR threshold; more conservative and coherent risk measure than VaR alone
- [ ] **Beta** — sensitivity of asset returns to a benchmark return series
- [ ] **Alpha** — excess return above what beta-adjusted benchmark exposure would predict
- [ ] **Correlation matrix** — pairwise correlation across a panel of assets

### Multi-Asset Analysis & Portfolio Construction

A basket of assets can be analysed from two perspectives — historical performance and forward-looking simulation — with a shared portfolio construction layer sitting between them.

**Historical Analysis**
- [x] **Portfolio returns** — compute weighted return series for a configurable basket of assets with user-defined weights
- [ ] **Rolling correlation heatmaps** — track how pairwise correlations between assets evolve over time; identify diversification breakdown during stress periods
- [ ] **Contribution analysis** — decompose portfolio return and risk into per-asset contributions, identifying which positions are driving performance or adding unnecessary volatility
- [ ] **Drawdown analysis** — detailed drawdown periods, duration, and recovery time at both the asset and portfolio level; compare individual asset drawdowns against the portfolio drawdown to assess diversification benefit
- [ ] **Historical stress testing** — replay the portfolio through specific historical periods (e.g. COVID crash, 2022 crypto bear, GFC) using actual weights to measure realised losses

**Portfolio Construction**
- [ ] **Efficient frontier** — mean-variance optimisation across a configurable asset universe; plot the set of portfolios that maximise return for a given level of risk, and identify the maximum Sharpe ratio and minimum variance portfolios
- [ ] **Risk parity** — weight assets by equal risk contribution rather than equal capital; reduces concentration in high-volatility assets without requiring return forecasts
- [ ] **Minimum correlation portfolio** — weight assets to minimise average pairwise correlation, maximising diversification benefit
- [ ] **Configurable weighting schemes** — equal weight, market cap weight, custom manual weights; rebalancing on fixed schedules or threshold drift

**Forward-Looking Simulation (GBM-based)**
- [ ] **Correlated multi-asset GBM** — simulate joint price paths for a basket of assets using a multivariate GBM parameterised by the historical covariance matrix (Cholesky decomposition to preserve cross-asset correlation structure); single-asset GBM ignores correlations entirely, which understates diversification benefit and overstates portfolio risk
- [ ] **Portfolio Monte Carlo** — apply a weight vector to N simulated multi-asset path sets, producing a distribution of simulated portfolio values at a target horizon; output percentile fan chart (5th, 25th, 50th, 75th, 95th) and probability of ruin / target attainment
- [ ] **Weight sensitivity analysis** — run Monte Carlo across a grid of weight combinations to identify which allocations produce the best risk-adjusted simulated outcomes
- [ ] **Rebalancing simulation** — compare buy-and-hold vs periodic rebalancing strategies across simulated paths, measuring the volatility drag and rebalancing premium

### Infrastructure
- [ ] **CLI** — command-line interface for running updates, querying data, and triggering analysis without editing `dev.py`
- [ ] **Backtesting engine** — event-driven or vectorised backtester with transaction cost modelling
- [ ] **Alerting** — price/indicator threshold alerts via email or Telegram
- [x] **Scheduled updates** — cron job or task scheduler integration for daily data updates

### Charting
- [x] **Indicator overlays** — plot SMA, EMA, Bollinger Bands directly on the price chart
- [x] **Multi-pane charts** — RSI, MACD, and volume in separate synchronised panes
- [ ] **Multi-asset comparison** — normalised price performance of multiple assets on one chart
- [ ] **Drawdown chart** — visualise underwater equity curve below a rolling high watermark
- [x] **Configurable styling** — pass chart style options rather than hardcoding colours

---

## Dependencies

```
yfinance
fredapi
pandas
pyarrow          # parquet read/write backend
python-dotenv
lightweight-charts
```

Install with:
```bash
pip install yfinance fredapi pandas pyarrow python-dotenv lightweight-charts
```

A FRED API key is required for macro data. Register free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) and set it as an environment variable:

```bash
FRED_API_KEY=your_key_here
```

---

## Disclaimer

This project is for personal research and educational purposes only. Nothing in this repository constitutes financial advice. All models, metrics, and simulations involve assumptions that may not hold in practice. Past performance and simulated results do not predict future returns.
