# file to download 
import yfinance as yf
gspc = yf.download(tickers='^GSPC', start='2010-01-01', end='2023-12-31', interval='1d')
gspc.to_csv('gspc.csv')
