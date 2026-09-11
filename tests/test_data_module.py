from unittest.mock import patch

import pandas as pd

from core import data_module


def valid_frame(rows=20):
    return pd.DataFrame(
        {
            "Open": [10] * rows,
            "High": [12] * rows,
            "Low": [9] * rows,
            "Close": [11] * rows,
            "Volume": [1000] * rows,
        }
    )


def test_validate_stock_data_covers_empty_short_missing_nan_and_valid():
    assert data_module.validate_stock_data(pd.DataFrame()) == (False, "Data kosong")
    assert data_module.validate_stock_data(valid_frame(2), min_rows=20) == (False, "Data tidak cukup (2/20)")

    missing = valid_frame().drop(columns=["Volume"])
    assert data_module.validate_stock_data(missing)[0] is False
    assert "Kolom hilang" in data_module.validate_stock_data(missing)[1]

    with_nan = valid_frame()
    with_nan.loc[0, "Close"] = float("nan")
    assert data_module.validate_stock_data(with_nan) == (False, "Ada data kosong di kolom penting")
    assert data_module.validate_stock_data(valid_frame()) == (True, "Valid")


def test_sector_lookup_helpers_return_known_and_fallback_values():
    all_sectors = data_module.get_all_sectors()
    known = data_module.get_sector_tickers(all_sectors[0])

    assert all_sectors == sorted(all_sectors)
    assert known
    assert data_module.get_sector_tickers("missing") == []
    assert data_module.get_ticker_sector("UNKNOWN", {}) == "Other"


def test_download_single_stock_returns_none_for_empty_mock_response():
    with patch.object(data_module.yf, "download", return_value=pd.DataFrame()) as download:
        result = data_module.download_single_stock("ABC.JK", period="1d")

    assert result is None
    download.assert_called_once()
    assert download.call_args.kwargs["period"] == "1d"


def test_download_batch_dict_handles_single_ticker_mock_response():
    frame = valid_frame()
    with patch.object(data_module.yf, "download", return_value=frame) as download:
        result = data_module.download_batch_dict(["ABC.JK"], period="5d")

    assert list(result) == ["ABC.JK"]
    pd.testing.assert_frame_equal(result["ABC.JK"], frame)
    assert download.call_args.kwargs["tickers"] == ["ABC.JK"]