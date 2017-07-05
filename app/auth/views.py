from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required
from . import auth  #引入蓝本
from ..models import User
from .forms import LoginForm, RegisterForm, UpdatePsdForm, UserEmailForm, ResetPasswordForm
from .forms import Change_Email_Req
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
        send_mail(user.email, 'Confirm Your Account.','auth/email/confirm_user',user=user,token=token)
        flash('A confirmation email has been sent to your email.\
            you can login.')
        
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html',form=form)

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
    send_mail(current_user.email, 'Confirm Your Account.','auth/email/confirm_user',user=current_user,token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))



@auth.route('/change_password',methods=['GET','POST'])
def change_password():
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

@auth.route('/reset_psd_req',methods=['GET','POST'])
def reset_psd_req():
    #忘记密码,提供一个email的表格，接收表格发送重设密码邮件
    if not current_user.is_anonymous:
        #已登录用户返回主界面
        return redirect(url_for('main.index'))

    form = UserEmailForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user is not None:
            #发送带有token令牌的邮件：token确认为当前用户
            token = user.generate_password_token()
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
    if not current_user.is_anonymous:
        #已登录用户返回主界面
        return redirect(url_for('main.index'))

    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        newpassword = form.password.data

        if user is not None and user.resetpassword(newpassword,token):
            
            #验证函数中更新密码
            flash('You have reseted your password.')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalidate Request')

    return render_template('auth/resetpassword.html',form=form)

@auth.route('/change_email_req',methods=['POST','GET'])
def change_email_req():
    #提交新邮箱
    form = Change_Email_Req()

    if form.validate_on_submit():
        #提交邮箱后发送邮件
        newemail = form.email.data
        #将新邮件地址保存在session中，待验证后更新用户
        password = form.password.data

        if current_user.verify_password(password):
            #生成新邮箱令牌，token保存新邮箱地址
            token = current_user.generate_email_token(newemail)
            send_mail(newemail,'Change your Email!','auth/email/change_email',user=current_user,token=token)
            flash('A Reset email has been sent to your email.')
        else:
            flash('Invalidate Password.')
        return redirect(url_for('main.index'))

    return render_template('auth/emailchange.html',form=form)

@auth.route('/change_email/<token>',methods=['POST','GET'])
@login_required
def change_email(token):
    #邮件url修改邮箱
    if current_user.confirmed_email(token):
        #验证邮箱的同时，更新用户
        flash('You have changed your email.')
    else:
        flash('Invalidate Request')

    return redirect(url_for('main.index'))