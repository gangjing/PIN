from src.data_loader import load_watchlist_csv, row_to_item, validate_ticker


def test_load_watchlist_skips_disabled():
    items = load_watchlist_csv("config/watchlist.sample.csv")
    assert len(items) == 4
    assert all(item.enabled for item in items)


def test_ticker_validation():
    assert validate_ticker("HK", "1810.HK")
    assert validate_ticker("CN", "002594.SZ")
    assert validate_ticker("US", "TTD")
    assert not validate_ticker("HK", "1810")


def test_google_sheet_style_row_mapping():
    item = row_to_item(
        {
            "Ticker": "HKG:0700",
            "Company Name": "腾讯科技",
            "Shares": "500",
            "Avg Price": "363.401",
            "Action Goal": "Hold Long",
        }
    )
    assert item.market == "HK"
    assert item.ticker == "0700.HK"
    assert item.name == "腾讯科技"
    assert item.type == "holding"
    assert item.quantity == 500
    assert item.cost == 363.401


def test_cn_prefixed_row_mapping_and_sell_target():
    item = row_to_item(
        {
            "Ticker": "SHE:000002",
            "Company Name": "万科 A",
            "Shares": "42700",
            "Avg Price": "10.0977",
            "Action Goal": "Sell at 11",
        }
    )
    assert item.market == "CN"
    assert item.ticker == "000002.SZ"
    assert item.take_profit == 11
