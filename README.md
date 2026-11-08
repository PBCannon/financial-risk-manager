# Financial Risk Manager

Command-line portfolio risk summary. Give it a holdings file and a local price file. It prints the book weights, total return, annualized volatility, mean-excess Sharpe, max drawdown, and one-day historical VaR.

Prices stay in a CSV you already have. The tool does not call a market-data API and it does not store client books.

This is a public reference project under the MIT license. It is not a source drop of a private advisory product.

## Layout

```
src/financial_risk_manager/   CLI entry point (argparse)
core/                         holdings parser, risk math, config loader
tests/                        unit tests, including a secret scan
config.yaml                   risk-free rate, trading days, VaR confidence
.env.example                  optional environment overrides
examples/                     sample holdings and synthetic prices
```

## Run

Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
frm --holdings examples/holdings.csv --prices examples/prices.csv
```

Without installing the script:

```bash
PYTHONPATH="src:." python -m financial_risk_manager \
  --holdings examples/holdings.csv \
  --prices examples/prices.csv
```

## Configuration

`config.yaml` holds the risk-free rate, the trading-day count, and the VaR confidence. Copy `.env.example` to `.env` to override the rate locally. `.env` is gitignored. `FRM_RISK_FREE_RATE=0.03` replaces the rate in `config.yaml`.

## Holdings file

Header must be `ticker,weight`. Weights may be percents (`40` or `40%`) or decimals (`0.40`). A percent sign on every row, or any weight above 1, means percents. Mixing `0.5` with `50` is rejected. The book is rescaled to 100%.

## Prices file

Header is `date` plus one column per ticker. The sample file in `examples/prices.csv` is a synthetic random walk, not market history.

## Tests

```bash
pytest
```

Sharpe in this repository is mean daily excess return over daily volatility, annualized with the trading-day count in `config.yaml`. Historical VaR is the positive one-day loss at the configured percentile.

## What is not in this repository

No API keys, no `.env`, no saved client portfolios, and no private product documents. Sample prices are synthetic.

## Roadmap

See `ROADMAP.md`.
