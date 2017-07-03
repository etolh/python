from flask import render_template
from . import main
from flask.ext.moment import Moment  #本地化时间
from datetime import datetime


@main.route('/',methods=['GET','POST'])
def index():
    return render_template('index.html',current_time=datetime.utcnow())