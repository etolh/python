from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from . import main
from flask.ext.moment import Moment  #本地化时间
from datetime import datetime
from ..models import User, Role, Post, Comment
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from flask_login import login_required, current_user
from .. import db
from ..decorators import admin_required, permission_required
from ..models import Permission


@main.route('/',methods=['GET','POST'])
def index():
    form = PostForm()

    if current_user.can(Permission.WRITE_ARTICLES) and \
        form.validate_on_submit():
        #用户有写文章权限，且已提交，参数author即为当前用户
        post = Post(body=form.body.data,
            author=current_user._get_current_object())
        db.session.add(post)

        return redirect(url_for('.index'))

    #分页：page表示当前显示的页数
    page = request.args.get('page', 1, type=int)
    #获取所关注用户的Post --query
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    #show_followed决定是显示所有文章，还是显示所关注用户的文章
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query

    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           pagination=pagination)


#用户资料页面路由
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(name=username).first()
    if user is None:
        abort(404)

    #分页：page表示当前显示的页数
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    return render_template('user.html',user=user, posts=posts,
                    pagination=pagination)

#资料编辑路由
@main.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        #更新用户资料
        current_user.realname = form.realname.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.user',username=current_user.name))

    form.realname.data = current_user.realname
    form.location.data = current_user.about_me
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form)

#管理员资料编辑路由
@main.route('/edit_profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    #由视图函数传入的id查找用户
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    
    if form.validate_on_submit():
        #更新用户资料
        user.email = form.email.data
        user.name = form.name.data
        user.confirmed = form.confirmed.data
        #role_id属性被赋值给form.role.data，利用form.role.data从数据库加载角色
        user.role = Role.query.get(form.role.data)
        user.realname = form.realname.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.user',username=user.name))

    form.email.data = user.email
    form.name.data = user.name
    form.confirmed.data = user.confirmed
    #赋值时role_id赋给form中的role属性
    form.role.data = user.role_id
    form.realname.data = user.realname
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html',form=form,user=user)


#文章固定连接 13:在文章页面增加评论显示
@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    #由Post的id得到指定的Post
    post = Post.query.get_or_404(id)
    #评论表单
    form = CommentForm()

    if form.validate_on_submit():
        #评论表单提交，创建评论提交到数据库,current_user为context代理对象，通过_get_current_object()获取真正对象
        comment = Comment(body=form.body.data, post=post, 
            author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        #page设为-1，表示为最后一页，能显示刚提交的评论
        return redirect(url_for('.post', id=post.id, page=-1))

    #分页显示评论
    page = request.args.get('page', 1, type=int)

    if page == -1:
        #设为最后一页
        page = (post.comments.count() - 1) / current_app.\
            config['FLASKY_COMMENTS_PER_PAGE'] + 1

    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(
            page=page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items

    return render_template('post.html', posts=[post], 
        form=form, comments=comments, pagination=pagination)


#用户或管理员编辑文章
@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    
    if current_user != post.author and \
        not current_user.can(Permission.ADMINISTER):
        #用户不是当前post用户，或非管理员
        abort(403)

    form = PostForm()

    if form.validate_on_submit():
        #修改，提交数据库
        post.body = form.body.data
        db.session.add(post)
        flash('You have updated your post')
        #返回文章界面
        return redirect(url_for('.post', id=post.id))

    #未修改，默认为原内容
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

#关注username
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(name=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user')
        return redirect(url_for('.user',username=username))

    current_user.follow(user)
    flash('You are now following %s' % username)
    return redirect(url_for('.user',username=username)) 



#取消关注
@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(name=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not followed this user')
        return redirect(url_for('.user',username=username))

    current_user.unfollow(user)
    flash('You are now unfollowing %s' % username)
    return redirect(url_for('.user',username=username))

#关注用户的用户数和列表
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(name=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp':item.timestamp}
        for item in pagination.items]
    return render_template('followers.html',user=user, title='Followers of',
            endpoint='.followers', pagination=pagination,
            follows=follows)

#用户关注的用户列表
@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(name=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp':item.timestamp}
        for item in pagination.items]
    return render_template('followers.html',user=user, title='Followed by',
            endpoint='.followed_by', pagination=pagination,
            follows=follows)

#决定显示所有还是所关注用户
@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp