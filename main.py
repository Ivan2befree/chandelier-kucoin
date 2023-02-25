import json, time
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from kucoin_futures.client import Market, User, Trade
from extensions import db
from models import Signal, Setting, Symbols


with open('config.json') as f:
		config = json.load(f)
key = config['key']
secret = config['secret']
passphrase = config['passphrase']

market = Market()
trade = Trade(key, secret, passphrase)
user = User(key, secret, passphrase)


class Kucoin:
	def __init__(self):
		self.bot = 'Stop' # or 'Run'
		self.kline = False
		self.symbols = []
		self.timeframe = ''
		self.leverage = ''
		self.risk = ''
		self.TP = ''
		self.SL = ''
		self.SLPrice = {}
		self.onExchange = False
		self.signal = {}

	def _try_request(self, method:str, **kwargs):
		try:
			if method == 'get_server_time':
				stime = ''
				while stime == '':
					print('try to get server time ... ... ...')
					try:
						stime = market.get_server_timestamp()
						#print(stime)
					except:
						time.sleep(1)
				return stime
			elif method == 'get_position_details':
				res = None
				while not res:
					try:
						res = trade. get_position_details(symbol=kwargs['symbol'])
					except Exception as e:
						print('e for get position details: ', e)
						time.sleep(1)
				return res
			elif method == 'create_market_order':
				self.onExchange = False
				while not self.onExchange:
					try:
						order_id = trade.create_market_order(symbol=kwargs['symbol'], size=kwargs['size'], side=kwargs['side'], lever=kwargs['lever'], closeOrder=kwargs['closeOrder'], clientOid=kwargs.get('clientOid'))
					except Exception as e:
						print("e for create market order: ", e)
						time.sleep(1)
				return order_id
			elif method == "cancel_all_stop_order":
				res = ''
				while res == '':
					try:
						res = trade.cancel_all_stop_order(symbol=kwargs.get('symbol'))
					except Exception as e:
						print('e for cancel_all_stop_order: ', e)
						time.sleep(1)
				return res
			elif method == 'get_balance':
				balance = ''
				while balance == '':
					try:
						balance = user.get_account_overview("USDT")['availableBalance']
					except Exception as e:
						print('e of get balance is: ', e)
						time.sleep(1)
				print('balance is: ', balance)
				return balance
			elif method == 'convert_symbol':
				symbol = kwargs.get('symbol')
				if symbol == "BTCUSDT":
					symbol = "XBTUSDTM"
				else:
					symbol = symbol + "M"
				return symbol
			elif method == "get_lot":
				symbol = kwargs.get('symbol')
				price = kwargs.get('price')
				lot = 0
				while lot == 0:
					try:
						input_balance = kucoin.risk * kucoin._try_request('get_balance') 
						contract_detail = market.get_contract_detail(symbol)
						multi = contract_detail['multiplier']
						tickSize = contract_detail['tickSize']
						lot = input_balance / ( (multi) * price)#market.get_current_mark_price(symbol)['indexPrice'] )
						lot = lot * kucoin.leverage
						#lot = math.floor(lot)
						lot = round(lot, 4)
					except Exception as e:
						print('e for get lot is: ', e)
						time.sleep(1)
				print('lot is: ',lot)
				return lot
			elif method == "get_signal":
				symbol = kwargs.get('symbol')
				t = 0
				interval = self.timeframe
				gap = interval[0]
				if interval == '15min' or interval == '30min':
					gap = interval[:2]
				elif interval == '1h' or interval == '4h':
					gap = int(interval[0]) * 60
				stime = self._try_request(method='get_server_time')
				while (stime - t) > 2*int(gap)*60000:
					try:
						klines = market.get_kline_data(f'{symbol}',f'{gap}')
						t = int(klines[-2][0])
						print(f'{symbol}: open time: ... ...', datetime.fromtimestamp(t/1000))
					except Exception as e:
						print('e in market.get_kline_data ', e)
						time.sleep(1)

				side = None
				klines = klines[:-1] # last candle is open
				df = ta.DataFrame(klines)
				df.columns = ['time', 'open', 'high', 'low', 'close', 'vol']
				dfha = ta.ha(df['open'], df['high'], df['low'], df['close'])
				dfha.columns = ['open', 'high', 'low', 'close']
				dfha['time'] = pd.to_datetime(df['time']*10**6)
				df = dfha
				lenght = 22
				mult = 3
				def wwma(values, n):
					return values.ewm(alpha=1/n, adjust=False).mean()
				def atr(df, n):
					data = df.copy()
					high = data['high']
					low = data['low']
					close = data['close']
					data['tr0'] = abs(high - low)
					data['tr1'] = abs(high - close.shift())
					data['tr2'] = abs(low - close.shift())
					tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
					atr = wwma(tr, n)
					return atr
				df['atr'] = mult * atr(df, lenght)
				df['dir'] = 1
				
				df['longStop'] = df['close'].rolling(lenght).max() - df['atr']
				df['shortStop'] = df['close'].rolling(lenght).min() + df['atr']
				for i in df.index:
					if df['close'].iloc[i-1] > df['longStop'].iloc[i-1]:
						df.at[i, 'longStop'] = max(df['longStop'].iloc[i], df['longStop'].iloc[i-1])
					
					if df['close'].iloc[i-1] < df['shortStop'].iloc[i-1]:
						df.at[i, 'shortStop'] = min(df['shortStop'].iloc[i], df['shortStop'].iloc[i-1])
				
					if df['close'].iloc[i] > df['shortStop'].iloc[i-1]:
						df.at[i, 'dir'] = 1
					elif df['close'].iloc[i] < df['longStop'].iloc[i-1]:
						df.at[i, 'dir'] = -1
					else:
						df.at[i, 'dir'] = df['dir'].iloc[i-1]

				if df['dir'].iloc[-1] == 1 and df['dir'].iloc[-2] == -1:
					side = 'buy'
					self.SLPrice[symbol] = df['longStop'].iloc[i]

				elif df['dir'].iloc[-1] == -1 and df['dir'].iloc[-2] == 1:
					side = 'sell'
					self.SLPrice[symbol] = df['shortStop'].iloc[i]
				print(df.tail(10))
				#print(side)
				#side = None
				price = df['close'].iloc[-1]
				time = df['time'].iloc[-1]
				self.signal[symbol] = [side, price, time]
				#return [side, round(price, 4), df['time'].iloc[-1]]

			elif method == 'get_entry_price':
				symbol = kwargs.get('symbol')
				isOpen = False
				while isOpen == False:
					try:
						pos_detail = trade.get_position_details(symbol)
						isOpen = pos_detail['isOpen']
						entry_price = pos_detail['avgEntryPrice']
						entry_time = pos_detail['openingTimestamp']
						currentCost = pos_detail['currentCost']
						entry_time = datetime.fromtimestamp(int(entry_time)/1000).strftime("%Y-%m-%d %H:%M:%S")
						print('entry price: ', entry_price)
					except Exception as e:
						print('e of get avg_price is', e)
						time.sleep(1)
				return entry_price
			elif method == 'set_tpsl':
				symbol = kwargs.get('symbol')
				side = kwargs.get('side')
				size = kwargs.get('size')
				tp_per = kucoin.TP
				sl_per = kucoin.SL
				entry_price = kucoin._try_request(method='get_entry_price', symbol=symbol)
				#sl = float(entry_price) * (1-sl_per)
				tp = float(entry_price) * (1+tp_per)
				stop_sl = 'down'
				stop_tp = 'up'
				side_tpsl = 'sell'
				if side == 'sell':
					#sl = float(entry_price) * (1+sl_per)
					tp = float(entry_price) * (1-tp_per)
					stop_tp = 'down'
					stop_sl = 'up'
					side_tpsl = 'buy'
				sl = self.SLPrice[symbol]
				SL = 0
				while SL == 0:
					try:
						print(' try set SL ... ... ...')
						SL = trade.create_market_order(symbol=symbol, stop= stop_sl, stopPriceType= 'TP', stopPrice= sl,  lever=kucoin.leverage, size = size, side = side_tpsl, clientOid=symbol+"_SL")
						print('SL is set on ', symbol, SL)
						#telegram(f'SL set on {symbol}')
					except Exception as e:
						print('e for set SL: ', e)
						time.sleep(1)
				TP = 0
				while TP == 0:
					try:
						print(' try set TP ... ... ...')
						TP = trade.create_market_order(symbol=symbol, stop= stop_tp, stopPriceType= 'TP', stopPrice= tp,  lever=kucoin.leverage, size = size, side = side_tpsl, clientOid=symbol+"_TP")
						print('TP is set on ', symbol, TP)
						#telegram(f'TP set on {symbol}')
					except Exception as e:
						print('e for set TP: ', e)
						time.sleep(1)

		except Exception as e:
			print(f'e for _try_request---{method}: ', e)


kucoin = Kucoin()
#kucoin.timeframe = '1min'
#print(kucoin._try_request(method='get_signal', symbol='SOLUSDTM'))

def create_loop():
	while 1:
		#print('bot ...')
		try:
			if kucoin.kline and kucoin.bot=='Run':
				print('kline is closed.')
				kucoin.kline = False

				for symbol in kucoin.symbols:
					if symbol:
						sym = kucoin._try_request(method='convert_symbol', symbol=symbol)
						## sym == kucoin symbol
						kucoin._try_request(method='get_signal', symbol=sym)
						signal = kucoin.signal[sym]
						side = signal[0]; price = signal[1]#; time = signal[2]
						#side = 'buy'
						#price = 0.37
						if side:
							# get positions
							pos = kucoin._try_request(method='get_position_details', symbol=sym)
							print("get position details ... ... ...")
							#print(res)
							if pos['isOpen']:
								lever = pos["realLeverage"]
								size = abs(pos["currentQty"])
								side = 'buy' if pos["currentQty"]<0 else 'sell'
								kucoin._try_request(method='create_market_order', symbol=sym, size=size, side=
													side, lever=lever, clientOid=sym+"_exit", closeOrder=True)
							### cancle all stop orders
							kucoin._try_request(method="cancel_all_stop_order", symbol=sym)
							lot = kucoin._try_request(method='get_lot', symbol=sym, price=price)
							print('get lot ...', lot)
							kucoin._try_request(method='create_market_order', symbol=sym, size=lot, side=
							side, lever=kucoin.leverage, clientOid=sym+"_entry", closeOrder=False)
								

		except Exception as e:
			print('e for create loop: ', e)
		time.sleep(1)


import asyncio
from kucoin_futures.client import WsToken, Trade
from kucoin_futures.ws_client import KucoinFuturesWsClient
trade = Trade(key, secret, passphrase)
from kucoin.client import WsToken as WsToken_spot
from kucoin.ws_client import KucoinWsClient as KucoinWsClient_spot


async def main(loop):
	async def deal_msg_spot(msg):
		try:
			#print(msg['subject'])
			#print('deal msg spot ... ... ...')
			if msg['subject'] == "trade.candles.add":
				print('kline is closed... ... ...')
				kucoin.kline = True
		except Exception as e:
			print('e for deal msg spot ', e)

	async def deal_msg(msg):
		print('runing async ... ...')
		if msg['topic'] == '/contractMarket/tradeOrders':
			try:
				data = msg['data']
				print('...........................................')
				#print(msg)
				print('*******************************************')
				now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				symbol = data['symbol']
				symbol_db = symbol[:-1]
				if symbol == 'XBTUSDTM': symbol_db = 'BTCUSDT'
				clientOid = data['clientOid']
				side = data['side']
				lot = float(data['size'])
				#price = float(data['price'])
				print("type: ... ... ...", data['type'])
				print("status: ... ... ...", data["status"])
				if data["status"] == 'done' and data['type'] == 'filled':
					if 'entry' in clientOid:
						print('position done.')
						kucoin.onExchange = True
						price = kucoin.signal[symbol][1]
						from app import app
						with app.app_context():
							signal = Signal()
							signal.symbol = symbol_db
							signal.side = side
							signal.size = lot
							signal.price = price
							signal.time = now
							signal.status = 'entry'
							db.session.add(signal)
							db.session.commit()
						kucoin._try_request(method="set_tpsl",symbol=symbol, side=side, size=lot)
						print('set_tpsl')
					
					if 'exit' in clientOid:
						print('position is closed.')
						kucoin.onExchange = True
						price = kucoin.signal[symbol][1]
						from app import app
						with app.app_context():
							position = db.session.execute(db.select(Signal).where(Signal.symbol==symbol_db).order_by(Signal.id.desc())).scalar()
							position.status = "close"
							position.exittime = now
							position.exitprice = price
							db.session.commit()
					
					elif ('_SL' or '_TP') in clientOid:
						SLTP = 'SL'
						if clientOid[-2:] == 'TP': SLTP = 'TP'
						print('SL/TP is done.')
						kucoin._try_request(method='cancel_all_stop_order', symbol=symbol)
						print('close all stop orders')

						price = kucoin.signal[symbol][1]
						from app import app
						with app.app_context():
							order = db.session.execute(db.select(Signal).where(Signal.symbol==symbol_db).order_by(Signal.id.desc())).scalar()
							order.exittime = now
							order.exitprice = price
							order.status = SLTP
							db.session.commit()

			except Exception as e:
				print('e for contractMarket/tradeOrders', e)
		

	client = WsToken(key=key, secret=secret, passphrase=passphrase)
	client_ticker = WsToken()
	ws_client = await KucoinFuturesWsClient.create(loop, client, deal_msg, private=True)
	await ws_client.subscribe('/contractMarket/tradeOrders')
	###
	
	# spot
	client_spot = WsToken_spot()
	ws_client_spot = await KucoinWsClient_spot.create(loop, client_spot, deal_msg_spot, private=False)
	ws_client_spot = await KucoinWsClient_spot.create(loop, client_spot, deal_msg_spot, private=False)
	await ws_client_spot.subscribe(f"/market/candles:BTC-USDT_{kucoin.timeframe}")#1min, 15min, 1hour
	
	while True:
		await asyncio.sleep(60, loop=loop)


def handle_async():
	#loop = asyncio.get_event_loop()
	loop = asyncio.new_event_loop()
	#asyncio.set_event_loop(loop)
	loop.run_until_complete(main(loop))




def async_loop():
	while 1:
		if kucoin.bot == 'Run':
			print('........................ bot is started ... ... ...')
			from app import app
			with app.app_context():
				user_set = db.session.execute(db.select(Setting).order_by(Setting.id.desc())).scalar()
				#positions = db.session.execute(db.select(Signal).where(Signal.status=='entry')).scalars()
				kucoin.leverage = user_set.leverage
				kucoin.risk = float(user_set.risk)/100
				kucoin.TP = float(user_set.TP)/100
				kucoin.SL = float(user_set.SL)/100
				kucoin.timeframe = user_set.timeframe
				symbols = db.session.execute(db.select(Symbols).order_by(Symbols.id.desc())).scalars()
				kucoin.symbols = [symbol.symbol for symbol in symbols]

			handle_async()
		print('bot is off ... ... ...')
		time.sleep(1)