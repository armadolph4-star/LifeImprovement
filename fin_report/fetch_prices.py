#!/usr/bin/env python3
"""
Zero-dependency End-of-Day (EOD) market price & FX fetcher for the Family Financial Report.
Reads tickers dynamically from financial_data.json and writes market_prices.json.
Compatible with Python 3.8+.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT_SEC = 10


def http_get_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/html,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def http_get_json(url: str) -> dict:
    return json.loads(http_get_text(url))


def extract_tickers(ledger: dict, all_versions: bool = False) -> list[str]:
    versions = ledger.get("versions")
    if isinstance(versions, list) and versions:
        target_versions = versions if all_versions else [versions[-1]]
    elif isinstance(ledger.get("data"), list):
        target_versions = [{"data": ledger["data"]}]
    else:
        return []

    tickers: list[str] = []
    seen: set[str] = set()
    for ver in target_versions:
        items = ver.get("data", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("entryType") not in ("stock", "rsu"):
                continue
            raw_ticker = item.get("ticker")
            if isinstance(raw_ticker, str):
                norm = raw_ticker.strip().upper()
                if norm and norm not in seen:
                    seen.add(norm)
                    tickers.append(norm)
    return tickers


def fetch_fx_rates(fallback_rates: dict) -> dict:
    rates = {
        "$": float(fallback_rates.get("$", 3.65)),
        "€": float(fallback_rates.get("€", 3.95)),
    }

    for symbol, code in (("$", "USD"), ("€", "EUR")):
        url = f"https://open.er-api.com/v6/latest/{code}"
        try:
            payload = http_get_json(url)
            ils_rate = payload.get("rates", {}).get("ILS")
            if isinstance(ils_rate, (int, float)) and ils_rate > 0:
                rates[symbol] = round(float(ils_rate), 4)
                print(f"[OK]  FX {code}->ILS = {rates[symbol]}")
            else:
                print(f"[ERR] FX {code}->ILS missing in response; keeping {rates[symbol]}")
        except Exception as exc:
            print(f"[ERR] FX {code}->ILS failed ({exc}); keeping {rates[symbol]}")

    return rates


def parse_date_string(raw: str) -> str:
    raw = raw.strip()
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%d/%m/%y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return datetime.date.today().strftime("%Y-%m-%d")


def fetch_funder_mutual_fund(fund_id: str) -> dict:
    url = f"https://www.funder.co.il/fund/{urllib.parse.quote(fund_id)}"
    html = http_get_text(url)

    price_agorot = None
    date_str = None

    # 1. Try embedded JSON / Next.js / script state fields first
    json_price_patterns = [
        r'"(?:sellPrice|buyPrice|unitPrice|lastPrice|price|nav)"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
        r'"(?:navDate|priceDate|lastDate|date|updateDate)"\s*:\s*"(\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{2,4})"',
    ]
    m_price = re.search(json_price_patterns[0], html, re.IGNORECASE)
    if m_price:
        val = float(m_price.group(1))
        if val > 0:
            price_agorot = val

    m_date = re.search(json_price_patterns[1], html, re.IGNORECASE)
    if m_date:
        date_str = parse_date_string(m_date.group(1))

    # 2. Fallback to visible Hebrew HTML table/label patterns on Funder
    if price_agorot is None:
        text_only = re.sub(r"<[^>]+>", " ", html)
        text_only = re.sub(r"\s+", " ", text_only)

        hebrew_patterns = [
            r"(?:מחיר\s*(?:פדיון|קנייה|יחידה)|שער\s*(?:יחידה|פדיון|סגירה|אחרון))\s*[:\-]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)",
            r"([0-9]{2,6}\.[0-9]{1,4})\s*(?:אג'|אגורות)",
        ]
        for pat in hebrew_patterns:
            m = re.search(pat, text_only)
            if m:
                val = float(m.group(1).replace(",", ""))
                if val > 0:
                    price_agorot = val
                    break

        if date_str is None:
            m_heb_date = re.search(
                r"(?:נכון\s*ל(?:תאריך)?|תאריך\s*(?:שער|עדכון)?)\s*[:\-]?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
                text_only,
            )
            if not m_heb_date:
                m_heb_date = re.search(r"(\d{1,2}[./]\d{1,2}[./]20\d{2})", text_only)
            if m_heb_date:
                date_str = parse_date_string(m_heb_date.group(1))

    if price_agorot is None or price_agorot <= 0:
        raise ValueError("Could not parse unit price (Agorot) from Funder HTML")

    # Convert Agorot to ILS
    price_ils = round(price_agorot / 100.0, 4)
    return {
        "price": price_ils,
        "currency": "₪",
        "date": date_str or datetime.date.today().strftime("%Y-%m-%d"),
    }


def fetch_bizportal_etf(fund_id: str) -> dict:
    biz_url = f"https://www.bizportal.co.il/tradedfund/quote/generalview/{urllib.parse.quote(fund_id)}"
    html = http_get_text(biz_url)

    price_val = None
    date_str = None

    m_json = re.search(r'"(?:lastPrice|LastPrice|price|Price|rate|Rate)"\s*:\s*([0-9]+(?:\.[0-9]+)?)', html)
    if m_json:
        val = float(m_json.group(1))
        if val > 0:
            price_val = val

    if price_val is None:
        text_only = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        patterns = [
            (r'class="[^"]*number[^"]*"[^>]*>\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)', html),
            (r"(?:שער\s*(?:אחרון|סגירה|בסיס)|מחיר\s*אחרון)\s*[:\-]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)", text_only),
        ]
        for pat, target in patterns:
            m = re.search(pat, target)
            if m:
                val = float(m.group(1).replace(",", ""))
                if val > 0:
                    price_val = val
                    break

    m_date = re.search(r"(\d{1,2}[./]\d{1,2}[./]20\d{2})", html)
    if m_date:
        date_str = parse_date_string(m_date.group(1))

    if price_val is None or price_val <= 0:
        raise ValueError("Could not parse unit price (Agorot) from Bizportal HTML")

    return {
        "price": round(price_val / 100.0, 4),
        "currency": "₪",
        "date": date_str or datetime.date.today().strftime("%Y-%m-%d"),
    }


def fetch_israeli_fund_or_etf(fund_id: str) -> dict:
    try:
        return fetch_funder_mutual_fund(fund_id)
    except Exception:
        return fetch_bizportal_etf(fund_id)


def fetch_yahoo_us_quote(ticker: str) -> dict:
    encoded = urllib.parse.quote(ticker)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval=1d&range=5d"
    payload = http_get_json(url)

    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise ValueError(str(chart["error"]))

    results = chart.get("result") or []
    if not results:
        raise ValueError("Empty chart result")

    result = results[0]
    meta = result.get("meta") or {}
    timestamps = result.get("timestamp") or []
    quote_list = (result.get("indicators") or {}).get("quote") or []
    closes = quote_list[0].get("close") if quote_list else []

    raw_price = None
    last_ts = None

    if isinstance(closes, list):
        for idx in range(len(closes) - 1, -1, -1):
            c = closes[idx]
            if isinstance(c, (int, float)) and c > 0:
                raw_price = float(c)
                if idx < len(timestamps) and isinstance(timestamps[idx], (int, float)):
                    last_ts = int(timestamps[idx])
                break

    if raw_price is None:
        reg_price = meta.get("regularMarketPrice")
        if isinstance(reg_price, (int, float)) and reg_price > 0:
            raw_price = float(reg_price)
            if isinstance(meta.get("regularMarketTime"), (int, float)):
                last_ts = int(meta["regularMarketTime"])

    if raw_price is None or raw_price <= 0:
        raise ValueError("No valid closing price found")

    raw_currency = str(meta.get("currency") or "").upper()
    is_tase_agorot = ticker.endswith(".TA") or raw_currency == "ILA"

    if is_tase_agorot:
        price = round(raw_price / 100.0, 4)
        currency = "₪"
    else:
        price = round(raw_price, 4)
        currency_map = {"USD": "$", "EUR": "€", "ILS": "₪"}
        currency = currency_map.get(raw_currency, raw_currency or "$")

    if last_ts:
        date_str = datetime.datetime.fromtimestamp(last_ts, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
    else:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    return {
        "price": price,
        "currency": currency,
        "date": date_str,
    }


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Fetch EOD market prices for financial_data.json")
    parser.add_argument(
        "--input",
        type=Path,
        default=base_dir / "financial_data.json",
        help="Path to input financial_data.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=base_dir / "market_prices.json",
        help="Path to output market_prices.json",
    )
    parser.add_argument(
        "--all-versions",
        action="store_true",
        help="Extract tickers across all historical versions instead of only the latest snapshot",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"[ERR] Input file not found: {args.input}", file=sys.stderr)
        return 1

    try:
        ledger = json.loads(args.input.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[ERR] Failed to parse {args.input}: {exc}", file=sys.stderr)
        return 1

    existing_rates = ledger.get("rates") if isinstance(ledger.get("rates"), dict) else {}
    rates = fetch_fx_rates(existing_rates)

    tickers = extract_tickers(ledger, all_versions=args.all_versions)
    if not tickers:
        print("[SKIP] No stock/RSU tickers found in financial_data.json")

    prices: dict[str, dict] = {}
    for ticker in tickers:
        try:
            if re.fullmatch(r"\d{6,8}", ticker):
                quote = fetch_israeli_fund_or_etf(ticker)
                prices[ticker] = quote
                print(f"[OK]  IL Security {ticker}: {quote['price']} {quote['currency']} ({quote['date']})")
            else:
                quote = fetch_yahoo_us_quote(ticker)
                prices[ticker] = quote
                print(f"[OK]  Quote {ticker}: {quote['price']} {quote['currency']} ({quote['date']})")
        except Exception as exc:
            print(f"[ERR] {ticker}: {exc}")

    output_payload = {
        "updatedAt": datetime.date.today().strftime("%Y-%m-%d"),
        "rates": rates,
        "prices": prices,
    }

    args.output.write_text(
        json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[DONE] Wrote {len(prices)}/{len(tickers)} prices to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
