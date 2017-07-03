from flask import render_template
from . import auth  #引入蓝本

@auth.route('/login')
def login():
    return render_template('auth/login.html')