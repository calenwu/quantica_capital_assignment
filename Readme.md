# Assignment
I was given this as a take home assignment for some junior swe position.

## Goal of the assignment

Implement a script that can calculate the value and performance of a portfolio of ETFs over time derived from a CSV file containing transaction data.

You will need to:
    
- reconstruct the `positions` from the transactions
- value the positions over time
- calculate the performance of the portfolio (in % and in USD)

### Input

The provided input is in two CSV files containing transactions and prices.

tx_etf.csv:
- `date`: the date of the position
- `ticker`: the ticker of the position
- `qty`: the quantity of the order
- `order`: BUY or SELL
- there is no price data for the ETFs pr


# Solution

## How to Run the Command Line Tool

Please change into the directory where this file lies and then run the commands

## Building and Running the Docker Container for Command Line
1. Build the Docker container: `docker build --tag 'georg_cmd' .`
2. Run the docker container: `docker run -v "$PWD":/usr/src/myapp -w /usr/src/myapp georg_cmd python main.py`

## How to run the juptyer notebook:
### Building and Running the Docker Container for Jupyter Notebook
1. Build the Docker container: `docker build --tag 'georg_jupyter' -f Dockerfile.j .`
2. Run the Docker container: `docker run -p 8888:8888 -v $PWD:/home/jovyan/work georg_jupyter`

### Accessing the Jupyter Notebook
- After running the Docker container, open the link printed in the terminal.
- Navigate to the `work` folder using the file explorer on the left of the page.
- Open the `main.ipynb` file.
- Execute the notebook: Click on the Play button and run every cell from top to bottom.
- Utilize the UI at the bottom to run specific functions once finished loading.

Please note that the profits histrogramm might take a few seconds to load if the timeframe is big

## Calculating Profits in Percentage

How profits in percentage are calculated:
Total profits / total costs

If you buy 10 TSLA at 10 and sell 5 for 20 then buy 5 for 15 and sell 10 for 20 you get:
(5 * 10 + 5 * 5 + 5 * 10) / (10 * 10 + 5 * 15) = 125 / 175

One could have also calculated it like so: Total profits / Initial investment:
(5 * 10 + 5 * 5 + 5 * 10) / (10 * 10) = 125 / 100

But the second option was difficult to calculate due to time constraints.
