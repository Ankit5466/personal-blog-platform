from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import json
import math
from datetime import datetime

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

# flask app, connection with database
local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Posts(db.Model):
    s_no = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(12), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(20), nullable=True)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def index():
    posts = Posts.query.all()
    total_posts = len(posts)
    page = request.args.get('page', default=1, type=int)
    if page < 1:
        page = 1
    if total_posts == 0 or params['no_of_posts'] == 0:
        # Handle the case where there are no posts or no posts per page
        return render_template('index.html', params=params, posts=[], old="#", new="#")
    last = math.ceil(total_posts / params['no_of_posts'])
    if page > last:
        page = last
    start_index = (page - 1) * params['no_of_posts']
    end_index = min(start_index + params['no_of_posts'], total_posts)
    posts = posts[start_index:end_index]
    old = "#" if page == 1 else "/?page=" + str(page - 1)
    new = "#" if page == last else "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, old=old, new=new)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_rout(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/edit/<string:s_no>", methods = ['GET', 'POST'])
def edit(s_no):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if s_no == '0':
                post = Posts(title=box_title, tagline=tagline, slug=slug, content=content, img_file=img_file, date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(s_no=s_no).first()
                post.title = box_title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+s_no)
        post = Posts.query.filter_by(s_no=s_no).first()
        return render_template('edit.html', params=params, s_no=s_no, post=post)

@app.route("/delete/<string:s_no>", methods = ['GET', 'POST'])
def delete(s_no):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(s_no=s_no).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
    return render_template('login.html', params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/login')


app.run(debug=True)