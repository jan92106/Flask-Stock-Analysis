from flask import Flask, render_template, jsonify
import yfinance as yf
import pandas as pd
# Removed time import to improve speed

app = Flask(__name__)

def get_nifty50_stocks():
    # Removed HDFC.NS (Delisted)
    return [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "HINDUNILVR.NS",
        "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
        "LT.NS", "ASIANPAINT.NS", "AXISBANK.NS", "MARUTI.NS", "TITAN.NS", "ULTRACEMCO.NS",
        "WIPRO.NS", "SUNPHARMA.NS", "INDUSINDBK.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS",
        "TATASTEEL.NS", "NESTLEIND.NS", "TECHM.NS", "JSWSTEEL.NS", "HCLTECH.NS",
        "COALINDIA.NS", "ADANIPORTS.NS"
    ]

def fetch_stock_data(stock):
    try:
        ticker = yf.Ticker(stock)
        # Fetch slightly more data to ensure we have previous close
        data = ticker.history(period='5d')
        
        if data.empty or 'Close' not in data.columns:
            return None
        
        current_close = data['Close'].iloc[-1]
        # Use previous closing price for accurate "Change" calculation
        prev_close = data['Close'].iloc[-2] if len(data) > 1 else data['Open'].iloc[-1]
        
        change_val = current_close - prev_close
        p_change_val = (change_val / prev_close) * 100
        
        return {
            'symbol': stock.replace(".NS", ""),
            'lastPrice': round(current_close, 2),
            'dayHigh': round(data['High'].iloc[-1], 2),
            'dayLow': round(data['Low'].iloc[-1], 2),
            'prevClose': round(prev_close, 2),
            'change': round(change_val, 2),
            'pChange': round(p_change_val, 2),
            'SMA_5': round(data['Close'].rolling(window=5).mean().iloc[-1], 2) if len(data) >= 5 else None,
            'SMA_10': round(data['Close'].rolling(window=10).mean().iloc[-1], 2) if len(data) >= 10 else None
        }
    except Exception as e:
        print(f"Error fetching {stock}: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stocks', methods=['GET'])
def get_stock_data():
    stocks = get_nifty50_stocks()
    data = []
    
    # LOOP PERFORMANCE FIX: Removed time.sleep(2)
    # Even without sleep, fetching 30 stocks sequentially is slow.
    # For a real production app, use yf.download(..., group_by='ticker')
    for stock in stocks:
        stock_data = fetch_stock_data(stock)
        if stock_data:
            data.append(stock_data)
            
    df = pd.DataFrame(data)
    if df.empty:
        return jsonify({"error": "No stock data available."}), 500
    
    live_prices = df[['symbol', 'lastPrice', 'change', 'pChange']].to_dict(orient='records')
    
    # Filter for trending stocks where SMA5 > SMA10
    # Added safety check for columns existence
    if 'SMA_5' in df.columns and 'SMA_10' in df.columns:
        trending_stocks_df = df[df['SMA_5'] > df['SMA_10']]
        trending_stocks = trending_stocks_df[['symbol', 'lastPrice', 'SMA_5', 'SMA_10']].to_dict(orient='records')
    else:
        trending_stocks = []
    
    return jsonify({
        "livePrices": live_prices,
        "trendingStocks": trending_stocks
    })

if __name__ == '__main__':
    app.run(debug=True)