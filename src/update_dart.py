#!/usr/bin/env python3
"""Collect Samsung Electronics periodic reports and derive financial ratios from OpenDART."""
from __future__ import annotations

import json
import os
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "data"
REPORT_DIR = ROOT / "data" / "reports"
BASE = "https://opendart.fss.or.kr/api"
KEY = os.environ.get("DART_API_KEY", "").strip()
HEADERS = {"User-Agent": "dart-samsung-finance-dashboard/1.0"}
PERIODS = {"annual": "11011", "half-year": "11012", "quarterly": "11013"}
# DART account IDs are more stable than localized labels across report years.
ACCOUNT_IDS = {
    "revenue": {"ifrs-full_Revenue", "ifrs-full_RevenueFromContractsWithCustomers", "dart_Revenue"},
    "operating_income": {"dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities"},
    "net_income": {"ifrs-full_ProfitLoss", "dart_ProfitLoss"},
    "assets": {"ifrs-full_Assets", "dart_TotalAssets"},
    "liabilities": {"ifrs-full_Liabilities", "dart_TotalLiabilities"},
    "equity": {"ifrs-full_Equity", "dart_TotalEquity"},
    "current_assets": {"ifrs-full_CurrentAssets", "dart_CurrentAssets"},
    "current_liabilities": {"ifrs-full_CurrentLiabilities", "dart_CurrentLiabilities"},
}


def api(path: str, **params):
    if not KEY:
        raise RuntimeError("DART_API_KEY is not set. Add it as a GitHub Actions secret.")
    response = requests.get(
        f"{BASE}/{path}",
        params={"crtfc_key": KEY, **params},
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") not in ("000", "013"):
        raise RuntimeError(f"DART {path}: {payload.get('status')} {payload.get('message')}")
    return payload


def to_num(value):
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def match(rows, metric):
    candidates = set(CFG["metrics"].get(metric, []))
    candidates.update(ACCOUNT_IDS.get(metric, set()))
    for fs in ("CFS", "OFS"):
        for row in rows:
            if row.get("fs_div") != fs:
                continue
            if row.get("account_nm") in candidates or row.get("account_id") in candidates:
                value = to_num(row.get("thstrm_amount"))
                if value is not None:
                    return value
    return None


def report_list(year):
    records = []
    page = 1
    while True:
        result = api(
            "list.json",
            corp_code=CFG["company"]["corp_code"],
            bgn_de=f"{year}0101",
            end_de=f"{year}1231",
            pblntf_ty="A",
            page_no=page,
            page_count=100,
        )
        records.extend(result.get("list", []))
        if page >= int(result.get("total_page", 1)):
            break
        page += 1
        time.sleep(0.15)

    output = []
    seen = set()
    for item in records:
        name = item.get("report_nm", "")
        if "사업보고서" in name:
            category = "annual"
        elif "반기보고서" in name:
            category = "half-year"
        elif "분기보고서" in name:
            category = "quarterly"
        else:
            continue
        receipt_no = item.get("rcept_no")
        if not receipt_no or receipt_no in seen:
            continue
        seen.add(receipt_no)
        output.append(
            {
                "category": category,
                "year": year,
                "report_name": name,
                "receipt_no": receipt_no,
                "filed_at": item.get("rcept_dt"),
                "viewer_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
            }
        )
    return output


def ratios_for(values):
    def ratio(numerator, denominator):
        return numerator / denominator * 100 if numerator is not None and denominator else None

    return {
        "operating_margin": ratio(values["operating_income"], values["revenue"]),
        "net_margin": ratio(values["net_income"], values["revenue"]),
        "roe": ratio(values["net_income"], values["equity"]),
        "debt_to_equity": ratio(values["liabilities"], values["equity"]),
        "current_ratio": ratio(values["current_assets"], values["current_liabilities"]),
        "roa": ratio(values["net_income"], values["assets"]),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    rows = []
    empty_responses = 0
    unmatched_examples = []

    for year in range(CFG["start_year"], date.today().year + 1):
        year_reports = report_list(year)
        reports.extend(year_reports)
        for report in year_reports:
            if year < CFG["financial_api_start_year"]:
                continue
            payload = api(
                "fnlttSinglAcntAll.json",
                corp_code=CFG["company"]["corp_code"],
                bsns_year=year,
                reprt_code=PERIODS[report["category"]],
                fs_div="CFS",
            )
            statement_rows = payload.get("list", [])
            values = {name: match(statement_rows, name) for name in CFG["metrics"]}
            if not any(value is not None for value in values.values()):
                empty_responses += 1
                if not unmatched_examples:
                    unmatched_examples = [
                        {
                            "fs_div": row.get("fs_div"),
                            "account_id": row.get("account_id"),
                            "account_nm": row.get("account_nm"),
                            "thstrm_amount": row.get("thstrm_amount"),
                        }
                        for row in statement_rows[:12]
                    ]
                continue
            rows.append(
                {
                    "period": f"{year} {report['category']}",
                    "year": year,
                    "category": report["category"],
                    "receipt_no": report["receipt_no"],
                    **values,
                    **ratios_for(values),
                }
            )
            time.sleep(0.15)

    reports.sort(key=lambda item: (item["filed_at"] or "", item["receipt_no"]), reverse=True)
    rows.sort(key=lambda item: (item["year"], item["category"]))
    if not rows:
        raise RuntimeError(
            "DART reports were found, but no financial accounts matched. "
            f"Checked {empty_responses} statements; sample accounts: {json.dumps(unmatched_examples, ensure_ascii=False)}"
        )

    (OUT / "reports.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "financials.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "peer_firms.json").write_text(
        json.dumps(CFG["peer_firms"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Updated {len(reports)} reports and {len(rows)} financial rows ({empty_responses} unmatched statements).")


if __name__ == "__main__":
    main()
