import yfinance as yf
import pandas as pd
import requests
import os

# ---------------- SETTINGS ----------------
stocks = [
    "SUZLON.NS",
    "RPOWER.NS",
    "IDEA.NS",
    "JPPOWER.NS",
    "GTLINFRA.NS"
]

# Get token from GitHub Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "1811269438"

# ---------------- TELEGRAM ALERT ----------------
def send_alert(message):
    try:
        if not BOT_TOKEN:
            print("❌ BOT_TOKEN is missing")
            return

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        response = requests.get(url, params={
            "chat_id": CHAT_ID,
            "text": message
        })

        print("✅ Alert sent:", message)
        print("Response:", response.text)

    except Exception as e:
        print("❌ Telegram Error:", e)


# ---------------- FETCH DATA ----------------
def get_data(stock):
    try:
        df = yf.download(stock, period="3mo", interval="1d", progress=False)
        return df
    except Exception as e:
        print(f"❌ Data error for {stock}: {e}")
        return None


# ---------------- PATTERN CHECK ----------------
def check_pattern(df):
    try:
        if df is None or len(df) < 50:
            return False

        # Range (accumulation)
        high_50 = df['High'].rolling(50).max()
        low_50 = df['Low'].rolling(50).min()
        range_val = (high_50 - low_50) / low_50

        # Volume spike
        avg_vol = df['Volume'].rolling(20).mean()
        volume_spike = df['Volume'] / avg_vol

        # Breakout level
        recent_high = df['High'].rolling(20).max()

        latest = df.iloc[-1]

        cond1 = range_val.iloc[-1] < 0.3
        cond2 = volume_spike.iloc[-1] > 2
        cond3 = latest['Close'] > 0.9 * recent_high.iloc[-1]

        # Avoid already pumped stocks
        cond4 = latest['Close'] < 1.5 * df['Close'].iloc[-30]

        if cond1 and cond2 and cond3 and cond4:
            return True

        return False

    except Exception as e:
        print("❌ Feature error:", e)
        return False


# ---------------- MAIN SCANNER ----------------
def run_scanner():
    print("🚀 Running scanner...")

    # 🔥 TEST MESSAGE (keep for now)
    send_alert("✅ GitHub scanner is working")

    found = []

    for stock in stocks:
        print(f"Checking {stock}...")
        df = get_data(stock)

        if check_pattern(df):
            found.append(stock)

    # Send results
    if found:
        message = "🚀 Breakout Candidates:\n" + "\n".join(found)
        send_alert(message)
    else:
        print("No strong setups today.")


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    run_scanner()
