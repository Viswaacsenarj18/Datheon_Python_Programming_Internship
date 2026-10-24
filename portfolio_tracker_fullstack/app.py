from flask import Flask, render_template, request, jsonify
import csv
import os
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    yf = None

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio_data.csv")
SP500_FILE = os.path.join(BASE_DIR, "sp500_companies.csv")
SAMPLE_PRICE_FILE = os.path.join(BASE_DIR, "sample_prices.csv")

FIELDS = ["id", "ticker", "company", "buy_price", "quantity", "current_price", "added_at"]


def read_csv_rows(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except (OSError, csv.Error):
        return []


def write_portfolio(rows):
    with open(PORTFOLIO_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def company_lookup():
    companies = {}
    for row in read_csv_rows(SP500_FILE):
        ticker = (row.get("Symbol") or row.get("symbol") or "").strip().upper()
        name = (row.get("Security") or row.get("security") or "").strip()
        if ticker:
            companies[ticker] = name
    return companies


def sample_prices():
    prices = {}
    for row in read_csv_rows(SAMPLE_PRICE_FILE):
        ticker = (row.get("ticker") or row.get("Symbol") or "").strip().upper()
        raw = row.get("current_price") or row.get("Current Price") or row.get("price")
        if ticker and raw:
            try:
                prices[ticker] = float(str(raw).replace("$", "").replace(",", ""))
            except ValueError:
                continue
    return prices


def get_quote(ticker):
    prices = sample_prices()
    if ticker in prices and prices[ticker] > 0:
        return prices[ticker], "sample"
    if yf is not None:
        try:
            stock = yf.Ticker(ticker)
            price = stock.fast_info.get("lastPrice")
            if not price:
                hist = stock.history(period="1d")
                if not hist.empty:
                    closes = hist["Close"].dropna()
                    if not closes.empty:
                        price = closes.iloc[-1]
            if price and float(price) > 0:
                return round(float(price), 4), "live"
        except Exception:
            pass
    return None, "manual"


def all_portfolio_rows():
    companies = company_lookup()
    result = []
    for row in read_csv_rows(PORTFOLIO_FILE):
        try:
            ticker = row["ticker"].upper()
            buy_price = float(row["buy_price"])
            quantity = int(row["quantity"])
            current_price = float(row["current_price"])
        except (KeyError, ValueError, TypeError):
            continue
        invested = buy_price * quantity
        market_value = current_price * quantity
        pnl = market_value - invested
        pnl_pct = (pnl / invested * 100) if invested else 0
        result.append({
            "id": row.get("id", ""),
            "ticker": ticker,
            "company": row.get("company") or companies.get(ticker, ticker),
            "buy_price": round(buy_price, 2),
            "quantity": quantity,
            "current_price": round(current_price, 2),
            "invested": round(invested, 2),
            "market_value": round(market_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "added_at": row.get("added_at", ""),
        })
    return result


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/portfolio")
def get_portfolio():
    holdings = all_portfolio_rows()
    invested = sum(item["invested"] for item in holdings)
    market_value = sum(item["market_value"] for item in holdings)
    pnl = market_value - invested
    pnl_pct = (pnl / invested * 100) if invested else 0
    return jsonify({
        "holdings": holdings,
        "summary": {
            "total_holdings": len(holdings),
            "invested": round(invested, 2),
            "market_value": round(market_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
        }
    })


@app.get("/api/quote/<ticker>")
def quote(ticker):
    ticker = ticker.strip().upper()
    price, source = get_quote(ticker)
    company = company_lookup().get(ticker, ticker)
    if price is None:
        return jsonify({"ticker": ticker, "company": company, "price": None, "source": source,
                        "message": "No price source available. Enter the current price manually."})
    return jsonify({"ticker": ticker, "company": company, "price": price, "source": source})


@app.post("/api/holdings")
def add_holding():
    data = request.get_json(silent=True) or {}
    ticker = str(data.get("ticker", "")).strip().upper()
    try:
        buy_price = float(data.get("buy_price"))
        quantity = int(data.get("quantity"))
        current_price_input = data.get("current_price")
        current_price = float(current_price_input) if current_price_input not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"error": "Enter a valid buy price, quantity, and current price if needed."}), 400

    if not ticker or buy_price <= 0 or quantity <= 0 or (current_price is not None and current_price <= 0):
        return jsonify({"error": "Ticker, buy price, and quantity are required. Prices and quantity must be greater than zero."}), 400

    quote_source = "manual"
    if current_price is None:
        current_price, quote_source = get_quote(ticker)
    if current_price is None:
        return jsonify({"error": "Current price could not be found. Enter the current price manually."}), 400

    companies = company_lookup()
    rows = read_csv_rows(PORTFOLIO_FILE)
    # Each submitted purchase is saved as its own holding/transaction.
    next_id = str(max([int(r.get("id", "0") or 0) for r in rows if str(r.get("id", "0")).isdigit()] + [0]) + 1)
    rows.append({
        "id": next_id,
        "ticker": ticker,
        "company": companies.get(ticker, ticker),
        "buy_price": f"{buy_price:.4f}",
        "quantity": str(quantity),
        "current_price": f"{current_price:.4f}",
        "added_at": datetime.now().isoformat(timespec="seconds"),
    })
    write_portfolio(rows)
    return jsonify({"message": f"{ticker} holding added successfully.", "quote_source": quote_source})


@app.delete("/api/holdings/<holding_id>")
def delete_holding(holding_id):
    rows = read_csv_rows(PORTFOLIO_FILE)
    remaining = [row for row in rows if row.get("id") != holding_id]
    if len(remaining) == len(rows):
        return jsonify({"error": "Holding not found."}), 404
    write_portfolio(remaining)
    return jsonify({"message": "Holding deleted."})


@app.post("/api/refresh-prices")
def refresh_prices():
    rows = read_csv_rows(PORTFOLIO_FILE)
    updated = 0
    for row in rows:
        ticker = row.get("ticker", "").upper()
        price, source = get_quote(ticker)
        if price is not None:
            row["current_price"] = f"{price:.4f}"
            updated += 1
    write_portfolio(rows)
    return jsonify({"message": f"Updated prices for {updated} holding(s).", "updated": updated})


@app.get("/api/export")
def export_csv():
    # Serve the portfolio data file as a downloadable CSV report with calculated columns.
    holdings = all_portfolio_rows()
    output_path = os.path.join(BASE_DIR, "portfolio_summary.csv")
    columns = ["ticker", "company", "buy_price", "quantity", "current_price", "invested_amount",
               "current_market_value", "gain_loss", "gain_loss_percent"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for item in holdings:
            writer.writerow({
                "ticker": item["ticker"], "company": item["company"], "buy_price": item["buy_price"],
                "quantity": item["quantity"], "current_price": item["current_price"],
                "invested_amount": item["invested"], "current_market_value": item["market_value"],
                "gain_loss": item["pnl"], "gain_loss_percent": item["pnl_pct"],
            })
        summary = get_summary(holdings)
        writer.writerow({
            "ticker": "TOTAL", "company": "Portfolio total", "buy_price": "", "quantity": "",
            "current_price": "", "invested_amount": summary["invested"],
            "current_market_value": summary["market_value"], "gain_loss": summary["pnl"],
            "gain_loss_percent": summary["pnl_pct"],
        })
    from flask import send_file
    return send_file(output_path, as_attachment=True, download_name="portfolio_summary.csv", mimetype="text/csv")


def get_summary(holdings):
    invested = sum(item["invested"] for item in holdings)
    market_value = sum(item["market_value"] for item in holdings)
    pnl = market_value - invested
    return {
        "invested": round(invested, 2),
        "market_value": round(market_value, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl / invested * 100, 2) if invested else 0,
    }


if __name__ == "__main__":
    if not os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
    app.run(debug=True, host="127.0.0.1", port=5000)
