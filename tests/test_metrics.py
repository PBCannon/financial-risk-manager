import numpy as np
import pandas as pd
import pytest

from core.metrics import (
    historical_var,
    max_drawdown,
    portfolio_returns,
    price_returns,
    read_prices,
    sharpe_ratio,
    summarize,
)


def test_max_drawdown_on_a_known_path() -> None:
    # Wealth goes 1.00 -> 1.10 -> 0.99. Drawdown is 0.99 / 1.10 - 1.
    returns = pd.Series([0.10, -0.10], index=pd.bdate_range("2024-01-02", periods=2))
    assert max_drawdown(returns) == pytest.approx(0.99 / 1.10 - 1.0)


def test_flat_loss_var_is_that_loss() -> None:
    returns = pd.Series([-0.01] * 8, index=pd.bdate_range("2024-01-02", periods=8))
    assert historical_var(returns, 0.95) == pytest.approx(0.01)


def test_zero_volatility_sharpe_is_zero() -> None:
    returns = pd.Series([0.0, 0.0, 0.0], index=pd.bdate_range("2024-01-02", periods=3))
    assert sharpe_ratio(returns, risk_free_rate=0.04, trading_days=252) == 0.0


def test_portfolio_return_is_the_weighted_sum() -> None:
    index = pd.bdate_range("2024-01-02", periods=2)
    asset_returns = pd.DataFrame({"AAA": [0.10, 0.0], "BBB": [0.0, 0.20]}, index=index)
    portfolio = portfolio_returns(asset_returns, {"AAA": 0.25, "BBB": 0.75})
    assert portfolio.iloc[0] == pytest.approx(0.025)
    assert portfolio.iloc[1] == pytest.approx(0.15)


def test_missing_price_column_is_an_error() -> None:
    index = pd.bdate_range("2024-01-02", periods=2)
    asset_returns = pd.DataFrame({"AAA": [0.01, 0.02]}, index=index)
    with pytest.raises(ValueError, match="No prices for: BBB"):
        portfolio_returns(asset_returns, {"BBB": 1.0})


def test_summary_uses_the_documented_volatility() -> None:
    index = pd.bdate_range("2024-01-02", periods=6)
    returns = pd.Series([0.01, -0.02, 0.015, 0.0, -0.005, 0.012], index=index)
    summary = summarize(returns, risk_free_rate=0.0, trading_days=252, var_confidence=0.95)
    expected_vol = float(returns.std(ddof=1) * np.sqrt(252))
    assert summary.annualized_volatility == pytest.approx(expected_vol)
    assert summary.total_return == pytest.approx(float((1.0 + returns).prod() - 1.0))
    assert summary.observations == 6


def test_price_csv_drops_the_first_return_row() -> None:
    text = "date,AAA,BBB\n2024-01-02,100,50\n2024-01-03,110,50\n2024-01-04,110,55\n"
    returns = price_returns(read_prices(text))
    assert len(returns) == 2
    assert returns["AAA"].iloc[0] == pytest.approx(0.10)
    assert returns["BBB"].iloc[1] == pytest.approx(0.10)
