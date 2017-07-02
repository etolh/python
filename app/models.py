from . import db


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

    def __repr__(self):
        return '<User %r>' % self.name