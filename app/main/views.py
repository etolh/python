from datetime import datetime
from flask import render_template, session, redirect, url_for
from . import main
from .forms import NameForm
from .. import db
from ..models import User


@main.route('/',methods=['GET','POST'])
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

        return redirect(url_for('.index'))

    return render_template('index.html', 
        form=form,name=session.get('name'),
        known=session.get('known',False),
        current_time=datetime.utcnow())