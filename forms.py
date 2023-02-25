from flask_wtf import FlaskForm
from wtforms import  StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class SettingForm(FlaskForm):
    leverage = StringField(validators=[DataRequired()])
    risk = StringField(validators=[DataRequired()])
    TP = StringField(validators=[DataRequired()])
    SL = StringField(validators=[DataRequired()])
    timeframe = SelectField(choices=('1min', '5min','15min', '30min', '1hour', '4hour',), default='5min')
    submit = SubmitField()

