import requests
import datetime
import ccxt
import config
import time

# send a post request to the server
JSON = {
      "passphrase": "passphrase",
      "time": "2022-01-09T11:48:05Z",
      "exchange": "COINBASEPRO",
      "ticker": "ETHUSDC",
      "ID": "123456789",
      "strategy": {
            "position_size": "0.0001",
            "order_action": "SELL",
            "order_contracts": "0.0001"
      }
}


def send_request(request):
    data = request.get_json(force=True)
    time = str(datetime.datetime.now())
    time = time[11:16]

    JSON['strategy']['order_action'] = data['strategy']['order_action']

    # check every hour if a request came in and send a response
    flag = False
    while flag:
            r = requests.post('Insert your URL', JSON)


