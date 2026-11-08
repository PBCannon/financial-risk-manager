"""Long-only holdings file: ticker and weight columns, weights sum to 1."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

_TICKER = re.compile(r"[A-Z][A-Z0-9.\-]{0,9}")


class HoldingsError(ValueError):
    """The holdings file cannot be used as a long-only book."""


@dataclass(frozen=True)
class Holding:
    ticker: str
    weight: float


@dataclass(frozen=True)
class HoldingsBook:
    """Normalized book. ``notice`` is set when the file was rescaled to 100%."""

    holdings: tuple[Holding, ...]
    notice: str | None = None

    def as_map(self) -> dict[str, float]:
        return {row.ticker: row.weight for row in self.holdings}


def parse_holdings_csv(text: str) -> HoldingsBook:
    """Parse ``ticker,weight`` text into weights that sum to 1.

    A ``%`` sign on every weight, or any weight above 1, means percents.
    Weights that are all at most 1 stay decimals. Mixing 0.5 with 50 is an
    error. The book is then rescaled so the weights sum to 1.
    """
    raw_rows = _read_rows(text)
    parsed = [_parse_row(ticker, weight) for ticker, weight in raw_rows]
    _reject_duplicates(parsed)
    scaled = _to_fractions(parsed)
    total = sum(weight for _, weight in scaled)
    if total <= 0:
        raise HoldingsError("Weights must sum to a positive number.")
    notice = None
    if abs(total - 1.0) > 0.005:
        notice = f"Weights summed to {total * 100:.2f}% and were rescaled to 100%."
    holdings = tuple(
        Holding(ticker, weight / total) for ticker, weight in scaled
    )
    return HoldingsBook(holdings, notice)


def _read_rows(text: str) -> list[tuple[str, str]]:
    sample = text.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(sample))
    if not reader.fieldnames:
        raise HoldingsError("Expected columns: ticker, weight")
    fields = [(name or "").strip().lower() for name in reader.fieldnames]
    if fields[:2] != ["ticker", "weight"] or len(fields) != 2:
        raise HoldingsError("Expected columns: ticker, weight")
    rows: list[tuple[str, str]] = []
    for line in reader:
        values = {(key or "").strip().lower(): (value or "").strip() for key, value in line.items()}
        ticker = values.get("ticker", "")
        weight = values.get("weight", "")
        if not ticker and not weight:
            continue
        rows.append((ticker, weight))
    if not rows:
        raise HoldingsError("Holdings file has no rows.")
    return rows


def _parse_row(ticker: str, weight: str) -> tuple[str, float, bool]:
    symbol = ticker.strip().upper()
    if not _TICKER.fullmatch(symbol):
        raise HoldingsError(f"Invalid ticker: {ticker!r}")
    token = weight.strip().replace(",", "")
    percent = token.endswith("%")
    number_text = token[:-1].strip() if percent else token
    if not number_text:
        raise HoldingsError(f"Invalid weight for {symbol}: {weight!r}")
    try:
        number = float(number_text)
    except ValueError as exc:
        raise HoldingsError(f"Invalid weight for {symbol}: {weight!r}") from exc
    if number < 0:
        raise HoldingsError(f"Negative weight for {symbol}: {weight}")
    return symbol, number, percent


def _reject_duplicates(rows: list[tuple[str, float, bool]]) -> None:
    seen: set[str] = set()
    for ticker, _, _ in rows:
        if ticker in seen:
            raise HoldingsError(f"Duplicate ticker: {ticker}")
        seen.add(ticker)


def _to_fractions(rows: list[tuple[str, float, bool]]) -> list[tuple[str, float]]:
    percent_flags = [flag for _, _, flag in rows]
    numbers = [number for _, number, _ in rows]
    if any(percent_flags) and not all(percent_flags):
        raise HoldingsError("Use a percent sign on every weight, or on none.")
    if all(percent_flags) or any(number > 1 for number in numbers):
        if any(number < 1 for number in numbers) and not all(percent_flags):
            raise HoldingsError("Mixed percent and decimal weights.")
        scale = 100.0
    else:
        scale = 1.0
    return [(ticker, number / scale) for ticker, number, _ in rows]
