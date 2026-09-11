from core.idx_all_tickers import IDX_TICKERS


NEW_JULY_2026_TICKERS = {"BACH", "EMMI", "JECX", "JELI", "PRDL", "RANS"}


def test_july_2026_idx_tickers_are_present_and_unique():
    assert NEW_JULY_2026_TICKERS.issubset(IDX_TICKERS)
    assert len(IDX_TICKERS) == len(set(IDX_TICKERS))
    assert all(len(ticker) == 4 and ticker.isupper() for ticker in IDX_TICKERS)
