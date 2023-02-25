
from api_key import key, secret, passphrase
from kucoin_futures.client import Market, User, Trade

market = Market()
trade = Trade(key, secret, passphrase)
user = User(key, secret, passphrase)

trade.create_market_order(symbol="ADAUSDTM", closeOrder=True)

trade.create_market_order(symbol="SOLUSDTM", side='buy', closeOrder=True)

trade.create_market_order(symbol="SOLUSDTM", side='sell', closeOrder=True)

trade.create_market_order(symbol="SOLUSDTM", side='sell', closeOrder=True, size='50', lever='10')