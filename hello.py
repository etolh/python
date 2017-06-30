from flask import Flask
app = Flask(__name__)

#app.route完成url映射的路由绑定：
#当输入该url时，app程序对象会自动寻找对应的函数处理url请求
@app.route('/')
def index():
    return '<h1>Hello World!</h1>'

#url动态部分可以用<>修饰，再传入绑定的视图函数
@app.route('/user/<name>')
def user(name):
    return '<h1>Hello %s!</h1>' % name

if __name__ == '__main__':
    app.run(debug=True)
