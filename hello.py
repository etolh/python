import os
from flask import Flask,render_template
from flask_script import Manager    #flask扩展：使用命令行选项
from flask.ext.bootstrap import Bootstrap 
from flask.ext.moment import Moment  #本地化时间
from datetime import datetime
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask import Flask, render_template, session, redirect, url_for, flash #4b,重定向
from flask_sqlalchemy import SQLAlchemy
from flask.ext.script import Shell
from flask.ext.migrate import Migrate,MigrateCommand
from flask.ext.mail import Mail,Message
from threading import Thread

app = Flask(__name__)

#defend csrf
app.config['SECRET_KEY'] = 'hard to guess string'
#config mysql
app.config['SQLALCHEMY_DATABASE_URI'] = \
'mysql://root:4854264@localhost:3306/web'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
#mail
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
#get from environment
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = '2137243608@qq.com'
app.config['FLASKY_TO'] = os.environ.get('FLASKY_TO')


#db refers to database
db = SQLAlchemy(app)
manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
migrate = Migrate(app, db)
mail = Mail(app)

#定义数据库表对应的模型:extends db.Model
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)

    #one2many-relations:one,backref与__tablename__对应,lazy='dynamic'禁止自动
    users = db.relationship('User', backref='role',lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),unique=True)

    #one2many-relations:many,ForeignKey与__tablename__对应
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __repr__(self):
        return '<User %r>' % self.name

def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)

def send_mail(to,subject,template,**kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, 
        sender=app.config['FLASKY_MAIL_SENDER'],recipients=[to])
    msg.body = render_template(template+'.txt', **kwargs)
    msg.html = render_template(template+'.html',**kwargs)
    thr = Thread(target=send_async_email,args=[app, msg])
    thr.start()
    return thr

#定义表单类
class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


def make_shell_context():
    return dict(app=app,db=db,User=User,Role=Role)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


#app.route完成url映射的路由绑定：
#当输入该url时，app程序对象会自动寻找对应的函数处理url请求
@app.route('/',methods=['GET','POST'])
def index():
    
    form = NameForm()
    if form.validate_on_submit():

        name = form.name.data
        user = User.query.filter_by(name=name).first()

        if user is None:
            user = User(name=name)
            db.session.add(user)
            session['known'] = False

            #每新加入一个用户，向管理员发送邮件
            if app.config['FLASKY_TO']:
                send_mail(app.config['FLASKY_TO'],'New User','mail/new_user',user=user)

        else:
            #设为TRUE
            session['known'] = True

        session['name'] = name
        form.name.data = '' #清空

        return redirect(url_for('index'))

    return render_template('index.html', form=form,name=session.get('name'),known=session.get('known',False),current_time=datetime.utcnow())


#url动态部分可以用<>修饰，再传入绑定的视图函数
@app.route('/user/<name>')
def user(name):
    # return '<h1>Hello %s!</h1>' % name
    return render_template('user.html',name=name)

#错误处理页面:404:未知请求，500：内部错误
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    #app.run(debug=True)
    manager.run()
