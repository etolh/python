from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required
from . import auth  #引入蓝本
from ..models import User
from .forms import LoginForm, RegisterForm, UpdatePsdForm, UserEmailForm, ResetPasswordForm
from .. import db
from flask.ext.moment import Moment  #本地化时间
from datetime import datetime
from ..email import send_mail
from flask.ext.login import current_user

@auth.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid name or password')

    return render_template('auth/login.html',form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # 注册进数据库
        user = User(email=form.email.data,name=form.username.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()

        token = user.generate_confirmation_token()
        send_mail(user.email, 'Confirm Your Account.','auth/email/confirm',user=user,token=token)
        flash('A confirmation email has been sent to your email.\
            you can login.')
        
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html',form=form)

@auth.route('/setting',methods=['GET','POST'])
def setting():
    #修改密码
    form = UpdatePsdForm()

    if form.validate_on_submit():
        oldpassword = form.oldpassword.data
        newpassword = form.password2.data

        #确认密码为当前用户的密码
        if current_user.verify_password(oldpassword):
            current_user.password = newpassword
            db.session.add(current_user)
            db.session.commit()
            flash('You have change your password.')
            return redirect(url_for('auth.login'))

        #密码错误
        flash('Invalid name or password')

    return render_template('auth/setting.html',form=form)

@auth.route('/resetrequest',methods=['GET','POST'])
def resetrequest():
    #忘记密码,提供一个email的表格，接收表格发送重设密码邮件
    form = UserEmailForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user is not None:
            #发送带有token令牌的邮件
            token = user.generate_confirmation_token()
            send_mail(email, 'Reset your Password!','auth/email/reset_password',user=user,token=token)
            flash('A Reset email has been sent to your email.\
            you can login.')
        else:
            flash('Invalid email')
        
        return redirect(url_for('auth.login'))

    return render_template('auth/resetpassword.html',form=form)

@auth.route('/password_reset/<token>',methods=['GET','POST'])
def password_reset(token):
    #邮件url重设密码
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user is not None and user.confirm(token):
            #确认为输入的用户
            newpassword = form.password.data
            user.password = newpassword
            db.session.add(user)
            db.session.commit()

            flash('You have reseted your password.')
            return redirect(url_for('auth.login'))
        
        flash('resetpassword')

    return render_template('auth/resetpassword.html',form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    #验证用户，并激活
    if current_user.confirmed:
        #已激活
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    #用户在线但处于未激活状态
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        #已激活，返回主页
        return redirect(url_for('main.index'))
    #未激活，返回激活说明，重新发送激活邮件
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_mail(current_user.email, 'Confirm Your Account.','auth/email/confirm',user=current_user,token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))

