import hashlib
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from datetime import datetime
from markdown import markdown
import bleach

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
    #one2many-relations:one,backref与外键名称对应,lazy='dynamic'禁止自动
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

#多对多关系形成的中间表
class Follow(db.Model):
    __tablename__ = 'follows'

    #关注者id
    follower_id = db.Column(db.Integer, db.ForeignKey('User.id'),
            primary_key=True)
    #被关注者id
    followed_id = db.Column(db.Integer, db.ForeignKey('User.id'),
            primary_key=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


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
    #用户激活状态
    confirmed = db.Column(db.Boolean,default=False)
    #使用缓存的md5散列计算生成的gravatar-url
    avatar_hash = db.Column(db.String(32))
    #一对多：一方
    posts = db.relationship('Post',backref='author',lazy='dynamic')

    #关注者的一对多：一方
    followed = db.relationship('Follow',
        foreign_keys=[Follow.follower_id],
        #回引Follow模型
        backref=db.backref('follower',lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan')

    #被关注者的一对多关系：
    followers = db.relationship('Follow',
        foreign_keys=[Follow.followed_id],
        backref=db.backref('followed',lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan')


    #构造函数中赋予用户角色
    def __init__(self,**kw):
        super(User,self).__init__(**kw)

        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                #注册邮箱为管理员邮箱,设为管理员角色
                self.role = Role.query.filter_by(
                    permissions=0xff).first()
            if self.role is None:
                #默认为普通角色
                self.role = Role.query.filter_by(
                    default=True).first()

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    #生成虚拟数据
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                name=forgery_py.internet.user_name(True),
                password=forgery_py.lorem_ipsum.word(),
                confirmed=True,
                realname=forgery_py.name.full_name(),
                location=forgery_py.address.city(),
                about_me=forgery_py.lorem_ipsum.sentence(),
                member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()

    #生成邮箱对应的图像
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        #若已保存，则使用保存的avatar_hash
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, hash=hash, size=size, default=default, rating=rating)



    #刷新用户访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

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
        
        #根据email生成gravatar的url
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()

        db.session.add(self)
        # db.session.commit()
        return True

    #关注关系的辅助函数
    #关注user
    def follow(self, user):
        if not self.is_following(user):
            #未关注user，则self对user关注，设置中间对象，加入数据库
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    #取消关注user
    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    #是否为关注状态:self是否关注user
    def is_following(self, user):
        #查找self关注的对象是否有user
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    #self是否被user关注
    def is_followed_by(self, user):
        #查找self的关注者中是否有user
        return self.followers.filter_by(
            follower_id=user_id).first() is not None



    def __repr__(self):
        return '<User %r>' % self.name

#验证匿名用户（未登录）
class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

class Post(db.Model):
    #文章--表

    __tablename__ = 'posts'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #多对一外键
    author_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    #保存生成的html
    body_html = db.Column(db.Text)

    #当Post中的body发送变化，将body字段的文本经过markdown生成html再保存在数据库中
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        #允许的html标签
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                    'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                    'h1', 'h2', 'h3', 'p']
        #生成的html保存到body_html
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), 
            tags=allowed_tags, strip=True))


    #生成虚拟列表
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                    timestamp=forgery_py.date.date(True),
                    author=u)
            db.session.add(p)
            db.session.commit()
    
#将Post的on_changed_body函数绑定在Post的body字段上，当body发生变化时，自动调用函数
db.event.listen(Post.body, 'set', Post.on_changed_body)



