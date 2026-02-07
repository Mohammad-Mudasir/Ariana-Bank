from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,FloatField,PasswordField
from wtforms.validators import DataRequired,Email


class CreateAccount(FlaskForm):
    name = StringField('Name',[DataRequired()])
    email = StringField('Email',[DataRequired(),Email('Invalid Email!')])
    amount = FloatField('Amount In Dollar',[DataRequired()])
    password = PasswordField('Password',[DataRequired()])
    submit = SubmitField('Create Account')

class MakeDeposit(FlaskForm):
    name = StringField('Name',[DataRequired()])
    receiver = StringField('Send To',[DataRequired()])
    amount = FloatField('Amount In Dollar',[DataRequired()])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    name = StringField('Name',[DataRequired()])
    password = PasswordField('Password',[DataRequired()])
    submit = SubmitField('Login')

class WithdrawalsForm(FlaskForm):
    amount = FloatField('Amount In Dollar',[DataRequired()])
    password = PasswordField('Password',[DataRequired()])
    submit = SubmitField('Submit')