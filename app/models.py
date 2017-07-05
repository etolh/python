from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


#定义数据库表对应的模型:extends db.Model
class Role(db.Model):
    
    __tablename__ = 'role'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)
    #设置默认角色，当Role为True时为默认角色（只有一个）
    default = db.Column(db.Boolean, default=False,index=True)
    # 位标志，表示角色能进行的操作
    permissions = db.Column(db.Integer)
    #one2many-relations:one,backref与__tablename__对应,lazy='dynamic'禁止自动
    users = db.relationship('User', backref='role',lazy='dynamic')

    #自动将角色加入数据库
    @staticmethod
    def insert_roles():
        roles = {
            #普通角色，默认
            'User': (Permission.FOLLOW |
                Permission.COMMENT |
                Permission.WRITE_ARTICLES, True),
            #协管员
            'Moderator':(Permission.FOLLOW |
                Permission.COMMENT |
                Permission.WRITE_ARTICLES |
                Permission.MODERATE_COMMENTS, False),
            #管理员
            'Administator': (0xff,False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                #数据库查找，若无则创建角色
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class User(UserMixin,db.Model):
    
    __tablename__ = 'User'
    
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(64),unique=True,index=True)
    name = db.Column(db.String(64),unique=True,index=True)
    realname = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    #one2many-relations:many,ForeignKey与__tablename__对应
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    password_hash = db.Column(db.String(128))

    #刷新用户访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    #构造函数中赋予用户角色
    def __init__(self,**kw):
        super(User,self).__init__(**kw)

        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                #注册邮箱为管理员邮箱,设为管理员角色
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                #默认为普通角色
                self.role = Role.query.filter_by(default=True).first()


    #验证用户是否具有指定权限
    def can(self,permissions):
        #比较用户的权限与需要的权限permissions是否一致：&
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions


    #验证是否是管理员
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    #password_hash列是根据password属性生成的
    @property
    def password(self):
        raise Attribute('password is not a readable attribute!')


    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash, password)

    #用户激活状态
    confirmed = db.Column(db.Boolean,default=False)

    #生成激活令牌
    def generate_confirmation_token(self,expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'],expires_in = 3600)
        return s.dumps({'confirm':self.id})

    #激活
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'],expires_in = 3600)
        try:
            data = s.loads(token)
        except:
            return False
        
        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)
        return True

    #生成重设密码令牌
    def generate_password_token(self,expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'],expires_in = 3600)
        return s.dumps({'confirm':self.id})

    #重设密码验证，并更新用户密码
    def resetpassword(self, newpassword, token):
        s = Serializer(current_app.config['SECRET_KEY'],expires_in = 3600)
        try:
            data = s.loads(token)
        except:
            return False
        
        if data.get('confirm') != self.id:
            return False

        #确认为当前用户，更新
        self.password = newpassword
        db.session.add(self)
        return True


    #生成修改邮箱令牌
    def generate_email_token(self,newemail,expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'],expires_in = 3600)
        return s.dumps({'change_email':self.id,'newemail':newemail})

    #验证令牌
    def confirmed_email(self,token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)   #由令牌得到邮箱信息
        except:
            return False

        if data.get('change_email') != self.id:
            return False

        newemail = data.get('newemail')

        if newemail is None or self.query.filter_by(email=newemail).first() is not None:
            #未获得新邮箱或新邮箱已存在于数据库中，均验证失败
            return False

        #验证成功，更新用户
        self.email = newemail
        db.session.add(self)
        # db.session.commit()
        return True

    def __repr__(self):
        return '<User %r>' % self.name

#验证匿名用户（未登录）
class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

