import yfinance as yf
import pandas as pd
import alpaca_trade_api as tradeapi
import schedule
import time
import os
import sys

# ── YOUR ALPACA KEYS ──────────────────────
API_KEY = "PK7OBTF6ZJA4XZR3QOYCDUVR4J"
SECRET_KEY = "5mWoKam6d8EPwS5iBNzqec4FsrjM8Xyytun8ewf8rn6b"
BASE_URL = "https://paper-api.alpaca.markets"

# ── CONNECT TO ALPACA ─────────────────────
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)

def run_trade():
    try:
        print("=== Kronos Trader Running ===")

        # Get fresh BTC data
        df = yf.download("BTC-USD", interval="1h",
                         period="15d", auto_adjust=True)
        df = df.reset_index()
        df.columns = [c[0].lower() if isinstance(c, tuple)
                      else c.lower() for c in df.columns]
        df['amount'] = df['close'] * df['volume']
        df = df.dropna().reset_index(drop=True)

        total = len(df)
        lookback = 150
        pred_len = 24
        current = float(df.iloc[-1]['close'])

        x_df = df.iloc[total-lookback:total][['open','high',
                       'low','close','volume','amount']]
        x_ts = df.iloc[total-lookback:total].iloc[:, 0]
        y_ts = df.iloc[total-pred_len:total].iloc[:, 0]

        print(f"Current BTC: ${current:,.2f}")

        pred_df = predictor.predict(
            df=x_df, x_timestamp=x_ts, y_timestamp=y_ts,
            pred_len=pred_len, T=0.6, top_p=0.9,
            sample_count=10
        )

        forecast = float(pred_df['close'].iloc[-1])
        signal = (forecast - current) / current

        print(f"Forecast: ${forecast:,.2f}")
        print(f"Signal: {signal*100:.2f}%")

        try:
            qty = int(api.get_position("BTCUSD").qty)
        except:
            qty = 0

        if signal > 0.01:
            api.submit_order(symbol="BTCUSD", qty=0.01,
                            side="buy", type="market",
                            time_in_force="gtc")
            print("✅ BUY placed!")
        elif signal < -0.01 and qty > 0:
            api.submit_order(symbol="BTCUSD", qty=0.01,
                            side="sell", type="market",
                            time_in_force="gtc")
            print("✅ SELL placed!")
        else:
            print("➡️ HOLD")

        print(f"Balance: ${api.get_account().portfolio_value}")

    except Exception as e:
        print(f"Error: {e}")

# Load Kronos
sys.path.insert(0, '/app/Kronos')
os.system('git clone https://github.com/shiyu-coder/Kronos /app/Kronos')
os.system('pip install -r /app/Kronos/requirements.txt -q')

from model import Kronos, KronosTokenizer, KronosPredictor
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
predictor = KronosPredictor(model, tokenizer, max_context=512)
print("✅ Kronos loaded!")

# Run immediately then every hour
run_trade()
schedule.every(1).hours.do(run_trade)

while True:
    schedule.run_pending()
    time.sleep(60)
