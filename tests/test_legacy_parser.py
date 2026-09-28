import unittest

from src.legacy_parser import parse_legacy_documents


class LegacyParserTest(unittest.TestCase):
    def test_extracts_statement_rows(self):
        config = {
            "Assets": {"statement": "BS", "names": ["자산총계"]},
            "Liabilities": {"statement": "BS", "names": ["부채총계"]},
            "Equity": {"statement": "BS", "names": ["자본총계"]},
            "Revenue": {"statement": "IS", "names": ["매출액"]},
            "OperatingIncome": {"statement": "IS", "names": ["영업이익"]},
            "NetIncome": {"statement": "IS", "names": ["당기순이익"]},
            "CFO": {"statement": "CF", "names": ["영업활동현금흐름"]},
            "CFI": {"statement": "CF", "names": ["투자활동현금흐름"]},
        }
        html = """<table>
          <tr><td>자산총계</td><td>1,000</td></tr><tr><td>부채총계</td><td>400</td></tr><tr><td>자본총계</td><td>600</td></tr>
          <tr><td>매출액</td><td>800</td></tr><tr><td>영업이익</td><td>100</td></tr><tr><td>당기순이익</td><td>80</td></tr>
          <tr><td>영업활동현금흐름</td><td>90</td></tr><tr><td>투자활동현금흐름</td><td>(50)</td></tr>
        </table>"""
        rows = parse_legacy_documents([("test.htm", html)], config)
        by_name = {row["account_nm"]: row for row in rows}
        self.assertEqual(by_name["자산총계"]["thstrm_amount"], "1000")
        self.assertEqual(by_name["투자활동현금흐름"]["thstrm_amount"], "-50")


if __name__ == "__main__":
    unittest.main()
