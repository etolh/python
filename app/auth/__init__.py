from flask import Blueprint
#创建蓝本
auth = Blueprint('auth', __name__)

#将app/auth/views.py即视图函数引入蓝本，末尾导入避免循环依赖
from . import views