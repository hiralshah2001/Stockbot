import yfinance as yf
import pandas as pd

# Function to calculate RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Ask the user to input stock tickers and alert thresholds
tickers = input("Enter stock ticker symbols separated by commas (e.g., TSLA, AAPL, AMZN): ").upper().split(',')
rsi_low = float(input("Enter RSI lower limit for alerts (e.g., 30 for oversold): "))
rsi_high = float(input("Enter RSI upper limit for alerts (e.g., 70 for overbought): "))
price_lower = float(input("Enter price lower limit for alerts: "))
price_upper = float(input("Enter price upper limit for alerts: "))

# Initialize a list to hold summary data
summary_data = []

# Process each ticker
for ticker in [t.strip() for t in tickers]:
    print(f"\nFetching data for {ticker}...\n")
    try:
        stock = yf.Ticker(ticker)

        # Fetch stock info
        info = stock.info
        current_price = info.get('regularMarketPrice', None)
        fifty_two_week_high = info.get('fiftyTwoWeekHigh', None)
        fifty_two_week_low = info.get('fiftyTwoWeekLow', None)

        # Fetch historical data for the last 1 year
        history = stock.history(period="1y")

        # Fallback for current price
        if not current_price:
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                print(f"\nCurrent price not available. Using the latest closing price: ${current_price:.2f}")
            else:
                print("\nNo historical data available to determine the price.")
                current_price = None

        # Calculate moving averages
        history['50_MA'] = history['Close'].rolling(window=50).mean()
        history['200_MA'] = history['Close'].rolling(window=200).mean()
        ma_50 = history['50_MA'].iloc[-1] if len(history) >= 50 else None
        ma_200 = history['200_MA'].iloc[-1] if len(history) >= 200 else None

        # Calculate RSI
        history['RSI'] = calculate_rsi(history)
        rsi = history['RSI'].iloc[-1] if not history['RSI'].isna().all() else None

        # Decision-making logic
        decision = "Hold"
        if current_price and ma_50 and ma_200:
            if current_price > ma_50 and current_price > ma_200:
                decision = "Buy (Uptrend)"
            elif current_price < ma_50 and current_price < ma_200:
                decision = "Sell (Downtrend)"
            else:
                decision = "Hold (Sideways Trend)"

        if rsi and rsi < 30:
            decision += " (Strong Buy - Oversold)"
        elif rsi and rsi > 70:
            decision += " (Strong Sell - Overbought)"

        print(f"\nDecision for {ticker}: {decision}")

        # Check alert conditions
        print("\nAlerts:")
        if rsi is not None:
            if rsi < rsi_low:
                print(f"ALERT: RSI for {ticker} is {rsi:.2f} (Below {rsi_low} - Oversold)")
            elif rsi > rsi_high:
                print(f"ALERT: RSI for {ticker} is {rsi:.2f} (Above {rsi_high} - Overbought)")
        else:
            print(f"No RSI data available for {ticker}.")

        if current_price is not None:
            if current_price < price_lower:
                print(f"ALERT: Current price for {ticker} is ${current_price:.2f} (Below ${price_lower:.2f})")
            elif current_price > price_upper:
                print(f"ALERT: Current price for {ticker} is ${current_price:.2f} (Above ${price_upper:.2f})")
        else:
            print(f"No price data available for {ticker}.")

        # Add to summary data
        summary_data.append({
            "Ticker": ticker,
            "Stock Name": info.get('longName', 'N/A'),
            "Current Price": f"${current_price:.2f}" if current_price else "N/A",
            "50-Day MA": f"${ma_50:.2f}" if ma_50 else "Insufficient Data",
            "200-Day MA": f"${ma_200:.2f}" if ma_200 else "Insufficient Data",
            "RSI": f"{rsi:.2f}" if rsi else "Insufficient Data",
            "Decision": decision
        })

        # Save historical data for each stock
        csv_filename = f"{ticker}_historical_data.csv"
        history.to_csv(csv_filename)
        print(f"\nHistorical data saved to {csv_filename}")

    except Exception as e:
        print(f"\nError fetching data for {ticker}. Please check the ticker symbol and try again.")
        print("Error details:", e)

# Create a summary DataFrame
summary_df = pd.DataFrame(summary_data)

# Save the summary report to a CSV file
summary_filename = "stock_summary_report.csv"
summary_df.to_csv(summary_filename, index=False)
print(f"\nSummary report saved to {summary_filename}")
