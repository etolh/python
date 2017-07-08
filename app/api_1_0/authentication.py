from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User, AnonymousUser
from . import api
from .errors import unauthorized, forbidden

auth = HTTPBaseAuth()

#除接受普通的密令，还接受令牌认证
@auth.verify_password
def verify_password(email_or_token, password):
    #将通过验证的用户保存的flask的全局对象g中
    if email_or_token == '':
        #匿名登录，AnonymousUser类实例赋值给 g.current_user
        g.current_user = AnonymousUser()
        return True
    
    if password == '':
        #令牌验证
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True #表示使用token
        return g.current_user is not None

    user = User.query.filter_by(email=email).first()

    if not user:
        return False

    g.current_user = user
    g.token_used = False #表示未使用token

    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    #拒绝已通过验证但未确认账户的用户
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('Unconfirmed account')



#将令牌返回给路由
@api.route('/token')
def get_token():
    
    if g.current_user.is_anonymous() or g.token_used:
        #匿名用户或令牌被使用
        return unauthorized('Invalid credentials')
    #生成令牌返回给用户
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
