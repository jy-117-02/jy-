from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path
from typing import Any

import requests


class DartError(RuntimeError):
    pass


class DartClient:
    BASE = "https://opendart.fss.or.kr/api"
    FATAL = {"010", "011", "012", "020", "901"}
    EMPTY = {"013", "014"}

    def __init__(self, api_key: str, timeout: int = 45, pause: float = 0.18):
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.pause = pause
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "JY-SAMSUNG-DART-Agent/2.0"})

    def _request(self, endpoint: str, params: dict[str, Any], binary: bool = False):
        query = {"crtfc_key": self.api_key, **params}
        last_error = None
        for attempt in range(4):
            try:
                response = self.session.get(f"{self.BASE}/{endpoint}", params=query, timeout=self.timeout)
                response.raise_for_status()
                time.sleep(self.pause)
                return response.content if binary else response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(2 ** attempt)
        raise DartError(f"OpenDART 요청 실패: {endpoint}: {last_error}")

    def financial_statements(self, corp_code: str, year: int, report_code: str, fs_div: str = "CFS") -> list[dict[str, Any]] | None:
        payload = self._request("fnlttSinglAcntAll.json", {
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": report_code,
            "fs_div": fs_div,
        })
        status = payload.get("status")
        if status == "000":
            return payload.get("list", [])
        if status in self.EMPTY:
            return None
        if status in self.FATAL:
            raise DartError(f"OpenDART {status}: {payload.get('message')}")
        raise DartError(f"OpenDART {status}: {payload.get('message')}")

    def list_filings(self, corp_code: str, year: int, detail_type: str) -> list[dict[str, Any]]:
        # 사업보고서는 통상 결산연도 다음 해에 제출되고, 분기·반기보고서는 같은 해에 제출됩니다.
        if detail_type == "A001":
            begin_date, end_date = f"{year + 1}0101", f"{year + 1}0630"
        else:
            begin_date, end_date = f"{year}0101", f"{year}1231"
        payload = self._request("list.json", {
            "corp_code": corp_code,
            "bgn_de": begin_date,
            "end_de": end_date,
            "last_reprt_at": "Y",
            "pblntf_ty": "A",
            "pblntf_detail_ty": detail_type,
            "sort": "date",
            "sort_mth": "desc",
            "page_count": "100",
        })
        status = payload.get("status")
        if status == "000":
            return payload.get("list", [])
        if status in self.EMPTY:
            return []
        raise DartError(f"OpenDART {status}: {payload.get('message')}")

    def download_document_texts(self, receipt_no: str) -> list[tuple[str, str]]:
        content = self._request("document.xml", {"rcept_no": receipt_no}, binary=True)
        try:
            archive = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile as exc:
            raise DartError(f"공시 원문 ZIP 해제 실패: {receipt_no}") from exc
        documents = []
        for name in archive.namelist():
            if not name.lower().endswith((".xml", ".html", ".htm")):
                continue
            raw = archive.read(name)
            text = None
            for encoding in ("utf-8", "euc-kr", "cp949"):
                try:
                    text = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if text:
                documents.append((name, text))
        return documents

    @staticmethod
    def save_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
