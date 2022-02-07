from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length

class LaptopForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired(), Length(min=6, max=20)])
    price=IntegerField('Price',validators=[DataRequired(), Length(min=6, max=20)])
    description = StringField('description', validators=[DataRequired(), Length(min=6, max=200)])
    submit = SubmitField('Update!')


class PurchaseForm(FlaskForm):
    submit = SubmitField(label='Purchase')

class SellForm(FlaskForm):
    submit = SubmitField(label='Sell')