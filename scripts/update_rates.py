"""Refresh the iFAST margin rates and the FX rates in index.html.

Reads the board (IFF) and preferential (IGB) rates from the JSON feed behind
https://www.ifastgm.com.sg/igm/adviser/cash-solutions/product-financing and
the units-per-USD rates from the Yahoo Finance quotes behind
https://sg.finance.yahoo.com/markets/currencies/, then rewrites pfBoard /
pfPref / fx in the CCY table, plus the dates that say when they were read.
Exits non-zero, leaving the file untouched, if either feed looks wrong.
"""
import datetime
import json
import pathlib
import re
import sys
import urllib.request

API = "https://www.ifastgm.com.sg/igm/web/rest/microsite/"
FEEDS = {"pfBoard": "get-margin-system-interest-rate?currency=",
         "pfPref": "get-margin-system-interest-rate-igb"}
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{}=X?range=1d&interval=1d"
HTML = pathlib.Path(__file__).resolve().parent.parent / "index.html"


def fetch(path):
    req = urllib.request.Request(API + path, data=b"{}", method="POST", headers={
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("status") != "SUCCESS":
        sys.exit(f"{path}: status {body.get('status')!r}")
    return body["data"]


def fetch_fx(c):
    req = urllib.request.Request(YAHOO.format(c), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        meta = json.load(r)["chart"]["result"][0]["meta"]
    return float(meta["regularMarketPrice"])


def main():
    html = HTML.read_text(encoding="utf-8")
    ccys = re.findall(r'\{c:"([A-Z]{3})"', html)
    rates, dates = {}, set()
    for field, path in FEEDS.items():
        rows = {d["currency"]: d for d in fetch(path)}
        for c in ccys:
            if c not in rows:
                sys.exit(f"{field}: {c} missing from feed")
            v = float(rows[c]["interestRate"])
            if not 0 <= v <= 20:
                sys.exit(f"{field}: {c} rate {v} out of range")
            rates[(c, field)] = v
            dates.add(rows[c]["settlementDate"])

    fx = {}
    for c in ccys:
        if c == "USD":
            continue
        old = float(re.search(r'\{c:"%s"[^}]*?fx:\s*([\d.]+)' % c, html).group(1))
        v = fetch_fx(c)
        if not 0.75 * old <= v <= 1.25 * old:
            sys.exit(f"fx: {c} {v} is more than 25% from {old}")
        fx[c] = v

    def put(c, field, text):
        nonlocal html
        pat = re.compile(r'(\{c:"%s"[^}]*?%s:)\s*[\d.]+' % (c, field))
        html, n = pat.subn(lambda m: m.group(1) + text, html, count=1)
        if n != 1:
            sys.exit(f"could not find {field} for {c} in index.html")

    for (c, field), v in rates.items():
        put(c, field, f"{v:.2f}")
    for c, v in fx.items():
        put(c, "fx", f"{v:.6g}")

    d = datetime.date.fromisoformat(max(dates))
    stamp = f"{d.day} {d:%b %Y}"
    html = re.sub(r'(id="fx-date">)[^<]*', rf"\g<1>{stamp}", html, count=1)
    html = re.sub(r"(rates, read )\d{1,2} \w{3} \d{4}", rf"\g<1>{stamp}", html, count=1)
    html = re.sub(r"(fx = units per USD \()[^,]*, \d{1,2} \w{3} \d{4}",
                  rf"\g<1>Yahoo Finance, {stamp}", html, count=1)
    html = re.sub(r"(margin rates as published )\d{1,2} \w{3} \d{4}", rf"\g<1>{stamp}", html, count=1)

    HTML.write_text(html, encoding="utf-8")
    print(f"rates as of {stamp}: " + ", ".join(
        f"{c} {rates[(c, 'pfBoard')]:.2f}/{rates[(c, 'pfPref')]:.2f}" for c in ccys))
    print("fx per USD: " + ", ".join(f"{c} {v:.6g}" for c, v in fx.items()))


if __name__ == "__main__":
    main()
