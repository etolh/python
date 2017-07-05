from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#定义数据库表对应的模型:extends db.Model
class Role(db.Model):
    
    __tablename__ = 'role'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)

    #one2many-relations:one,backref与__tablename__对应,lazy='dynamic'禁止自动
    users = db.relationship('User', backref='role',lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(UserMixin,db.Model):
    
    __tablename__ = 'User'
    
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(64),unique=True,index=True)
    name = db.Column(db.String(50),unique=True,index=True)

    #one2many-relations:many,ForeignKey与__tablename__对应
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    password_hash = db.Column(db.String(128))

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