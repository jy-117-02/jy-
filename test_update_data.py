from src.update_data import amount, calculate_ratios


def test_amount():
    assert amount("1,234") == 1234
    assert amount("-") is None


def test_ratios():
    ratios = calculate_ratios({"OperatingIncome": 20, "Revenue": 100, "NetIncome": 10, "Equity": 50, "Assets": 200, "Liabilities": 150, "CurrentAssets": 80, "CurrentLiabilities": 40})
    assert ratios["operatingMargin"] == 20.0
    assert ratios["debtRatio"] == 300.0
    assert ratios["currentRatio"] == 200.0

