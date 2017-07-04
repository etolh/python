from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(Form):
    email = StringField('Email', validators=[Required(),Length(1,64),Email()])
    password = PasswordField('Password',validators=[Required()])
    remember_me = BooleanField('keep me logged in')
    submit = SubmitField('Log in')


class RegisterForm(Form):
    
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password = PasswordField('Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    #验证email、username未用过，即未出现在数据库
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('Username already in use.')

class UpdatePsdForm(Form):
    oldpassword = PasswordField('OldPassword',validators=[Required()])
    password = PasswordField('New password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password',validators=[Required()])
    submit = SubmitField('Change')


class UserEmailForm(Form):
    #重设密码s1:输入用户
    email = StringField('Email', validators=[Required(),Length(1,64),Email()])
    submit = SubmitField('next step')

class ResetPasswordForm(Form):
    #重设密码：输入用户名，新密码
    email = StringField('Email', validators=[Required(),Length(1,64),Email()])
    password = PasswordField('New password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password',validators=[Required()])
    submit = SubmitField('Reset')