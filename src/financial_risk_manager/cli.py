"""Command-line entry point. Reads local CSV files and prints a risk summary."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.config import ConfigError, load_settings
from core.holdings import HoldingsError, parse_holdings_csv
from core.metrics import MetricsError, portfolio_returns, price_returns, read_prices, summarize
from financial_risk_manager import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="frm",
        description="Summarize portfolio risk from a holdings CSV and a local prices CSV.",
    )
    parser.add_argument("--holdings", required=True, type=Path, help="ticker,weight CSV")
    parser.add_argument("--prices", required=True, type=Path, help="date plus one column per ticker")
    parser.add_argument("--config", type=Path, default=None, help="defaults to config.yaml")
    parser.add_argument("--version", action="version", version=f"frm {__version__}")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config)
        book = parse_holdings_csv(args.holdings.read_text(encoding="utf-8"))
        prices = read_prices(args.prices.read_text(encoding="utf-8"))
        returns = portfolio_returns(price_returns(prices), book.as_map())
        summary = summarize(
            returns,
            risk_free_rate=settings.risk_free_rate,
            trading_days=settings.trading_days,
            var_confidence=settings.var_confidence,
        )
    except (OSError, ConfigError, HoldingsError, MetricsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if book.notice:
        print(book.notice)
    print(_render(book.holdings, summary, settings.var_confidence))
    return 0


def _render(holdings, summary, confidence: float) -> str:
    lines = ["Holdings"]
    for row in holdings:
        lines.append(f"  {row.ticker:<8} {row.weight * 100:6.2f}%")
    percent = f"{confidence * 100:.0f}"
    lines.extend(
        [
            "",
            f"Window: {summary.start} to {summary.end} ({summary.observations} days)",
            f"Total return:           {summary.total_return * 100:8.2f}%",
            f"Annualized volatility:  {summary.annualized_volatility * 100:8.2f}%",
            f"Sharpe (mean excess):   {summary.sharpe_ratio:8.2f}",
            f"Max drawdown:           {summary.max_drawdown * 100:8.2f}%",
            f"{percent}% historical VaR:    {summary.historical_var * 100:8.2f}%",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
