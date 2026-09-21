from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
CORP_CODE = "00126380"
COMPANY = "삼성전자"
REPORT_CODE = "11011"  # 사업보고서
ROOT = Path(__file__).resolve().parents[1]


def amount(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        return int(str(value).replace(",", "").strip())
    except ValueError:
        return None


def fetch_year(api_key: str, year: int, fs_div: str = "CFS") -> list[dict[str, Any]]:
    import requests

    params = {
        "crtfc_key": api_key,
        "corp_code": CORP_CODE,
        "bsns_year": str(year),
        "reprt_code": REPORT_CODE,
        "fs_div": fs_div,
    }
    response = requests.get(BASE_URL, params=params, timeout=40)
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "000":
        raise RuntimeError(f"OpenDART {year}: {payload.get('status')} {payload.get('message')}")
    return payload.get("list", [])


def select_metric(rows: list[dict[str, Any]], aliases: list[str]) -> int | None:
    for alias in aliases:
        for row in rows:
            if row.get("account_id") == alias or row.get("account_nm") == alias:
                value = amount(row.get("thstrm_amount"))
                if value is not None:
                    return value
    return None


def ratio(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or not denominator:
        return None
    return round(numerator / denominator * 100, 2)


def calculate_ratios(values: dict[str, int | None]) -> dict[str, float | None]:
    return {
        "operatingMargin": ratio(values.get("OperatingIncome"), values.get("Revenue")),
        "netMargin": ratio(values.get("NetIncome"), values.get("Revenue")),
        "roe": ratio(values.get("NetIncome"), values.get("Equity")),
        "roa": ratio(values.get("NetIncome"), values.get("Assets")),
        "debtRatio": ratio(values.get("Liabilities"), values.get("Equity")),
        "currentRatio": ratio(values.get("CurrentAssets"), values.get("CurrentLiabilities")),
    }


def build(api_key: str, start_year: int, end_year: int) -> dict[str, Any]:
    metric_map = json.loads((ROOT / "config/metrics.json").read_text(encoding="utf-8"))
    periods = []
    errors = []
    for year in range(start_year, end_year + 1):
        try:
            rows = fetch_year(api_key, year)
            values = {name: select_metric(rows, aliases) for name, aliases in metric_map.items()}
            periods.append({"year": year, "values": values, "ratios": calculate_ratios(values)})
        except Exception as exc:
            errors.append({"year": year, "error": str(exc)})
    if not periods:
        raise RuntimeError(f"수집된 연도가 없습니다: {errors}")
    return {
        "company": COMPANY,
        "corpCode": CORP_CODE,
        "basis": "연결재무제표(CFS), 사업보고서(11011)",
        "currency": "KRW",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "periods": periods,
        "errors": errors,
    }


def write_outputs(data: dict[str, Any]) -> None:
    docs_data = ROOT / "docs/data"
    raw_data = ROOT / "data"
    docs_data.mkdir(parents=True, exist_ok=True)
    raw_data.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    (docs_data / "financials.json").write_text(text, encoding="utf-8")
    (raw_data / "financials.json").write_text(text, encoding="utf-8")
    fields = ["year", *next(iter(data["periods"]))["values"].keys(), *next(iter(data["periods"]))["ratios"].keys()]
    for target in [docs_data / "financials.csv", raw_data / "financials.csv"]:
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for period in data["periods"]:
                writer.writerow({"year": period["year"], **period["values"], **period["ratios"]})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=datetime.now().year - 1)
    args = parser.parse_args()
    api_key = os.getenv("DART_API_KEY", "").strip()
    if not api_key:
        print("DART_API_KEY 환경변수가 필요합니다.", file=sys.stderr)
        return 2
    data = build(api_key, args.start_year, args.end_year)
    write_outputs(data)
    print(f"{len(data['periods'])}개 연도 갱신 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
