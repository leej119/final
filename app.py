import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from plotly import graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Stock Information App", layout='wide')
# Sidebar for navigation
st.sidebar.title("Navigation")
def navigate_to(page):
    st.session_state.current_page = page

# Create buttons for navigation
if st.sidebar.button("Home"):
    navigate_to("Home")
if st.sidebar.button("Stock Graph"):
    navigate_to("Stock Graph")
if st.sidebar.button("Market Indices"):
    navigate_to("Market Indices")
if st.sidebar.button("ETF Information"):
    navigate_to("ETF Information")
if st.sidebar.button("News"):
    navigate_to("News")
if st.sidebar.button("Transaction"):
    navigate_to("Transaction")

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

page = st.session_state.current_page

# Function to load stock data
@st.cache_data
def load_data(ticker, start="2020-01-01", end="2023-12-31"):
    data = yf.download(ticker, start=start, end=end)
    data.reset_index(inplace=True)
    return data

# Function to load index data
@st.cache_data
def load_index_data():
    indices = {'^GSPC': 'S&P 500', '^DJI': 'Dow Jones', '^IXIC': 'NASDAQ'}
    data = {}
    for symbol, name in indices.items():
        df = yf.download(symbol, start="2023-01-01", end="2023-12-31")
        data[name] = df['Close'].iloc[-1].to_string(index=False)
    return pd.DataFrame(list(data.items()), columns=['Index', 'Current Value'])


if 'transactions' not in st.session_state:
    st.session_state.transactions = []


# Function to add transaction
def add_transaction(ticker, quantity, price, date, transaction_type):
    st.session_state.transactions.append({
        'ticker': ticker,
        'quantity': quantity,
        'price': price,
        'date': date,
        'type': transaction_type
    })

# Function to calculate gains/losses
def calculate_gains_losses():
    gains_losses = {}
    for transaction in st.session_state.transactions:
        ticker = transaction['ticker']
        if ticker not in gains_losses:
            gains_losses[ticker] = 0
        
        if transaction['type'] == 'buy':
            gains_losses[ticker] -= transaction['quantity'] * transaction['price']
        else:  # sell
            gains_losses[ticker] += transaction['quantity'] * transaction['price']
    
    return gains_losses

# ---------------------

# Home page
if page == "Home":
    st.markdown("Welcome to the Stock Information App!")
    st.write("This app is designed to provide you with real-time insights into the stock market, including detailed information about individual stocks, ETFs, and major market indices. Whether you're a seasoned investor or just starting your financial journey, our user-friendly interface allows you to easily track your investments, analyze market trends, and stay updated with the latest financial news.")
    st.title('Stock Information')
    stock_symbol = st.text_input("Enter Stock Symbol", "AAPL")
    if stock_symbol:
        data = load_data(stock_symbol)
        st.subheader(f"Latest Data for {stock_symbol}")
        st.write(data.tail())

# Stock Graph page
elif page == "Stock Graph":
    st.title("Real-Time Line Chart")

    # Create a placeholder for the chart
    chart_placeholder = st.empty()

    # Create initial data
    data = pd.DataFrame({'time': [], 'value': []})

    # Function to update data
    def update_data():
        new_time = pd.Timestamp.now()
        new_value = np.random.randn()
        return pd.DataFrame({'time': [new_time], 'value': [new_value]})

    # Main loop for real-time updates
    while True:
        # Add new data
        data = pd.concat([data, update_data()], ignore_index=True)
    
    # Keep only the last 100 points
        data = data.tail(100)
    
    # Update the chart
        chart_placeholder.line_chart(data.set_index('time'))
    
    # Wait for a short time before the next update
        time.sleep(0.1)


# Market Indices page
elif page == "Market Indices":
    st.title('Market Indices')
    indices_data = load_index_data()
    st.write(indices_data)
        
    # Create a bar chart for indices
    fig = go.Figure(data=[go.Bar(x=indices_data['Index'], y=indices_data['Current Value'])])
    fig.update_layout(title='Current Values of Major Indices',
                        xaxis_title='Index',
                        yaxis_title='Value')
    st.plotly_chart(fig)


# ETF page
elif page == "ETF Information":
    st.header("ETF Information")

    etf_ticker = st.text_input("Enter ETF ticker symbol:", "SPY").upper()

    if etf_ticker:
        try:
            etf = yf.Ticker(etf_ticker)
            info = etf.info

            st.subheader(f"{info.get('longName', etf_ticker)} ({etf_ticker})")

            
            dividend_rate = info.get('dividendRate', None)
            trailing_annual_dividend_rate = info.get('trailingAnnualDividendRate', None)
            dividend_yield = info.get('dividendYield', None)

            if dividend_rate is not None and isinstance(dividend_rate, (int, float)):
                st.write(f"Forward Annual Dividend Rate: ${dividend_rate:.2f}")
            elif trailing_annual_dividend_rate is not None and isinstance(trailing_annual_dividend_rate, (int, float)):
                st.write(f"Trailing Annual Dividend Rate: ${trailing_annual_dividend_rate:.2f}")
            else:
                st.write("Dividend Rate: Information not available")

            if dividend_yield is not None and isinstance(dividend_yield, (int, float)):
                st.write(f"Dividend Yield: {dividend_yield:.2%}")
            else:
                st.write("Dividend Yield: Information not available")


            st.write(f"Net Assets: ${info.get('totalAssets', 0):,.0f}")

            st.subheader("Price and Performance")
            col1, col2 = st.columns(2)
            
            current_price = info.get('regularMarketPrice', info.get('regularMarketOpen', 'N/A'))
            col1.metric("Current Price", f"${current_price:.2f}" if isinstance(current_price, (int, float)) else current_price)

            ytd_return = info.get('ytdReturn', 'N/A')
            formatted_ytd_return = f"{ytd_return:.2f}%" if isinstance(ytd_return, (int, float)) else ytd_return
            col2.metric("YTD Return", formatted_ytd_return)
            
            st.subheader("Historical Price Chart")
            history = etf.history(period="1y")
            st.line_chart(history['Close'])

        except Exception as e:
            st.error(f"An error occurred while fetching data for {etf_ticker}: {str(e)}")
            st.write("Please check the ticker symbol and try again.")
        

# News page
elif page == "News":
    def show_recent_news():
        st.subheader("Recent Financial News")
        
        # S&P 500 as a proxy for general market news
        news = yf.Ticker("^GSPC").news  
        
        for article in news[:5]: 
            st.markdown(f"**{article['title']}**")
            st.write(article['link'])
            st.write("---")
    
    show_recent_news()


elif page == "Transaction":
    st.header("Transaction")
    
    # Add transaction
    st.subheader("Add Transaction")
    ticker = st.text_input("Stock Ticker")
    quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
    price = st.number_input("Price per Share", min_value=0.0, step=0.01)
    date = st.date_input("Transaction Date")
    transaction_type = st.selectbox("Transaction Type", ["buy", "sell"])
    
    if st.button("Add Transaction"):
        add_transaction(ticker.upper(), quantity, price, date, transaction_type)
    
    # Display transactions
    st.subheader("Transaction History")
    transactions_df = pd.DataFrame(st.session_state.transactions)
    if not transactions_df.empty:
        st.dataframe(transactions_df)
    
    # Calculate and display gains/losses
    st.subheader("Gains/Losses Summary")
    gains_losses = calculate_gains_losses()
    for ticker, amount in gains_losses.items():
        st.write(f"{ticker}: {'Gain' if amount >= 0 else 'Loss'} of {abs(amount):.2f} USD")


