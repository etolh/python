from flask import jsonify, request, g, abort, url_for, current_app
from .. import db
from ..models import Post, Permission
from . import api
from .decorators import permission_required
from .errors import forbidden

#实现资源断点:Post资源

#获取Posts资源, posts后面的斜杠表示获取整个资源
@api.route('/posts/')
@auth.login_required
def get_posts():
    posts = Post.query.all()
    return jsonify({'posts':[ post.to_json() for post in posts] })


@api.route('/posts/<int:id>')
@auth.login_required
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())


#将post请求中json格式转换为Post插入数据库
@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    #从request获取数据转化为post
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()

    #返回201和为Post创建的url
    return jsonify(post.to_json()), 201, \
        {'Location': url_for('api.get_post', id=post.id, _external=True)}