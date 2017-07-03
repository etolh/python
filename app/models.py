from . import db
from werkzeug.security import generate_password_hash, check_password_hash

#定义数据库表对应的模型:extends db.Model
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)

    #one2many-relations:one,backref与__tablename__对应,lazy='dynamic'禁止自动
    users = db.relationship('User', backref='role',lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),unique=True)

    #one2many-relations:many,ForeignKey与__tablename__对应
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    password_hash = db.Column(db.String(128))

    
    @property
    def password(self):
        raise Attribute('password is not a readable attribute!')


    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.name