import requests
import json
from datetime import datetime

webhook_url = "http://127.0.0.1:5000/webhook"
#webhook_url = "http://188.34.151.49:80/webhook"


data = {
    "passphrase": "kh321",
    "time": "{{timenow}}",
    "exchange": "{{exchange}}",
    "ticker": "{{ticker}}",
    "bar": {
        "time": "{{time}}",
        "open": "{{open}}",
        "high": "{{high}}",
        "low": "{{low}}",
        "close": "{{close}}",
        "volume": "{{volume}}"
    },  
    "strategy": {
        "position_size": "{{strategy.position_size}}",
        "order_action": "{{strategy.order.action}}",
        "order_contracts": "{{strategy.order.contracts}}",
        "order_price": "{{strategy.order.price}}",
        "order_id": "{{strategy.order.id}}",
        "message" : "{{strategy.order.alert_message}}",
        "market_position": "{{strategy.market_position}}",
        "market_position_size": "{{strategy.market_position_size}}",
        "prev_market_position": "{{strategy.prev_market_position}}",
        "prev_market_position_size": "{{strategy.prev_market_position_size}}"
    }
}

data = {
    "time":"2022-03-01",
    "ticker": "ETHUSDT",
    "strategy": {"order_action":"Buy", "order_price":"450","order_id":"Long","order_contracts":1, 'message':'exit'},   
}
now = datetime.now()
data = ("ADAUSDTM", "sell", '0.347', f'{now}')
data = ()
proxies = {
   'http' : 'socks5://127.0.0.1:9150',
   'https' : 'socks5://127.0.0.1:9150'
}

res = requests.post(webhook_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})#, proxies=proxies)

print(res)




"""
contracts = market.get_contracts_list()
symbols = [contract['symbol'] for contract in contracts]
"""
