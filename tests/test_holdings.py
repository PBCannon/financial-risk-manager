from pathlib import Path

import pytest

from core.holdings import HoldingsError, parse_holdings_csv


def test_percent_weights_normalize_to_one() -> None:
    book = parse_holdings_csv("ticker,weight\nAAPL,40\nMSFT,35\nNVDA,25\n")
    assert book.notice is None
    assert book.as_map() == {"AAPL": 0.40, "MSFT": 0.35, "NVDA": 0.25}


def test_decimal_weights_are_kept() -> None:
    book = parse_holdings_csv("ticker,weight\nAAPL,0.5\nMSFT,0.5\n")
    assert book.as_map()["AAPL"] == pytest.approx(0.5)


def test_percent_sign_allows_a_fractional_percent() -> None:
    book = parse_holdings_csv("ticker,weight\nAAPL,99.3%\nMSFT,0.7%\n")
    assert book.as_map()["MSFT"] == pytest.approx(0.007)


def test_off_total_is_rescaled_and_reported() -> None:
    book = parse_holdings_csv("ticker,weight\nAAPL,20\nMSFT,20\n")
    assert book.notice is not None
    assert sum(book.as_map().values()) == pytest.approx(1.0)
    assert book.as_map()["AAPL"] == pytest.approx(0.5)


def test_duplicate_ticker_is_rejected() -> None:
    with pytest.raises(HoldingsError, match="Duplicate ticker"):
        parse_holdings_csv("ticker,weight\nAAPL,50\nAAPL,50\n")


def test_mixed_scales_are_rejected() -> None:
    with pytest.raises(HoldingsError, match="Mixed percent and decimal"):
        parse_holdings_csv("ticker,weight\nAAPL,0.5\nMSFT,50\n")


def test_wrong_header_is_rejected() -> None:
    with pytest.raises(HoldingsError, match="Expected columns"):
        parse_holdings_csv("symbol,shares\nAAPL,10\n")


def test_example_file_parses() -> None:
    text = Path("examples/holdings.csv").read_text(encoding="utf-8")
    book = parse_holdings_csv(text)
    assert set(book.as_map()) == {"AAPL", "MSFT", "NVDA"}
    assert sum(book.as_map().values()) == pytest.approx(1.0)
