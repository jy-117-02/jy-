from __future__ import annotations

import re
from typing import Any


def amount(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    text = str(value).strip().replace(",", "")
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    try:
        number = int(text)
        return -number if negative else number
    except ValueError:
        return None


def _label(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def choose_value(row: dict[str, Any], report_code: str) -> int | None:
    statement = row.get("sj_div", "")
    if report_code != "11011" and statement in {"IS", "CIS", "CF"}:
        cumulative = amount(row.get("thstrm_add_amount"))
        if cumulative is not None:
            return cumulative
    return amount(row.get("thstrm_amount"))


def extract_values(rows: list[dict[str, Any]], metric_config: dict[str, Any], report_code: str) -> dict[str, int | None]:
    result: dict[str, int | None] = {}
    for metric, spec in metric_config.items():
        statement = spec.get("statement")
        candidates = [row for row in rows if row.get("sj_div") in {statement, "CIS" if statement == "IS" else statement}]
        selected = None
        for account_id in spec.get("account_ids", []):
            selected = next((row for row in candidates if row.get("account_id") == account_id), None)
            if selected:
                break
        if not selected:
            names = {_label(name) for name in spec.get("names", [])}
            selected = next((row for row in candidates if _label(row.get("account_nm", "")) in names), None)
        result[metric] = choose_value(selected, report_code) if selected else None
    return result


def safe_sum(*values: int | None) -> int | None:
    valid = [value for value in values if value is not None]
    return sum(valid) if valid else None


def ratio(numerator: float | int | None, denominator: float | int | None, scale: float = 100.0) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(float(numerator) / float(denominator) * scale, 2)


def average(current: int | None, previous: int | None) -> float | None:
    if current is None:
        return None
    return current if previous is None else (current + previous) / 2


def derive(values: dict[str, int | None]) -> dict[str, int | None]:
    result = dict(values)
    result["InterestBearingDebt"] = safe_sum(
        values.get("ShortTermBorrowings"), values.get("LongTermBorrowings"), values.get("Bonds"),
        values.get("LeaseLiabilitiesCurrent"), values.get("LeaseLiabilitiesNoncurrent"),
    )
    result["QuickAssets"] = None if values.get("CurrentAssets") is None else values["CurrentAssets"] - (values.get("Inventory") or 0)
    debt, cash = result.get("InterestBearingDebt"), values.get("Cash")
    result["NetDebt"] = None if debt is None or cash is None else debt - cash
    capex_parts = [values.get("PurchasePPE"), values.get("PurchaseIntangibles")]
    capex_valid = [abs(value) for value in capex_parts if value is not None]
    result["CAPEX"] = sum(capex_valid) if capex_valid else None
    result["FCF"] = None if values.get("CFO") is None or result["CAPEX"] is None else values["CFO"] - result["CAPEX"]
    da = values.get("DepreciationAmortization")
    result["EBITDA"] = None if values.get("OperatingIncome") is None or da is None else values["OperatingIncome"] + abs(da)
    return result


ANNUALIZE = {"11011": 1.0, "11012": 2.0, "11013": 4.0, "11014": 4.0 / 3.0}


def calculate_ratios(current: dict[str, int | None], previous: dict[str, int | None] | None, report_code: str) -> dict[str, float | None]:
    previous = previous or {}
    factor = ANNUALIZE[report_code]
    revenue = current.get("Revenue")
    cogs = current.get("COGS")
    net_income = current.get("NetIncome")
    pretax = current.get("PretaxIncome")
    tax_rate = 0.25
    if pretax and net_income is not None and pretax > 0:
        observed = (pretax - net_income) / pretax
        if 0 <= observed <= 0.5:
            tax_rate = observed
    nopat = None if current.get("OperatingIncome") is None else current["OperatingIncome"] * (1 - tax_rate)
    invested = None
    if current.get("Equity") is not None and current.get("InterestBearingDebt") is not None and current.get("Cash") is not None:
        invested = current["Equity"] + current["InterestBearingDebt"] - current["Cash"]
    previous_invested = None
    if previous.get("Equity") is not None and previous.get("InterestBearingDebt") is not None and previous.get("Cash") is not None:
        previous_invested = previous["Equity"] + previous["InterestBearingDebt"] - previous["Cash"]
    avg_invested = average(invested, previous_invested)
    avg_assets = average(current.get("Assets"), previous.get("Assets"))
    avg_equity = average(current.get("Equity"), previous.get("Equity"))
    avg_receivables = average(current.get("Receivables"), previous.get("Receivables"))
    avg_inventory = average(current.get("Inventory"), previous.get("Inventory"))
    avg_payables = average(current.get("Payables"), previous.get("Payables"))
    annual_revenue = None if revenue is None else revenue * factor
    annual_cogs = None if cogs is None else abs(cogs) * factor
    return {
        "grossMargin": ratio(current.get("GrossProfit"), revenue),
        "operatingMargin": ratio(current.get("OperatingIncome"), revenue),
        "netMargin": ratio(net_income, revenue),
        "ebitdaMargin": ratio(current.get("EBITDA"), revenue),
        "roa": ratio(None if net_income is None else net_income * factor, avg_assets),
        "roe": ratio(None if net_income is None else net_income * factor, avg_equity),
        "roic": ratio(None if nopat is None else nopat * factor, avg_invested),
        "currentRatio": ratio(current.get("CurrentAssets"), current.get("CurrentLiabilities")),
        "quickRatio": ratio(current.get("QuickAssets"), current.get("CurrentLiabilities")),
        "debtRatio": ratio(current.get("Liabilities"), current.get("Equity")),
        "equityRatio": ratio(current.get("Equity"), current.get("Assets")),
        "debtDependency": ratio(current.get("InterestBearingDebt"), current.get("Assets")),
        "interestCoverage": ratio(current.get("OperatingIncome"), None if current.get("InterestExpense") is None else abs(current["InterestExpense"]), 1.0),
        "netDebtToEbitda": ratio(current.get("NetDebt"), None if current.get("EBITDA") is None else current["EBITDA"] * factor, 1.0),
        "assetTurnover": ratio(annual_revenue, avg_assets, 1.0),
        "dso": ratio(avg_receivables, annual_revenue, 365.0),
        "dio": ratio(avg_inventory, annual_cogs, 365.0),
        "dpo": ratio(avg_payables, annual_cogs, 365.0),
        "revenueGrowth": ratio(None if revenue is None or previous.get("Revenue") is None else revenue - previous["Revenue"], previous.get("Revenue")),
        "cfoToNetIncome": ratio(current.get("CFO"), net_income, 1.0),
    }


def finish_periods(periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prior_by_code: dict[str, dict[str, int | None]] = {}
    for period in sorted(periods, key=lambda item: (item["year"], item["sortOrder"])):
        values = derive(period["values"])
        code = period["reportCode"]
        ratios = calculate_ratios(values, prior_by_code.get(code), code)
        if ratios.get("dso") is not None and ratios.get("dio") is not None and ratios.get("dpo") is not None:
            ratios["ccc"] = round(ratios["dso"] + ratios["dio"] - ratios["dpo"], 2)
        else:
            ratios["ccc"] = None
        period["values"] = values
        period["ratios"] = ratios
        prior_by_code[code] = values
    return sorted(periods, key=lambda item: (item["year"], item["sortOrder"]))
