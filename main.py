import datetime as dt
import csv
import copy
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import ipywidgets as widgets
import pytz
import random
import yfinance as yf
from calendar import monthrange
from datetime import datetime
from dateutil.relativedelta import relativedelta
from IPython.display import clear_output, Markdown
from prettytable import PrettyTable


# Constants
EPS = 1e-6
BUY = 'BUY'
SELL = 'SELL'

# Ticker of the market you want to compare it to for the alpha and beta, https://finance.yahoo.com/lookup/
PRICES_FILE = f'{os.path.dirname(os.path.abspath(__file__))}/px_etf.csv'
TRANSACTIONS_FILE = f'{os.path.dirname(os.path.abspath(__file__))}/tx_etf.csv'
MARKET_TICKER = '^GSPC'
MARKET_FILE = 'gspc.csv' # In case yfinance doesnt work, a csv file with the market data will be used instead

NUM_OF_X_TICKS = 30
RISK_FREE_RATE = 0.02

# Read prices and available Tickers
all_tickers = [] # List of all tickers which appear in PRICES_FILE
update_dates = [] # List of all dates which appear in PRICES_FILE
price_daily = {} # Nested dictionary of prices for each ticker on each day
tickers_interested = [] # List of tickers which the user is interested in
MARKET_DATA = None

# Classes
class Buy():
	"""
	Represents a buy order for a stock.
	This class holds the details of a buy order, including the ticker symbol of the stock, the price per share, and the quantity of shares.

	Attributes:
		ticker: A string representing the ticker symbol of the stock.
		price: A float representing the price per share.
		qty: An integer representing the quantity of shares.

	Methods:
		cost: Returns the total cost of the buy order.
	"""
	def __init__(self, ticker: str, price: float, qty: int):
		"""
		Initializes a Buy instance with a ticker symbol, price per share, and quantity of shares.

		Args:
			ticker: A string representing the ticker symbol of the stock.
			price: A float representing the price per share.
			qty: An integer representing the quantity of shares.
		"""
		self.ticker = ticker
		self.price = price
		self.qty = qty

	@property
	def cost(self):
		"""
		Returns the total cost of the buy order.
		This method multiplies the price per share by the quantity of shares to calculate the total cost.

		Returns:
			A float representing the total cost of the buy order.
		"""
		return self.price * self.qty

class Sell():
	"""
	Represents a sell order for a stock.
	This class holds the details of a sell order, including the ticker symbol of the stock, the price per share,
			the quantity of shares, the profit made, and the cost of the shares.

	Attributes:
		ticker: A string representing the ticker symbol of the stock.
		price: A float representing the price per share.
		qty: An integer representing the quantity of shares.
		profit: A float representing the profit made from the sell order.
		cost: A float representing the cost of the shares.
	"""

	def __init__(self, ticker: str, price: float, qty: int, profit: float, cost: float):
		"""
		Initializes a Sell instance with a ticker symbol, price per share, quantity of shares, profit, and cost.

		Args:
			ticker: A string representing the ticker symbol of the stock.
			price: A float representing the price per share.
			qty: An integer representing the quantity of shares.
			profit: A float representing the profit made from the sell order.
			cost: A float representing the cost of the shares.
		"""
		self.ticker = ticker
		self.price = price
		self.qty = qty
		self.profit = profit
		self.cost = cost

class TradeHistory():
	"""
	Represents a history of trade orders.
	This class holds the history of buy and sell orders, organized by date and ticker symbol.

	Attributes:
		buy_history: A nested dictionary where the first level keys are years,
				the second level keys are months, the third level keys are days,
				and the fourth level keys are ticker symbols.
				The values are Buy instances.
		sell_history: A nested dictionary where the first level keys are years,
				the second level keys are months, the third level keys are days, and the fourth level keys are ticker symbols.
				The values are Sell instances.

	Methods:
		add_buy: Adds a buy order to the history.
		add_sell: Adds a sell order to the history.
		get_buy: Retrieves a buy order from the history.
		get_sell: Retrieves a sell order from the history.
		sum_profits_costs: Calculates the total profits and costs for a given list of dates and ticker symbols.
	"""
	def __init__(self):
		"""
		Initializes a TradeHistory instance with empty buy and sell histories.
		"""
		self.buy_history = {}
		self.sell_history = {}

	def add_buy(self, year: int, month: int, day: int, buy: Buy) -> None:
		"""
		Adds a buy order to the history.

		Args:
			year: An integer representing the year.
			month: An integer representing the month.
			day: An integer representing the day.
			buy: A Buy instance representing the buy order.
		"""
		self.buy_history.setdefault(year, {}).setdefault(month, {}).setdefault(day, {}).setdefault(buy.ticker, buy)

	def add_sell(self, year: int, month: int, day: int, sell: Sell) -> None:
		"""
		Adds a sell order to the history.

		Args:
			year: An integer representing the year.
			month: An integer representing the month.
			day: An integer representing the day.
			sell: A Sell instance representing the sell order.
		"""
		self.sell_history.setdefault(year, {}).setdefault(month, {}).setdefault(day, {}).setdefault(sell.ticker, sell)

	def get_buy(self, year: int, month: int, day: int, ticker: str) -> Buy:
		"""
		Retrieves a buy order from the history.

		Args:
			year: An integer representing the year.
			month: An integer representing the month.
			day: An integer representing the day.
			ticker: A string representing the ticker symbol.

		Returns:
			A Buy instance representing the buy order, or None if no such order exists.
		"""
		try: 
			return self.buy_history[year][month][day][ticker]
		except KeyError:
			return None

	def get_sell(self, year: int, month: int, day: int, ticker: str) -> Sell:
		"""
		Retrieves a sell order from the history.
		This method takes a year, month, day, and ticker symbol, and returns the corresponding sell order from the history. If no such order exists, it returns None.

		Args:
			year: An integer representing the year.
			month: An integer representing the month.
			day: An integer representing the day.
			ticker: A string representing the ticker symbol.

		Returns:
			A Sell instance representing the sell order, or None if no such order exists.
		"""
		try: 
			return self.sell_history[year][month][day][ticker]
		except KeyError:
			return None
			
	def sum_profits_costs(self, dates: [(int, int, int)], tickers: [str] = all_tickers) -> (float, float):
		"""
		Calculates the total profits and costs for a given list of dates and ticker symbols.
		This method takes a list of dates and a list of ticker symbols, and calculates the total profits and costs from all sell orders on those dates for those ticker symbols.

		Args:
			dates: A list of tuples, where each tuple contains three integers representing a year, month, and day.
			tickers: A list of strings representing ticker symbols. Defaults to all ticker symbols.

		Returns:
			A tuple containing two floats. The first float is the total profits, and the second float is the total costs.
		"""
		profits = 0
		costs = 0
		for year, month, day in dates:
			for ticker in tickers:
				sell = self.get_sell(year, month, day, ticker)
				if sell is not None:
					profits += sell.profit
					costs += sell.cost
		return profits, costs

class Asset():
	"""
	Represents the holdings of an asset.
	This class holds the details of an asset, including the quantity of shares owned, the cost of the shares,
	the current value of the shares, and the cash made from the shares.

	Attributes:
		qty: An integer representing the quantity of shares owned.
		cost: A float representing the cost of the shares.
		value: A float representing the current value of the shares.
		cash: A float representing the cash made from the shares (realized profit). 

	Properties:
		avg_price: Returns the average price per share.
		profit: Returns the unrealized profits from the shares.
	"""
	def __init__(self):
		"""
		Initializes a Ticker instance with zero quantity, cost, value, and cash.
		"""
		self.qty = 0 # How many shares of this ticker are owned
		self.cost = 0 # How much cash was spent on this ticker
		self.value = 0 # How much the ticker is worth right now
		self.cash = 0 # How much cash was made from this ticker, all buys and sells
	
	@property
	def avg_price(self):
		"""
		Returns the average price per share.

		This property calculates the average price per share by dividing the cost by the quantity.
		If the quantity is zero, it returns zero.

		Returns:
			A float representing the average price per share.
		"""
		return self.cost / self.qty if self.qty != 0 else 0
	
	@property
	def profit(self):
		"""
		Returns the profit made from the shares.
		This property calculates the profit by subtracting the cost from the value.

		Returns:
			A float representing the profit made from the shares.
		"""
		return self.value - self.cost

class Inventory():
	"""
	Represents an inventory of assets.
	This class holds a dictionary of assets, where the keys are ticker symbols and the values are Asset instances.

	Attributes:
		assets: A dictionary where the keys are strings representing ticker symbols and the values are Asset instances.

	Methods:
		value: Returns the total value of the specified assets.
		profits: Returns the total profit of the specified assets.
		costs: Returns the total cost of the specified assets.
		cash: Returns the total cash of the specified assets.
	"""
	def __init__(self, tickers_interested: [str] = all_tickers):
		"""
		Initializes an Inventory instance with a dictionary of assets.
		"""
		self.assets = {
			ticker: Asset() for ticker in all_tickers
		}

	def value(self, tickers: [str] = all_tickers) -> float:
		"""
		Returns the total value of the specified assets.
		This method takes a list of ticker symbols and returns the sum of the values of the corresponding assets.

		Args:
			tickers: A list of strings representing ticker symbols. Defaults to all ticker symbols.

		Returns:
			A float representing the total value of the specified assets.
		"""
		return sum([self.assets[ticker].value for ticker in tickers])
	
	def profits(self, tickers: [str] = all_tickers) -> float:
		"""
		Returns the total profit of the specified assets.

		This method takes a list of ticker symbols and returns the sum of the profits of the corresponding assets.

		Args:
			tickers: A list of strings representing ticker symbols. Defaults to all ticker symbols.

		Returns:
			A float representing the total profit of the specified assets.
		"""
		return sum([self.assets[ticker].profit for ticker in tickers])
	
	def costs(self, tickers: [str] = all_tickers) -> float:
		"""
		Returns the total cost of the specified assets.
		This method takes a list of ticker symbols and returns the sum of the costs of the corresponding assets.

		Args:
			tickers: A list of strings representing ticker symbols. Defaults to all ticker symbols.

		Returns:
			A float representing the total cost of the specified assets.
		"""
		return sum([self.assets[ticker].cost for ticker in tickers])
	
	def cash(self, tickers: [str] = all_tickers) -> float:
		"""
		Returns the total cash of the specified assets.
		This method takes a list of ticker symbols and returns the sum of the cash of the corresponding assets.

		Args:
			tickers: A list of strings representing ticker symbols. Defaults to all ticker symbols.

		Returns:
			A float representing the total cash of the specified assets.
		"""
		return sum([self.assets[ticker].cash for ticker in tickers])

class InventorySnapshot():
	"""
	Represents a snapshot of an inventory.
	This class holds a dictionary of inventory snapshots, where the keys are dates and the values are Inventory instances.

	Attributes:
		snapshot: A dictionary where the keys are tuples representing dates and the values are Inventory instances.

	Methods:
		get: Returns the Inventory instance for the specified date.
		take_snapshot: Takes a snapshot of the specified Inventory instance and stores it with the specified date.
		get_closest_inventory: Returns the Inventory instance for the closest available date to the specified date.
	"""
	def __init__(self):
		"""
		Initializes an InventorySnapshot instance with an empty dictionary of snapshots.
		"""
		self.snapshot = {}

	def get(self, year: int, month: int, day: int) -> Inventory:
		"""
		Returns the Inventory instance for the specified date.
		This method takes a year, month, and day, and returns the corresponding Inventory instance from the snapshot. 
		If no such instance exists, it returns None.

		Args:
			year: An integer representing the year.
			month: An integer representing the month.
			day: An integer representing the day.

		Returns:
			An Inventory instance for the specified date, or None if no such instance exists.
		"""
		try:
			return self.snapshot[year][month][day]
		except KeyError:
			return None

	def take_snapshot(self, year: int, month: int, day: int, inventory: Inventory):
		"""
		Takes a snapshot of the specified Inventory instance and stores it with the specified date.
		This method takes a year, month, day, and Inventory instance,
				and stores the Inventory instance in the snapshot with the specified date.

		Args:
			year: An integer representing the year.
			month: An integer representing the month.
			day: An integer representing the day.
			inventory: An Inventory instance to be stored in the snapshot.
		"""
		self.snapshot.setdefault(year, {}).setdefault(month, {}).setdefault(day, copy.deepcopy(inventory))
	
	def get_closest_inventory(self, year: int, month: int, day: int) -> Inventory:
		"""
		Returns the Inventory instance for the closest available date to the specified date.
		This method takes a year, month, and day,
				and returns the Inventory instance from the snapshot that isclosest to the specified date.

		Args:
			year: An integer representing the year.
			month: An integer representing the month.
			day: An integer representing the day.

		Returns:
			An Inventory instance for the closest available date to the specified date.
		"""
		year, month, day = get_closest_available_date(year, month, day, self.snapshot)
		try:
			return self.snapshot[year][month][day]
		except KeyError:
			return None

# Date utilities
def get_date(first_cell: str) -> (int, int, int):
	"""
	Converts a date string to year, month, and day.
	This function takes a date string in the format 'YYYY-MM-DD' and splits it into year, month, and day.

	Args:
		first_cell: A string representing a date in the format 'YYYY-MM-DD'.

	Returns:
		A tuple of three integers representing the year, month, and day, respectively. For example:
		('2020-01-02') -> (2020, 1, 2)

	Raises:
		ValueError: If the input string is not in the correct format,
				a ValueError will be raised when trying to unpack the values.
	"""
	year, month, day = first_cell.split('-')
	return int(year), int(month), int(day)

def get_first_month_day(d: dict) -> (int, int):
	"""
	Returns the first day of the first month in the dictionary.
	This function takes a nested dictionary in the format {month: {day: {ticker: price}}},
			and returns the first day of the first month.

	Args:
		d: A nested dictionary where the first level keys are months, the second level keys are days,
				and the values are dictionaries mapping tickers to prices.

	Returns:
		A tuple of two integers representing the first month and the first day in the dictionary, respectively. For example:
		{1: {2: {'AAPL': 150}}} -> (1, 2)

	Raises:
		ValueError: If the input dictionary is empty, a ValueError will be raised when trying to find the minimum key.
	"""
	return min(d.keys()), min(d[min(d.keys())].keys())

def get_closest_available_date(year: int, month: int, day: int, d: dict) -> (int, int, int):
	"""
	Returns the closest available date in the dictionary which is less than or equal to the given date.
		This function takes a year, month, and day, and a nested dictionary in the format {year: {month: {day: {ticker: price}}}}.
		It finds the closest date in the dictionary that is less than or equal to the given date.

	Args:
		year: An integer representing the year.
		month: An integer representing the month.
		day: An integer representing the day.
		d: A nested dictionary where the first level keys are years, the second level keys are months,
				the third level keys are days, and the values are dictionaries mapping tickers to prices.

	Returns:
		A tuple of three integers representing the closest year, month, and day in the dictionary that is less than
				or equal to the given date. For example:
		2020, 2, 4, {2020: {1: {2: {'AAPL': 150}}}} -> (2020, 1, 2)

	Raises:
		ValueError: If the input dictionary is empty, a ValueError will be raised when trying to find the maximum key.
	"""
	year = max(key for key in map(int, d.keys()) if key <= year)
	try:
		month = max(key for key in map(int, d[year].keys()) if key <= month)
	except Exception:
		year = max(key for key in map(int, d.keys()) if key <= year)
		year = year - 1
		month = max(key for key in map(int, d[year].keys()) if key <= 12)
	try:
		day = max(key for key in map(int, d[year][month].keys()) if key <= day)
	except Exception:
		month = max(key for key in map(int, d[year].keys()) if key <= month)
		month = month - 1
		day = max(key for key in map(int, d[year][month].keys()) if key <= monthrange(year, month)[1])
	return year, month, day

def get_all_dates(
		year_start: int, month_start: int, day_start: int,
		year_end: int, month_end: int, day_end: int) -> [(int, int, int)]:
	"""
	Returns a list of all dates between the given start and end dates.
	This function takes a start date and an end date, and returns a list of all dates in between (inclusive).
	Each date is represented as a tuple of year, month, and day.

	Args:
		year_start: An integer representing the start year.
		month_start: An integer representing the start month.
		day_start: An integer representing the start day.
		year_end: An integer representing the end year.
		month_end: An integer representing the end month.
		day_end: An integer representing the end day.

	Returns:
		A list of tuples, where each tuple contains three integers representing a year, month, and day. For example:
		2020, 1, 1, 2020, 1, 3 -> [(2020, 1, 1), (2020, 1, 2), (2020, 1, 3)]

	Raises:
		ValueError: If the start date is later than the end date,
				a ValueError will be raised when trying to append dates to the list.
	"""
	date_start = datetime(year_start, month_start, day_start)
	date_end = datetime(year_end, month_end, day_end)
	dates = []
	while date_start <= date_end:
		dates.append((date_start.year, date_start.month, date_start.day))
		date_start += relativedelta(days=1)
	return dates

def get_all_dates_year(year: int, d: dict) -> [(int, int, int)]:
	"""
	Returns a list of all dates in the given year that are present in the dictionary.
	This function takes a year and a nested dictionary in the format {year: {month: {day: {ticker: price}}}}. 
	It finds the first and last available dates in the given year in the dictionary,
			and returns a list of all dates in between.

	Args:
		year: An integer representing the year.
		d: A nested dictionary where the first level keys are years, the second level keys are months,
				the third level keys are days, and the values are dictionaries mapping tickers to prices.

	Returns:
		A list of tuples, where each tuple contains three integers representing a year, month, and day. For example:
		2020, {2020: {1: {2: {'AAPL': 150}}}} -> [(2020, 1, 2), ..., (2020, 12, 31)]

	Raises:
		KeyError: If the given year is not in the dictionary, a KeyError will be raised when trying to access d[year].
		ValueError: If there are no dates in the given year in the dictionary,
				a ValueError will be raised when trying to find the first and last available dates.
	"""
	month_start, day_start = get_first_month_day(d[year])
	year_end, month_end, day_end = get_closest_available_date(year, 12, 31, d)
	return get_all_dates(year, month_start, day_start, year_end, month_end, day_end)

# Data processing
def get_daily_price(year: int, month: int, day: int, ticker: str) -> float:
	"""
	Returns the end-of-day price of the specified ETF on the specified date.
	This function takes a year, month, day, and ETF ticker symbol,
			and returns the end-of-day price of the specified ETF on the specified date.

	Args:
		year: An integer representing the year.
		month: An integer representing the month.
		day: An integer representing the day.
		ticker: A string representing the ETF ticker symbol.

	Returns:
		A float representing the end-of-day price of the specified ETF on the specified date.
	"""
	return price_daily[year][month][day][ticker]

def process_trade(year: str, month: str, day: str, ticker: str, qty: int, order_type: str) -> None:
	"""
	Processes a trade by updating the current inventory of assets and calculating realized profits if necessary.
	This function takes a year, month, day, asset ticker symbol, quantity, and order type,
			and updates the current inventory of asset accordingly.
	If the order type is a sell, it also calculates the realized profits.

	Args:
		year: A string representing the year.
		month: A string representing the month.
		day: A string representing the day.
		ticker: A string representing the ETF ticker symbol.
		qty: An integer representing the quantity of the ETF.
		order_type: A string representing the order type (either 'BUY' or 'SELL').

	Returns:
		None
	"""
	eod_price = get_daily_price(year, month, day, ticker)
	curr_ticker = inventory_curr.assets[ticker]
	if order_type == BUY:
		trades.add_buy(year, month, day, Buy(ticker, eod_price, qty))
		curr_ticker.qty += qty
		curr_ticker.cost += eod_price * qty
		curr_ticker.cash -= (eod_price * qty)
	else:
		temp_avg_price = curr_ticker.avg_price
		trades.add_sell(
			year, month, day, Sell(ticker, eod_price, qty, (eod_price - temp_avg_price) * qty, temp_avg_price * qty))
		curr_ticker.cash += (eod_price * qty)
		curr_ticker.cost -= temp_avg_price * qty
		curr_ticker.qty -= qty

def calc_unrealized_profits(year: int, month: int, day: int) -> None:
	"""
	Updates the unrealized profits of the inventory.
	This function takes a year, month, and day, and updates the unrealized profits of the inventory for each ETF ticker symbol. The unrealized profit for each ticker is calculated as the end-of-day price times the quantity of the ETF in the current inventory.

	Args:
		year: An integer representing the year.
		month: An integer representing the month.
		day: An integer representing the day.

	Returns:
		None
	"""
	for ticker in all_tickers:
		eod_price = get_daily_price(year, month, day, ticker)
		curr_ticker = inventory_curr.assets[ticker]
		curr_ticker.value = eod_price * curr_ticker.qty

def daily_update(year: int, month: int, day: int) -> None:
	"""
	Performs a daily update of the inventory.
	This function takes a year, month, and day, and performs a daily update of the inventory.
	It first calculates the unrealized profits for the current inventory,
			and then takes a snapshot of the current inventory.

	Args:
		year: An integer representing the year.
		month: An integer representing the month.
		day: An integer representing the day.

	Returns:
		None
	"""
	calc_unrealized_profits(year, month, day)
	inventory_snapshot.take_snapshot(year, month, day, inventory_curr)

# Utilities
def get_stock_price_yfinance(
		year_start: int, month_start: int, day_start:int,
		year_end: int, month_end: int, day_end: int) -> pd.Series:
	"""
	Fetches the stock price for a given ticker and date range using the yfinance library.
	This function takes a start and end date,
			and returns a pandas Series of the closing prices for each day in the date range.
	If the yfinance library fails to fetch the data, it reads the data from a local CSV file.
	You can access the closing price for a specific date by indexing the Series with a string in the format 'YYYY-MM-DD'.
	That is .loc['YYYY-MM-DD'].
	Args:
		year_start: An integer representing the start year.
		month_start: An integer representing the start month.
		day_start: An integer representing the start day.
		year_end: An integer representing the end year.
		month_end: An integer representing the end month.
		day_end: An integer representing the end day.

	Returns:
		A pandas Series of the closing prices for each day in the date range.
	"""
	tz = pytz.timezone('UTC')
	start_date = tz.localize(datetime.combine(dt.date(year=year_start, month=month_start, day=day_start), datetime.min.time()))
	end_date = tz.localize(datetime.combine(dt.date(year=year_end, month=month_end, day=day_end), datetime.max.time()))
	return MARKET_DATA.loc[start_date:end_date]

def get_profits_cost(dates: [(int, int, int)], tickers: [str]=all_tickers) -> \
		(float, float, float, float, float, float, float, float, float):
	"""
	Calculates the total returns for the specified dates and tickers.
	This function takes a list of dates and a list of ticker symbols,
			and calculates the total returns for these dates and tickers.
	The total returns are calculated as the sum of the realized and unrealized profits divided by the total cost,
			expressed as a percentage.

	Args:
		dates: A list of tuples, where each tuple represents a date as (year, month, day).
		tickers: A list of strings representing the ticker symbols. Defaults to all tickers.

	Returns:
		A tuple of nine floats.
		The first float represents the realized profits,
				the second float represents the realized cost,
				the third float represents the realized profits in percentage,
				the fourth float represents the unrealized cost,
				the fifth float represents the unrealized profits,
				the sixth float represents the unrealized profits in percentage,
				the seventh float represents the total profits,
				the eighth float represents the total cost,
				and the ninth float represents the total returns expressed as a percentage.
	"""
	realized_profits, realized_cost = trades.sum_profits_costs(dates, tickers=tickers)
	realized_profits_percent = realized_profits / realized_cost * 100 if realized_cost > EPS else 0

	inventory = inventory_snapshot.get_closest_inventory(*dates[-1])
	unrealized_profits, unrealized_cost = inventory.profits(tickers=tickers), inventory.costs(tickers=tickers)
	unrealized_profits_percent = unrealized_profits / unrealized_cost * 100 if unrealized_cost > EPS else 0

	total_profits = realized_profits + unrealized_profits
	total_cost = realized_cost + unrealized_cost
	total_profits_percent = total_profits / total_cost * 100 if total_cost > EPS else 0

	return realized_profits, realized_cost, realized_profits_percent, \
		unrealized_profits, unrealized_cost, unrealized_profits_percent, \
		total_profits, total_cost, total_profits_percent

def get_returns_timespan(
		dates: [(int, int, int)],
		tickers: [str]=all_tickers) -> ([float], [float]):
	"""
	Calculates the returns for a given timespan for the specified market and tickers.
	This function takes a market ticker, a list of dates, and a list of ticker symbols,
			and calculates the returns for these tickers and the market over the specified dates.
	The returns are calculated as the difference in market prices between each consecutive pair of dates.

	Args:
		market: A string representing the market ticker.
		dates: A list of tuples, where each tuple represents a date as (year, month, day).
		tickers: A list of strings representing the ticker symbols. Defaults to all tickers.

	Returns:
		A tuple of two lists of floats. The first list represents the returns for the tickers,
				and the second list represents the returns for the market.
	"""
	market_prices = get_stock_price_yfinance(*dates[0], *dates[-1])
	ret_market = []
	ret = []
	prev_date = None
	for date in dates:
		inventory = inventory_snapshot.get(*date)
		if inventory:
			try:
				market_now = market_prices.loc[f'{date[0]}-{str(date[1]).zfill(2)}-{str(date[2]).zfill(2)}']
				if prev_date:
					_, _, _, _, _, _, _ , _, r = get_profits_cost([prev_date, date], tickers)
					market_prev = market_prices.loc[f'{str(prev_date[0]).zfill(4)}-{str(prev_date[1]).zfill(2)}-{str(prev_date[2]).zfill(2)}']
					ret.append(r)
					ret_market.append(market_now - market_prev)
				prev_date = date
			except Exception as e:
				pass
	return ret, ret_market

def get_alpha(dates: [(int, int, int)], tickers: [str]=all_tickers):
	"""
	Calculates the alpha for the specified dates and tickers.
	This function takes a list of dates and a list of ticker symbols,
			and calculates the alpha for these tickers over the specified dates.
	The alpha is calculated as the difference between the returns of the tickers and the risk-free rate,
			minus the product of the beta and the difference between the total return of the market and the risk-free rate.
	Alpha = R - R_f - beta (R_m-R_f)
		R represents the portfolio return
		R_f represents the risk-free rate of return
		Beta represents the systematic risk of a portfolio
		R_m represents the market return, per a benchmark

	Args:
		dates: A list of tuples, where each tuple represents a date as (year, month, day).
		tickers: A list of strings representing the ticker symbols. Defaults to all tickers.

	Returns:
		A float representing the alpha for the specified dates and tickers.
	"""
	ret_ticker, ret_market = get_returns_timespan(dates, tickers=tickers_interested)
	market_prices = get_stock_price_yfinance(*dates[0], *dates[-1])
	total_return_of_market = (market_prices.iloc[-1] - market_prices.iloc[0]) / market_prices.iloc[0] * 100
	beta = get_beta(ret_market, ret_market)
	_, _, _, _, _, _, _ , _, returns = get_profits_cost(dates, tickers=tickers)
	return returns - RISK_FREE_RATE - beta * (total_return_of_market - RISK_FREE_RATE)

def get_beta(ret_ticker: [float], ret_market: [float]):
	"""
	Calculates the beta between the returns of a ticker and the market.
	This function takes two lists of floats representing the returns of a ticker and the market, and calculates the beta between them. The beta is calculated as the covariance between the returns of the ticker and the market divided by the variance of the market returns.

	Args:
		ret_ticker: A list of floats representing the returns of the ticker.
		ret_market: A list of floats representing the returns of the market.

	Returns:
		A float representing the beta between the returns of the ticker and the market.
	"""
	covariance = np.cov(ret_ticker, ret_market)[0, 1]
	variance = np.var(ret_market)
	beta = covariance / variance
	return beta

def get_std(ret_ticker: [float]):
	"""
	Calculates the standard deviation of the returns of a ticker.
	This function takes a list of floats representing the returns of a ticker,
			and calculates the standard deviation of these returns.

	Args:
		ret_ticker: A list of floats representing the returns of the ticker.

	Returns:
		A float representing the standard deviation of the returns of the ticker.
	"""
	ret_ticker = np.array(ret_ticker)
	return np.std(ret_ticker)

def get_sharpe_ratio(ret_ticker: [float]):
	"""
	Calculates the Sharpe ratio of the returns of a ticker.

	This function takes a list of floats representing the returns of a ticker,
			and calculates the Sharpe ratio of these returns.
	The Sharpe ratio is calculated as the difference between the average return and the risk-free rate,
			divided by the volatility of the returns.
	Sharpe Ratio = (R_x - R_f) / std(R_x)
		R_x = Expected portfolio return (actual return)
		R_f = Risk-free rate of return
		std(R_x) = Standard deviation of portfolio return (or, volatility)

	Args:
		ret_ticker: A list of floats representing the returns of the ticker.

	Returns:
		A float representing the Sharpe ratio of the returns of the ticker.
	"""
	returns_array = np.array(ret_ticker)
	average_return = np.mean(returns_array)
	volatility = np.std(returns_array)
	if volatility == 0:
		volatility = 1
		print('std is zero, cannot calculate Sharpe ratio. Used 1 for std instead.')
	return (average_return - RISK_FREE_RATE) / volatility

# Plottings functions
def date_label(year: int, month: int, day: int) -> str:
	"""
	Formats a date as a string in the format 'YYYY-MM-DD'.
	This function takes three integers representing a year, a month, and a day,
			and returns a string representing the date in the format 'YYYY-MM-DD'.

	Args:
		year: An integer representing the year.
		month: An integer representing the month.
		day: An integer representing the day.

	Returns:
		A string representing the date in the format 'YYYY-MM-DD'.
	"""
	return f'{year}-{month}-{day}'

def print_profit_table(year_start: str, month_start: str, year_end: str, month_end: str) -> None:
	"""
	Prints a table of the profits for a given range of dates.
	This function takes a start year and month, and an end year and month, 
			and prints a table of the profits for each month in this range.
	The table includes the realized and unrealized profits, total profits, cash, portfolio value, assets,
			standard deviation, beta, alpha, and Sharpe ratio.

	Args:
		year_start: A string representing the start year.
		month_start: A string representing the start month.
		year_end: A string representing the end year.
		month_end: A string representing the end month.

	Returns:
		None. The function prints the table to the console.
	"""
	def row_values(dates: [(int, int, int)]) -> \
			(float, float, float, float, float, float, float, float, float, float, float, float, float):
		rp, rc, rpp, up, uc, upp, tp, tc, tpp = get_profits_cost(dates, tickers=tickers_interested)

		inventory = inventory_snapshot.get_closest_inventory(*all_dates[-1])

		cash = inventory.cash(tickers=tickers_interested)
		portfolio = inventory.value(tickers=tickers_interested)
		assets = cash + portfolio

		ret_ticker, ret_market = get_returns_timespan(all_dates, tickers=tickers_interested)

		std = get_std(ret_ticker)
		beta = get_beta(ret_ticker, ret_market)
		alpha = get_alpha(dates, tickers=tickers_interested)
		sharpe_ratio = get_sharpe_ratio(ret_ticker)

		return rp, rc, rpp, up, uc, upp, tp, tc, tpp, cash, portfolio, assets, std, beta, alpha, sharpe_ratio
	
	def add_row(dates: [(int, int, int)], label: str, table, divider: bool) -> None:
		rp, _, rpp, up, _, upp, tp, _, tpp, cash, portfolio, assets, std, beta, alpha, sharpe_ratio = row_values(dates)
		table.add_row([
			label,

			'%.2f' % rp,
			'%.4f' % rpp,

			'%.2f' % up,
			'%.4f' % upp,

			'%.2f' % tp,
			'%.4f' % tpp,

			'%.2f' % cash,
			'%.2f' % portfolio,
			'%.2f' % assets,

			'%.2f' % std,
			'%.4f' % beta,
			'%.4f' % alpha,
			'%.4f' % sharpe_ratio,
		], divider=divider)
	
	global out
	year_start, month_start, year_end, month_end = map(int, [year_start, month_start, year_end, month_end])
	year_end, month_end, _ = get_closest_available_date(year_end, month_end, 31, inventory_snapshot.snapshot)
	for year in range(year_start, year_end + 1):
		annual_table = PrettyTable()
		annual_table.title = str(year)
		annual_table.field_names = [
			'Month',

			'Realized profits',
			'Realized profits %',

			'Unrealized profits',
			'Unrealized profits %',

			'Total profits',
			'Total profits %',

			'Cash',
			'Portfolio',
			'Assets',

			'Std',
			'Beta',
			'Alpha',
			'Sharpe Ratio'
		]

		for month in range(month_start if year == year_end else 1, month_end + 1 if year == year_end else 13):
			day_start = list(inventory_snapshot.snapshot[year][month])[0]
			all_dates = get_all_dates(year, month, day_start, year, month, monthrange(year, month)[1])
			add_row(all_dates, month, annual_table, month == (month_end if year == year_end else 12))
		
		all_dates = get_all_dates_year(year, inventory_snapshot.snapshot)
		add_row(all_dates, 'Annual', annual_table, False)
		print(annual_table)	

	table = PrettyTable()
	table.title = f'From {year_start}-{month_start} to {year_end}-{month_end}'
	table.field_names = [
		'Sum',

		'Realized profits',
		'Realized profits %',

		'Unrealized profits',
		'Unrealized profits %',

		'Total profits',
		'Total profits %',

		'Cash',
		'Portfolio',
		'Assets',

		'Std',
		'Beta',
		'Alpha',
		'Sharpe Ratio'
	]
	all_dates = get_all_dates(year_start, month_start, list(inventory_snapshot.snapshot[year_start][month_start])[0],
			year_end, month_end, monthrange(year_end, month_end)[1])
	add_row(all_dates, 'Sum', table, False)
	print(table)	

if __name__ == '__main__':
	year_start, month_start, day_start = '2010', '01', '01'
	year_end, month_end, day_end = '2023', '12', '31'
	# read prices
	with open(PRICES_FILE, newline='') as file:
		reader = csv.reader(file, delimiter=',')
		labels = next(reader)

		# Store ticker names
		all_tickers = [ticker for ticker in labels[1:]]

		# Store the prices for each ticker on each day
		first = True
		for row in reader:
			try:
				year, month, day = get_date(row[0])
				if first:
					year_start, month_start, day_start = year, month, day
					first = False
				# Creating a dictionary for each ticker and its price on that day
				prices = {ticker: float(row[i]) for i, ticker in enumerate(all_tickers, start=1)}
				# Storing the prices in the nested dictionary
				price_daily.setdefault(year, {}).setdefault(month, {})[day] = prices
				update_dates.append(row[0])
				year_end, month_end, day_end = year, month, day
			except Exception as e:
				print(f'An error occured while reading PRICES_FILE at the line: {row}. Exception: {e}')

	inventory_curr = Inventory(tickers_interested=all_tickers)
	inventory_snapshot = InventorySnapshot()
	trades = TradeHistory()

	# Read market data
	start_date = f'{year_start}-{month_start}-{day_start}'
	end_date = f'{year_end}-{month_end}-{day_end}'
	df = yf.Ticker(MARKET_TICKER).history(start=start_date, end=end_date, interval='1d')['Close']
	if not df.empty:
		MARKET_DATA = df
	else:
		df = pd.read_csv(MARKET_FILE)
		df['Date'] = pd.to_datetime(df['Date'])
		df.set_index('Date', inplace=True)
		filtered_df = df.loc[start_date:end_date]['Close']
		MARKET_DATA = filtered_df
	
	with open(TRANSACTIONS_FILE, newline='') as csvfile:
		global update_date
		reader = csv.reader(csvfile, delimiter=',')
		next(reader) # skip labels
		update_date = update_dates.pop(0)
		for row in reader:
			while update_date != row[0]:
				daily_update(*get_date(update_date))
				update_date = update_dates.pop(0)
			process_trade(*get_date(update_date), row[1], int(row[2]), row[3])
		for date in update_dates:
			daily_update(*get_date(date))

	for ticker in all_tickers:
		tickers_interested.append(ticker)
	print_profit_table(year_start, month_start, year_end, month_end)
