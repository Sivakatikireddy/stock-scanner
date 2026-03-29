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
        if df is None or df.empty:
            return None
        return df
    except Exception as e:
        print(f"❌ Data error for {stock}: {e}")
        return None


# ---------------- PATTERN CHECK (ERROR-FREE) ----------------
def check_pattern(df):
    try:
        if df is None or len(df) < 60:
            return False

        # Rolling calculations
        high_50 = df['High'].rolling(50).max()
        low_50 = df['Low'].rolling(50).min()
        avg_vol = df['Volume'].rolling(20).mean()
        recent_high = df['High'].rolling(20).max()

        # Latest row
        latest = df.iloc[-1]

        # Convert to scalar values safely
        high_val = float(high_50.iloc[-1])
        low_val = float(low_50.iloc[-1])
        avg_vol_val = float(avg_vol.iloc[-1])
        breakout_val = float(recent_high.iloc[-1])

        close_now = float(latest['Close'])
        volume_now = float(latest['Volume'])
        close_30 = float(df['Close'].iloc[-30])

        # Handle NaN values
        values = [high_val, low_val, avg_vol_val, breakout_val, close_now, volume_now, close_30]
        if any(pd.isna(values)):
            return False

        # Calculations
        range_val = (high_val - low_val) / low_val
        volume_spike = volume_now / avg_vol_val

        # Conditions
        cond1 = range_val < 0.3
        cond2 = volume_spike > 2
        cond3 = close_now > 0.9 * breakout_val
        cond4 = close_now < 1.5 * close_30

        return bool(cond1 and cond2 and cond3 and cond4)

    except Exception as e:
        print("❌ Feature error:", e)
        return False


# ---------------- MAIN SCANNER ----------------
def run_scanner():
    print("🚀 Running scanner...")

    # ✅ Test message (you can remove later)
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
