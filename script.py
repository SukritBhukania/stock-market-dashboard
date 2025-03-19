from flask import Flask, render_template, send_file
import yfinance as yf
import pandas as pd
import os
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)

industries = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSM", "INTC", "AMD", "IBM"],
    "Finance": ["JPM", "GS", "BAC", "MS", "WFC", "C", "AXP", "USB", "PNC", "TFC"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "VLO", "KMI", "HAL", "PSX"],
    "Healthcare": ["JNJ", "PFE", "UNH", "MRK", "ABBV", "LLY", "TMO", "BMY", "GILD", "CVS"],
    "Automotive": ["TSLA", "F", "GM", "RIVN", "LCID", "STLA", "HMC", "TM", "NIO", "XPEV"]
}

def fetch_stock_data():
    all_data = []
    for industry, stocks in industries.items():
        for stock in stocks:
            ticker = yf.Ticker(stock)
            df = ticker.history(period="1y", interval="1d")
            info = ticker.info

            if not df.empty:
                df.reset_index(inplace=True)
                df["symbol"] = stock
                df["industry"] = industry
                df["date"] = df["Date"].dt.date
                
                # Ensure values exist
                df["pe_ratio"] = info.get("trailingPE", 0) or 0.0
                df["market_cap"] = (info.get("marketCap", 0) or 0) / 1e9
                df["dividend_yield"] = (info.get("dividendYield", 0) or 0) * 100
                
                df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
                all_data.append(df[["industry", "symbol", "date", "open", "high", "low", "close", "volume", "pe_ratio", "market_cap", "dividend_yield"]])

    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_excel("industry_stock_data.xlsx", index=False)
    print("✅ Stock data successfully fetched and saved.")
    return combined_df

def load_stock_data():
    if os.path.exists("industry_stock_data.xlsx"):
        return pd.read_excel("industry_stock_data.xlsx")
    return fetch_stock_data()

def generate_industry_plots(df, industry):
    os.makedirs("static", exist_ok=True)

    industry_data = df[df['industry'] == industry]

    # Industry-Wise Growth Trends
    industry_trends = industry_data.groupby(["date"])["close"].mean().reset_index()
    fig1 = px.line(industry_trends, x="date", y="close", 
                   title=f"📈 {industry} Growth Trends Over Time",
                   template="plotly_dark")
    fig1.update_layout(height=600, width=1100)
    pio.write_html(f"static/{industry.lower()}_growth_trend.html", fig1)

    # Industry-Wise Risk (Volatility)
    industry_volatility = industry_data.groupby("symbol")["close"].std().reset_index()
    fig2 = px.bar(industry_volatility, x="symbol", y="close", 
                  title=f"⚠️ {industry} Risk (Volatility)",
                  template="plotly_dark", color="symbol")
    fig2.update_layout(height=500, width=1100)
    pio.write_html(f"static/{industry.lower()}_risk_chart.html", fig2)

    # Industry-Wise Trading Volume
    industry_volume = industry_data.groupby(["date"])["volume"].sum().reset_index()
    fig3 = px.line(industry_volume, x="date", y="volume", 
                   title=f"📊 {industry} Volume Traded Over Time",
                   template="plotly_dark")
    fig3.update_layout(height=600, width=1100)
    pio.write_html(f"static/{industry.lower()}_volume_chart.html", fig3)

    print(f"✅ {industry} charts updated successfully.")

def compute_ratios(df):
    df["pct_change"] = df.groupby("symbol")["close"].pct_change()
    volatility = df.groupby("symbol")["pct_change"].std().reset_index().rename(columns={"pct_change": "volatility"})
    ratios = df.groupby("symbol")[["pe_ratio", "market_cap", "dividend_yield"]].mean().reset_index()
    return ratios.merge(volatility, on="symbol")

@app.route("/")
def home():
    df = load_stock_data()
    return render_template("index.html", stock_data=df.to_dict(orient="records"))

@app.route("/industry")
def industry():
    # Logic to display industry analysis
    return render_template("industry.html")

@app.route("/ratios")
def ratios():
    # Logic to display ratios analysis
    return render_template("ratios.html")

@app.route("/download")
def download_excel():
    return send_file("industry_stock_data.xlsx", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)