from flask import Flask,render_template
from flask_script import Manager    #flask扩展：使用命令行选项
from flask.ext.bootstrap import Bootstrap 
from flask.ext.moment import Moment  #本地化时间
from datetime import datetime

app = Flask(__name__)

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)


#app.route完成url映射的路由绑定：
#当输入该url时，app程序对象会自动寻找对应的函数处理url请求
@app.route('/')
def index():
    # return '<h1>Hello World!</h1>'
    #使用jinja2模板
    return render_template('index.html', current_time=datetime.utcnow())

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
