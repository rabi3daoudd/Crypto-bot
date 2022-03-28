import time
import json
import config
import datetime
import os
import redis
import threading
import ccxt
import tickers

from zoneinfo import ZoneInfo
from flask import Flask, request, render_template


app = Flask(__name__)
db = redis.from_url(os.environ['REDIS_URL'])
# Initialize the exchange object with the API key and secret from config.py file
coinbase = ccxt.coinbasepro({
    'apiKey': config.API_KEY,  # API key from config.py file for Coinbase Pro exchange
    'secret': config.API_SECERET,  # API secret from config.py file for Coinbase Pro exchange
    'password': config.WEBHOOK_PASSPHRASE,  # API passphrase from config.py file for Coinbase Pro exchange
})


# a function that takes three arguments: the ticker symbol, action (buy or sell),
# and the amount of the ticker to buy or sell
def order(ticker, action, amount):
    try:
        print(f"sending order - {action} {amount} {ticker}")
        order = coinbase.create_market_order(ticker, action, amount)
        print(order)
    except Exception as e:
        print(e)
        return False
    return True


@app.route("/")
def welcome():
    return "Welcome to the Crypto Bot"


@app.route("/webhook", methods=['POST'])
def webhook():
    leaveloop = False
    data = json.loads(request.data)

    date = str(datetime.datetime.now(ZoneInfo("America/New_York")))

    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        leaveloop = True
        db.set("leaveloop", 'true')
        print("leave Loop set to true")
    else:
        db.set("leaveloop", 'false')
        print("leave Loop set to false")
    print(data['ticker'])
    side = data['strategy']['order_action']
    ticker = tickers.tickers[data['ticker']]
    print(side)
    print(datetime.datetime.now(ZoneInfo("America/New_York")))
    order_response = False
    time.sleep(5)
    if side == 'BUY':
        order_response = order(ticker, 'BUY', ETH_quantity_to_buy())
    elif side == 'SELL':
        order_response = order(ticker, 'SELL', ETH_quantity_to_sell())

    flag = order_response
    threading.Thread(target=loop_thread, args=(data, order_response, flag, leaveloop, side)).start()
    if order_response:
        print('order executed')
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")
        return {
            "code": "error",
            "message": "order failed"
        }


def loop_thread(data, order_response, flag, leaveloop, side):
    date1 = str(datetime.datetime.now(ZoneInfo("America/New_York")))
    ticker = tickers.tickers[data['ticker']]
    while flag and not leaveloop:
        leaveloop = (db.get("leaveloop").decode() == 'true')
        if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
            break
        if order_response == True:
            now = str(datetime.datetime.now(ZoneInfo("America/New_York")))
            date = date1[0:10]
            nextOddHour = next_odd_hour(date1[11:16])
            if nextOddHour == "01:00":
                nextdate = nextDate(date)
                if (now[0:10] == nextdate) and (now[11:16] == nextOddHour) and (order_response == True):
                    if side == 'BUY':
                        order(ticker, 'SELL', ETH_quantity_to_sell())
                        flag = False
                    elif side == 'SELL':
                        order(ticker, 'BUY', ETH_quantity_to_buy())
                        flag = False
            else:
                now = str(datetime.datetime.now(ZoneInfo("America/New_York")))
                date = date1[0:10]
                nextOddHour = next_odd_hour(date1[11:16])
                if (now[0:10] == date) and (now[11:16] == nextOddHour) and (order_response == True):
                    if side == 'BUY':
                        order(ticker, 'SELL', ETH_quantity_to_sell())
                        flag = False
                    elif side == 'SELL':
                        order(ticker, 'BUY', ETH_quantity_to_buy())
                        flag = False
    print(f"Leaving loop - {data['passphrase']}")


# function to get quantity to sell a crypto
def ETH_quantity_to_sell():
    currency = coinbase.fetch_balance()['ETH']
    return currency['free']


def ETH_quantity_to_buy():
    USDC = coinbase.fetch_balance()['USDC']
    ETH_USDC = coinbase.fetch_ticker('ETH/USDC')
    ETH_USDC_price = ETH_USDC['last']
    ammount_to_be_bought = USDC['free'] / ETH_USDC_price
    ammount_to_be_bought = ammount_to_be_bought * 0.984
    ammount_to_be_bought = round(ammount_to_be_bought, 4)
    return ammount_to_be_bought


# function to get the next odd hour and return it in string format
def next_odd_hour(time):
    hour = int(time[:2])
    minute = int(time[3:])
    if minute % 30 == 0:
        if hour % 2 == 0:
            hour += 1
        else:
            hour += 2
    else:
        if hour % 2 == 0:
            hour += 1
        else:
            hour += 2
    if hour > 23:
        hour = hour - 24
    if hour < 10:
        hour = '0' + str(hour)
    else:
        hour = str(hour)
    if minute < 10:
        minute = '0' + str(minute)
    else:
        minute = str(minute)
    minute = "01"
    return hour + ':' + minute


# function to get the next date and return it in string format and in the format of YYYY-MM-DD format (e.g.
# 2020-01-01) accounting for the leap year and the month with 31 days and 30 days respectively and the month with 28
# days and 29 days respectively
def nextDate(date):
    year = int(date[:4])
    month = int(date[5:7])
    day = int(date[8:])
    if month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
        if day == 31:
            day = 1
            month += 1
            if month == 13:
                month = 1
                year += 1
        else:
            day += 1
    elif month == 2:
        if year % 4 == 0:
            if day == 29:
                day = 1
                month += 1
            else:
                day += 1
        else:
            if day == 28:
                day = 1
                month += 1
            else:
                day += 1
    else:
        if day == 30:
            day = 1
            month += 1
        else:
            day += 1
    if month < 10:
        month = '0' + str(month)
    else:
        month = str(month)
    if day < 10:
        day = '0' + str(day)
    else:
        day = str(day)
    return str(year) + '-' + month + '-' + day


def is_night(time):
    # time is a striing format like "23:00" or "00:00"
    # check if time is between 23:00 and 23:59
    if "23:00" <= time <= "23:59":
        return True
    else:
        return False

