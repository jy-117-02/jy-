from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.analyzer import extract_values, finish_periods
from src.dart_client import DartClient, DartError
from src.legacy_parser import parse_legacy_documents


ROOT = Path(__file__).resolve().parents[1]
CORP_CODE = "00126380"
STOCK_CODE = "005930"
COMPANY = "삼성전자"

REPORTS = (
    {"reportCode": "11013", "detailType": "A003", "category": "quarterly", "label": "1분기", "sortOrder": 1, "month": "03"},
    {"reportCode": "11012", "detailType": "A002", "category": "halfYear", "label": "반기", "sortOrder": 2, "month": "06"},
    {"reportCode": "11014", "detailType": "A003", "category": "quarterly", "label": "3분기", "sortOrder": 3, "month": "09"},
    {"reportCode": "11011", "detailType": "A001", "category": "annual", "label": "사업보고서", "sortOrder": 4, "month": "12"},
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def select_filing(filings: list[dict[str, Any]], year: int, report: dict[str, Any]) -> dict[str, Any] | None:
    month = report["month"]
    expected = f"{year}.{month}"
    matches = [item for item in filings if expected in item.get("report_nm", "")]
    if not matches:
        name_hint = {"11011": "사업보고서", "11012": "반기보고서", "11013": "분기보고서", "11014": "분기보고서"}[report["reportCode"]]
        matches = [item for item in filings if name_hint in item.get("report_nm", "") and str(year) in item.get("report_nm", "")]
    return max(matches, key=lambda item: item.get("rcept_dt", ""), default=None)


def fetch_standard(client: DartClient, year: int, report: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
    rows = client.financial_statements(CORP_CODE, year, report["reportCode"], "CFS")
    if rows:
        return rows, "CFS"
    rows = client.financial_statements(CORP_CODE, year, report["reportCode"], "OFS")
    return rows, "OFS" if rows else None


def fetch_legacy(client: DartClient, year: int, report: dict[str, Any], metrics: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    filings = client.list_filings(CORP_CODE, year, report["detailType"])
    filing = select_filing(filings, year, report)
    if not filing:
        return [], {}
    receipt = filing["rcept_no"]
    documents = client.download_document_texts(receipt)
    rows = parse_legacy_documents(documents, metrics)
    return rows, {
        "receiptNo": receipt,
        "filingDate": filing.get("rcept_dt"),
        "filingName": filing.get("report_nm"),
        "documentCount": len(documents),
    }


def build_period(year: int, report: dict[str, Any], rows: list[dict[str, Any]], metrics: dict[str, Any], source: str, fs_div: str | None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = meta or {}
    return {
        "year": year,
        "period": f"{year} {report['label']}",
        "category": report["category"],
        "reportCode": report["reportCode"],
        "sortOrder": report["sortOrder"],
        "fsDiv": fs_div,
        "source": source,
        "receiptNo": meta.get("receiptNo"),
        "filingDate": meta.get("filingDate"),
        "filingName": meta.get("filingName"),
        "values": extract_values(rows, metrics, report["reportCode"]),
    }


def should_refresh(year: int, end_year: int, refresh_all: bool) -> bool:
    return refresh_all or year >= end_year - 1


def collect(start_year: int, end_year: int, refresh_all: bool, include_legacy: bool) -> dict[str, Any]:
    api_key = os.environ.get("DART_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("DART_API_KEY가 없습니다. 로컬 환경변수 또는 GitHub Actions Secret에 등록해 주세요.")

    metrics = read_json(ROOT / "config" / "metrics.json")
    client = DartClient(api_key)
    raw_dir = ROOT / "data" / "raw"
    periods: list[dict[str, Any]] = []
    warnings: list[str] = []

    for year in range(start_year, end_year + 1):
        if year < 2015 and not include_legacy:
            continue
        for report in REPORTS:
            cache = raw_dir / f"{year}_{report['reportCode']}.json"
            cached = read_json(cache) if cache.exists() and not should_refresh(year, end_year, refresh_all) else None
            if cached:
                rows = cached.get("rows", [])
                source = cached.get("source", "cache")
                fs_div = cached.get("fsDiv")
                meta = cached.get("meta", {})
            else:
                try:
                    if year >= 2015:
                        rows, fs_div = fetch_standard(client, year, report)
                        rows = rows or []
                        source = "OpenDART 정형 재무제표 API"
                        meta = {}
                    else:
                        rows, meta = fetch_legacy(client, year, report, metrics)
                        fs_div = "CFS 우선 원문"
                        source = "OpenDART 공시 원문 보완 파서"
                    DartClient.save_json(cache, {"source": source, "fsDiv": fs_div, "meta": meta, "rows": rows})
                except DartError as exc:
                    warnings.append(f"{year} {report['label']}: {exc}")
                    continue
            if not rows:
                warnings.append(f"{year} {report['label']}: 공개 데이터 없음")
                continue
            periods.append(build_period(year, report, rows, metrics, source, fs_div, meta))

    periods = finish_periods(periods)
    payload = {
        "company": COMPANY,
        "corpCode": CORP_CODE,
        "stockCode": STOCK_CODE,
        "currency": "KRW",
        "unit": "원",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "startYear": start_year,
        "endYear": end_year,
        "notes": [
            "연결재무제표(CFS)를 우선하고, 없으면 별도재무제표(OFS)를 사용합니다.",
            "2015년 이후는 OpenDART 정형 재무제표 API, 2010~2014년은 공시 원문을 보완 파싱합니다.",
            "분기·반기 손익/현금흐름 수치는 누적 기준이며 효율성 비율은 연환산됩니다.",
            "시장가격이 필요한 PER·PBR·EV/EBITDA는 DART만으로 계산하지 않습니다.",
        ],
        "warnings": warnings,
        "periods": periods,
    }
    return payload


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    value_keys = list(read_json(ROOT / "config" / "metrics.json").keys()) + ["InterestBearingDebt", "QuickAssets", "NetDebt", "CAPEX", "FCF", "EBITDA"]
    ratio_keys = ["grossMargin", "operatingMargin", "netMargin", "ebitdaMargin", "roa", "roe", "roic", "currentRatio", "quickRatio", "debtRatio", "equityRatio", "debtDependency", "interestCoverage", "netDebtToEbitda", "assetTurnover", "dso", "dio", "dpo", "ccc", "revenueGrowth", "cfoToNetIncome"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["year", "period", "category", "reportCode", "fsDiv", "source"] + value_keys + ratio_keys)
        writer.writeheader()
        for period in payload["periods"]:
            row = {key: period.get(key) for key in ("year", "period", "category", "reportCode", "fsDiv", "source")}
            row.update(period["values"])
            row.update(period["ratios"])
            writer.writerow(row)


def save_outputs(payload: dict[str, Any]) -> None:
    data_path = ROOT / "data" / "financials.json"
    docs_path = ROOT / "docs" / "data" / "financials.json"
    DartClient.save_json(data_path, payload)
    DartClient.save_json(docs_path, payload)
    write_csv(ROOT / "data" / "financials.csv", payload)
    write_csv(ROOT / "docs" / "data" / "financials.csv", payload)
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "config" / "peers.json", ROOT / "docs" / "data" / "peers.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="삼성전자 OpenDART 재무 데이터 수집기")
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=datetime.now().year)
    parser.add_argument("--refresh-all", action="store_true", help="기존 원본 캐시도 다시 받습니다.")
    parser.add_argument("--no-legacy", action="store_true", help="2010~2014 원문 보완 파싱을 건너뜁니다.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.start_year > args.end_year:
        raise SystemExit("start-year는 end-year보다 클 수 없습니다.")
    result = collect(args.start_year, args.end_year, args.refresh_all, not args.no_legacy)
    save_outputs(result)
    print(f"완료: {len(result['periods'])}개 기간, 경고 {len(result['warnings'])}건")
