from hello import User, Role, db

#创建数据库中的表 db相当于数据库在python的映射，定义的模型（继承db）即为库的的表
db.create_all()
#删除所有表
db.drop_all()

#插入：先在python中创建对象，此时并未提交到数据库，
#只有插入到db的事务session中并进行提交后，才能形成对数据库的操作
admin_role = Role(name='Admin')
mod_role = Role(name='Moderator')
user_role = Role(name='User')
user_john = User(name='john',role=admin_role)
user_susan = User(name='susan',role=user_role)
user_david = User(name='david',role=user_role)
print(admin_role.id)    #None

#添加到会话
db.session.add(admin_role)
db.session.add(mod_role)
db.session.add(user_role)
db.session.add(user_john)
db.session.add(user_susan)
db.session.add(user_david)
#提交
db.session.commit()
print(admin_role.id)    #1

#修改
admin_role.name='Administrator'
db.session.add(admin_role)
db.session.commit()
#删除表中数据
db.session.delete(mod_role)
db.session.commit()

#对表的insert、update、delete的操作，都需要进行提交才能完成对数据库本身的操作，否则只是对python对象的操作


#查询
Role.query.all()
User.query.all()

#添加过滤器
User.query.filter_by(role=user_role).all()
user_role = Role.query.filter_by(name='User').first()

# 自动执行查询关联的表
users = user_role.users
print(users)
print(users[0].role)

#非自动执行，添加过滤器
users = user_role.users.order_by(User.name).all()
print(users)
print(user_role.users.count())