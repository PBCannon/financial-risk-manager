# Roadmap

Version 0.1 is the public baseline: a local CLI, a holdings parser, and five risk figures with tests.

## 0.2 — Benchmark comparison

- Optional benchmark column in the price file.
- Beta, tracking error, and correlation against that series.
- The same numbers printed in the CLI summary and covered by unit tests.

## 0.3 — Clearer outputs

- Write the summary to a CSV as well as the terminal.
- Flag a holdings file whose weights were rescaled, which 0.1 already prints.
- Reject a price file that ends before the holdings need it, with the missing ticker named.

## 0.4 — What-if weights

- A second holdings file compared with the current book on the same price window.
- Side-by-side return, volatility, drawdown, and VaR.
- Still no network calls and no saved client books.

## Staying out of this public repository

Accounts, hosted delivery, payment, white-label reports, and any file of a real client's holdings. Those belong in a private product, not here. Price history, when a later version can download it, will use a key supplied at runtime and documented in `.env.example` only as a blank name.
