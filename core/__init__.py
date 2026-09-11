"""Core modules for the gtckrz stock analysis application."""

# Keep newly listed IDX tickers in a small, idempotent extension layer instead
# of rewriting the generated/full ticker catalogue. This makes future ticker
# refreshes less likely to overwrite the additions or introduce duplicates.
from .idx_all_tickers import IDX_TICKERS

_NEW_IDX_TICKERS = (
    "BACH",
    "EMMI",
    "JECX",
    "JELI",
    "PRDL",
    "RANS",
)

for _ticker in _NEW_IDX_TICKERS:
    if _ticker not in IDX_TICKERS:
        IDX_TICKERS.append(_ticker)

IDX_TICKERS.sort()

# Avoid leaking the implementation detail into the package namespace.
del _ticker
