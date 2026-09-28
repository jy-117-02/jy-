from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup


NUMBER = re.compile(r"[-+]?\(?\d[\d,]*\)?")


def normalize_label(value: str) -> str:
    return re.sub(r"[\s·ㆍ()\[\]]+", "", value or "").lower()


def parse_amount(value: str) -> int | None:
    text = (value or "").strip().replace(" ", "")
    match = NUMBER.search(text)
    if not match:
        return None
    token = match.group(0)
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()").replace(",", "")
    try:
        number = int(token)
    except ValueError:
        return None
    return -number if negative else number


def _table_rows(html: str) -> list[list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for row in soup.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
        if len(cells) >= 2:
            rows.append(cells)
    return rows


def parse_legacy_documents(documents: list[tuple[str, str]], metric_config: dict[str, Any]) -> list[dict[str, Any]]:
    aliases = {}
    for metric, spec in metric_config.items():
        for name in spec.get("names", []):
            aliases[normalize_label(name)] = (metric, spec.get("statement", ""))

    candidates: dict[str, list[tuple[int, list[dict[str, Any]]]]] = {"BS": [], "IS": [], "CF": []}
    for filename, html in documents:
        rows = _table_rows(html)
        extracted: dict[str, list[dict[str, Any]]] = {"BS": [], "IS": [], "CF": []}
        for cells in rows:
            label = normalize_label(cells[0])
            matched = None
            for alias, value in aliases.items():
                if label == alias or (len(alias) >= 4 and alias in label):
                    matched = value
                    break
            if not matched:
                continue
            amount = next((parse_amount(cell) for cell in cells[1:] if parse_amount(cell) is not None), None)
            if amount is None:
                continue
            metric, statement = matched
            extracted[statement].append({
                "sj_div": statement,
                "account_id": "legacy_" + metric,
                "account_nm": cells[0],
                "thstrm_amount": str(amount),
                "thstrm_add_amount": str(amount),
                "legacy_source": filename,
            })
        for statement, values in extracted.items():
            unique = {row["account_id"]: row for row in values}
            score = len(unique)
            threshold = 3 if statement != "CF" else 2
            if score >= threshold:
                candidates[statement].append((score, list(unique.values())))

    result = []
    for statement in ("BS", "IS", "CF"):
        if candidates[statement]:
            result.extend(max(candidates[statement], key=lambda item: item[0])[1])
    return result

