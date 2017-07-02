from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required

#定义表单类
class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')