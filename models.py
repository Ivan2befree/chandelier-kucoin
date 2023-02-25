from sqlalchemy import Column, Integer, String, Float, DateTime
from extensions import db


class Signal(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    side = Column(String)
    size = Column(Float)
    price = Column(Float)
    time = Column(String)
    status = Column(String)
    exittime = Column(String)
    exitprice = Column(Float)



class Setting(db.Model):
    id = Column(Integer, primary_key=True)
    leverage = Column(Integer)
    risk = Column(String)
    TP = Column(String)
    SL = Column(String)
    timeframe = Column(String)


class Symbols(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String)


class Start(db.Model):
    id = Column(Integer, primary_key=True)
    run = Column(String)