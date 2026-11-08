"""Portfolio return and risk from a local price table.

Sharpe here is mean daily excess return divided by daily volatility, then
annualized. It is the textbook mean-excess Sharpe, not a CAGR-over-vol ratio.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
import pandas as pd


class MetricsError(ValueError):
    """Prices or weights cannot produce a risk summary."""


@dataclass(frozen=True)
class RiskSummary:
    observations: int
    start: str
    end: str
    total_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    historical_var: float


def read_prices(text: str) -> pd.DataFrame:
    """Read a CSV with a date column and one column per ticker."""
    frame = pd.read_csv(io.StringIO(text.lstrip("\ufeff")))
    lookup = {str(column).strip().lower(): column for column in frame.columns}
    if "date" not in lookup:
        raise MetricsError("Prices CSV needs a date column.")
    frame = frame.rename(columns={lookup["date"]: "date"})
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame = frame.set_index("date").sort_index()
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    prices = frame.apply(pd.to_numeric, errors="raise")
    if prices.shape[1] == 0 or prices.empty:
        raise MetricsError("Prices CSV has no ticker columns.")
    return prices


def price_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple daily returns. Rows with any missing price are dropped."""
    returns = prices.pct_change().dropna(how="any")
    if returns.empty:
        raise MetricsError("Need at least two complete price rows.")
    return returns


def portfolio_returns(asset_returns: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """Weighted daily return. Missing tickers are an error."""
    if not weights:
        raise MetricsError("No holdings to weight.")
    missing = [ticker for ticker in weights if ticker not in asset_returns.columns]
    if missing:
        raise MetricsError("No prices for: " + ", ".join(missing))
    ordered = list(weights)
    values = asset_returns[ordered].to_numpy(dtype=float)
    vector = np.array([weights[ticker] for ticker in ordered], dtype=float)
    series = pd.Series(values @ vector, index=asset_returns.index, name="portfolio")
    if series.isna().any():
        raise MetricsError("Portfolio returns contain missing values.")
    return series


def total_return(returns: pd.Series) -> float:
    return float((1.0 + returns).prod() - 1.0)


def annualized_volatility(returns: pd.Series, trading_days: int) -> float:
    if trading_days <= 0:
        raise MetricsError("trading_days must be positive.")
    return float(returns.std(ddof=1) * np.sqrt(trading_days))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float, trading_days: int) -> float:
    """Annualized mean-excess Sharpe. Zero when daily volatility is zero."""
    daily_vol = float(returns.std(ddof=1))
    if daily_vol == 0.0 or not np.isfinite(daily_vol):
        return 0.0
    excess = returns - (risk_free_rate / trading_days)
    return float(excess.mean() / daily_vol * np.sqrt(trading_days))


def max_drawdown(returns: pd.Series) -> float:
    """Peak-to-trough of cumulative wealth. Zero or negative."""
    wealth = (1.0 + returns).cumprod()
    peak = wealth.cummax()
    drawdown = wealth / peak - 1.0
    return float(drawdown.min())


def historical_var(returns: pd.Series, confidence: float) -> float:
    """One-day historical loss at ``confidence``. Stored as a positive number."""
    if not 0.0 < confidence < 1.0:
        raise MetricsError("var_confidence must be between 0 and 1.")
    cutoff = float(np.percentile(returns.to_numpy(dtype=float), (1.0 - confidence) * 100.0))
    return max(0.0, -cutoff)


def summarize(
    returns: pd.Series,
    *,
    risk_free_rate: float,
    trading_days: int,
    var_confidence: float,
) -> RiskSummary:
    if returns.empty:
        raise MetricsError("No returns to summarize.")
    start = pd.Timestamp(returns.index.min()).date().isoformat()
    end = pd.Timestamp(returns.index.max()).date().isoformat()
    return RiskSummary(
        observations=int(len(returns)),
        start=start,
        end=end,
        total_return=total_return(returns),
        annualized_volatility=annualized_volatility(returns, trading_days),
        sharpe_ratio=sharpe_ratio(returns, risk_free_rate, trading_days),
        max_drawdown=max_drawdown(returns),
        historical_var=historical_var(returns, var_confidence),
    )
