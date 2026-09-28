import unittest

from src.analyzer import calculate_ratios, derive, finish_periods


class AnalyzerTest(unittest.TestCase):
    def test_derived_cashflow_and_debt(self):
        values = derive({
            "ShortTermBorrowings": 10,
            "LongTermBorrowings": 20,
            "Bonds": 5,
            "LeaseLiabilitiesCurrent": None,
            "LeaseLiabilitiesNoncurrent": None,
            "Cash": 12,
            "CurrentAssets": 80,
            "Inventory": 20,
            "PurchasePPE": -9,
            "PurchaseIntangibles": -1,
            "CFO": 30,
            "OperatingIncome": 25,
            "DepreciationAmortization": 5,
        })
        self.assertEqual(values["InterestBearingDebt"], 35)
        self.assertEqual(values["NetDebt"], 23)
        self.assertEqual(values["QuickAssets"], 60)
        self.assertEqual(values["CAPEX"], 10)
        self.assertEqual(values["FCF"], 20)
        self.assertEqual(values["EBITDA"], 30)

    def test_ratios_use_average_balance(self):
        current = derive({"Revenue": 200, "NetIncome": 20, "Assets": 120, "Equity": 60})
        previous = derive({"Revenue": 160, "Assets": 80, "Equity": 40})
        ratios = calculate_ratios(current, previous, "11011")
        self.assertEqual(ratios["roa"], 20.0)
        self.assertEqual(ratios["roe"], 40.0)
        self.assertEqual(ratios["assetTurnover"], 2.0)
        self.assertEqual(ratios["revenueGrowth"], 25.0)

    def test_periods_are_sorted_and_ccc_is_calculated(self):
        template = {
            "category": "annual", "reportCode": "11011", "sortOrder": 4,
            "values": {"Revenue": 100, "COGS": 50, "Receivables": 10, "Inventory": 20, "Payables": 5},
        }
        result = finish_periods([{**template, "year": 2024}, {**template, "year": 2023}])
        self.assertEqual([p["year"] for p in result], [2023, 2024])
        self.assertIsNotNone(result[-1]["ratios"]["ccc"])


if __name__ == "__main__":
    unittest.main()
