
import threading
from flask import Flask, request, render_template
from main import create_loop, async_loop
import time
from forms import SettingForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kucoin.db'
app.config['SECRET_KEY'] = 'asdfvbgf55645rtg'
from extensions import db

db.init_app(app)
from models import Signal, Setting, Symbols

from main import kucoin

@app.route('/', methods=['POST', "GET"])
def index():
	form = SettingForm()
	if request.method == "POST":
		data = request.form.to_dict()
		#print(data)
		if 'submit' in data.keys():
			setting = db.session.execute(db.select(Setting).order_by(Setting.id.desc())).scalar()
			if not setting:
				new_setting = Setting()
			else:
				new_setting = setting
			if data['leverage']: new_setting.leverage = data['leverage']
			if data['risk']: new_setting.risk = data['risk']
			if data['TP']: new_setting.TP = data['TP']
			if data['SL']: new_setting.SL = data['SL']
			if data['timeframe']: new_setting.timeframe = data['timeframe']
			if not setting: db.session.add(new_setting)
			db.session.commit()
		elif 'list[0]' in data.keys():
			syms = db.session.execute(db.select(Symbols)).scalars()
			symbols = [data.get(f'list[{i}]') for i in range(len(data.keys()))]
			for sym in syms:
				db.session.delete(sym)
			db.session.commit()
			for sym in symbols:
				symbol = Symbols()
				symbol.symbol = sym.upper()+'USDT'
				db.session.add(symbol)
				db.session.commit()
				#print(sym)
		else:
			kucoin.bot = data['Bot']


	setting = db.session.execute(db.select(Setting).order_by(Setting.id.desc())).scalar()
	signals = db.session.execute(db.select(Signal).order_by(Signal.id.desc())).scalars()
	syms = db.session.execute(db.select(Symbols)).scalars()
	return render_template('index.html', form=form, user=setting, signals=signals, syms=syms)




with app.app_context():
	db.create_all()

def web():
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)


if __name__ == '__main__':
	#app.run(debug=True, host='0.0.0.0', port=5000)
	threading.Thread(target=web, daemon=True).start()
	threading.Thread(target=async_loop, daemon=True).start()
	threading.Thread(target=create_loop, daemon=True).start()

	while True:
		time.sleep(1)  
























'''
threading.Thread(target=lambda: app.run(host='localhost', port=5000, debug=False, use_reloader=False)).start()
	
'''
