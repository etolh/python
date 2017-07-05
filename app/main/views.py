from flask import render_template, redirect, url_for, abort, flash
from . import main
from flask.ext.moment import Moment  #本地化时间
from datetime import datetime
from ..models import User
from .forms import EditProfileForm, EditProfileAdminForm
from flask_login import login_required, current_user
from .. import db
from ..decorators import admin_required

@main.route('/',methods=['GET','POST'])
def index():
    return render_template('index.html',current_time=datetime.utcnow())



#用户资料页面路由
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(name=username).first()
    if user is None:
        abort(404)
    return render_template('user.html',user=user)

#资料编辑路由
@main.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        #更新用户资料
        current_user.realname = form.realname.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.user',username=current_user.name))

    form.realname.data = current_user.realname
    form.location.data = current_user.about_me
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form)

#管理员资料编辑路由
@main.route('/edit_profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    
    if form.validate_on_submit():
        #更新用户资料
        user.email = form.email.data
        user.name = form.name.data
        user.cofirmed = form.cofirmed.data
        user.role = form.role.data
        user.realname = form.realname.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.user',username=user.name))

    form.email.data = user.email
    form.name.data = user.name
    form.cofirmed.data = user.cofirmed
    form.role.data = user.role
    form.realname.data = current_user.realname
    form.location.data = current_user.about_me
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form,user=user)
