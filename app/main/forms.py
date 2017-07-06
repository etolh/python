from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User

#定义表单类
class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


#资料编辑表单
class EditProfileForm(FlaskForm):
    realname = StringField('Real name',validators=[Length(0,64)])
    location = StringField('Location',validators=[Length(0,64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

#管理员编辑表单
class EditProfileAdminForm(FlaskForm):

    email = StringField('Email',validators=[Required(),Length(0,64),Email()])
    name = StringField('Username',validators=[Required(), Length(1, 64), 
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
        'Usernames must have only letters, '
        'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)

    #除基本编辑表单外，还能编辑用户的邮箱、用户名、激活状态和角色
    realname = StringField('Real name',validators=[Length(0,64)])
    location = StringField('Location',validators=[Length(0,64)])
    about_me = TextAreaField('About     me')
    submit = SubmitField('Submit')

    def __init__(self,user,*args,**kw):
        super(EditProfileAdminForm, self).__init__(*args, **kw)
        self.role.choices = [(role.id,role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    #验证邮箱、用户名，若其已经发生变化且在数据库已存在，抛出异常
    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.name and \
                User.query.filter_by(name=field.data).first():
            raise ValidationError('Username already in use.')