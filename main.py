from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import requests
import smtplib
# password hash
from werkzeug.security import generate_password_hash, check_password_hash

from flask_bootstrap import Bootstrap5
# textarea
from flask_ckeditor import CKEditor
# custom form model
from forms import PostForm, RegisterForm, LoginForm, CommentForm, EditCommentForm
from models import (database_config, read_all_posts, read_post_by_id, insert_new_post, edit_one_post,
                    insert_new_user, read_user_by_email, User, Comment, read_comment_by_id, edit_one_comment,
                    insert_comment)
#login flask
from flask_login import login_user, LoginManager, current_user, logout_user
from functools import wraps
from flask import abort
from flask_gravatar import Gravatar
import os
from icons import edit_icon, delete_icon


#Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# update login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# USE YOUR OWN npoint LINK!
# posts = requests.get("https://api.npoint.io/c790b4d5cab58020d391").json()

# '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app = Flask(__name__)
ckeditor = CKEditor(app)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
bootstrap = Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)

# initialize avatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

db = database_config(app)
with app.app_context():
    db.create_all()

# set email sending
my_email = os.environ.get('EMAIL')
password = os.environ.get('PASSWORD')


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route('/')
def get_all_posts():
    user = None
    # print(current_user.__dict__)
    posts = read_all_posts()
    if current_user.is_authenticated:
        user = current_user
    return render_template("index.html",
                           all_posts=posts,
                           user=user)


@app.route("/about")
def about():
    user = None
    posts = read_all_posts()
    if current_user.is_authenticated:
        user = current_user
    return render_template("about.html", user=user)


@app.route("/contact", methods=['POST', 'GET'])
def contact():
    user = None
    if current_user.is_authenticated:
        user = current_user
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]

        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            # make the connection secure
            connection.starttls()

            # login in account
            connection.login(user=my_email, password=password)

            # send email to others
            connection.sendmail(from_addr=my_email,
                                to_addrs=email,
                                msg=f"Subject: get Details\n\n Name: {name} \nEmail: {email}\nPhone: {phone}\nMessage: {message}")
        return f"<h1>successfully sent your message</h1>"
    else:
        return render_template("contact.html", user=user)


@app.route("/post", methods=["GET", "POST"])
def show_post():
    # API
    # requested_post = None
    # for blog_post in posts:
    #     if blog_post["id"] == index:
    #         requested_post = blog_post

    # database
    post = read_post_by_id(request.args.get('post_id'))
    comment_form = CommentForm()
    edit_comment_form = EditCommentForm()
    if current_user.is_authenticated:
        user = current_user
    else:
        flash("You need to login or register to comment.")
        return redirect(url_for("login"))

    if request.method == "POST":
        if comment_form.validate_on_submit():
            data = request.form.to_dict()
            data["author_id"] = current_user.id
            data["post_id"] = post.id
            insert_comment(data)

            return redirect(url_for("show_post", post_id=post.id))
    return render_template("post.html",
                           post=post,
                           form=comment_form,
                           edit_comment_form=edit_comment_form,
                           user=user,
                           edit_icon=edit_icon,
                           delete_icon=delete_icon)


# create new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def new_post():
    user = None
    if current_user.is_authenticated:
        user = current_user
    date = datetime.datetime.now()
    formatted_date = date.strftime("%B %d, %Y")

    form = PostForm()
    if form.validate_on_submit():
        # Convert form data to a dictionary
        new_data_form = request.form.to_dict()
        # Add the formatted date to the dictionary
        new_data_form["date"] = formatted_date
        new_data_form["author_id"] = current_user.id
        # Insert new post with the updated dictionary
        insert_new_post(new_data_form)
        return redirect(url_for("get_all_posts"))
    return render_template("make_post.html", form=form, user=user)


#edit route
@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    user = None
    if current_user.is_authenticated:
        user = current_user
    # Edit the post
    if post_id:
        post = read_post_by_id(post_id)
        form = PostForm(obj=post)
        if form.validate_on_submit():
            edit_one_post(post, form)
            return redirect(url_for("show_post", post_id=post.id))
        return render_template("make_post.html", form=form, post_id=post_id, user=user)


# delete post route
@app.route("/delete")
@admin_only
def delete_post():
    post_id = request.args.get("post_id")
    post_to_delete = read_post_by_id(post_id)

    # Delete all comments associated with the post
    comments_to_delete = read_comment_by_id(post_id)
    for comment in comments_to_delete.all():
        db.session.delete(comment)

    db.session.delete(post_to_delete)
    db.session.commit()

    return redirect(url_for('get_all_posts'))


#register route
@app.route("/register", methods=["GET", "POST"])
def register():
    user = None
    if current_user.is_authenticated:
        user = current_user
    form = RegisterForm()
    if form.validate_on_submit():
        register_password = request.form["password"]
        email = request.form["email"]
        user = read_user_by_email(email)
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        # Hashing and salting the password entered by the user
        hash_and_salted_password = generate_password_hash(
            register_password,
            method='pbkdf2:sha256',
            salt_length=8
        )
        register_data = request.form.to_dict()
        register_data["hashed_password"] = hash_and_salted_password
        insert_new_user(register_data)
        return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=form, user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    user = None
    if current_user.is_authenticated:
        user = current_user
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')
        user = read_user_by_email(email)
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            print("login successfully")
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form, user=user)


# logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/edit_comment", methods=["GET", "POST"])
@login_required
def edit_comment():
    if current_user.is_authenticated:
        user = current_user
    else:
        flash("You need to login or register to comment.")
        return redirect(url_for("login"))
    post = read_post_by_id(request.args.get('post_id'))
    comment = read_comment_by_id(request.args.get('comment_id'))
    comment_form = CommentForm()
    edit_comment_form = EditCommentForm(obj=comment)
    if request.method == "POST" and edit_comment_form.validate_on_submit():
        if comment and comment.author_id == current_user.id:
            edit_one_comment(comment, request.form)
            return redirect(url_for("show_post", post_id=post.id))
    return render_template("post.html",
                           post=post,
                           form=comment_form,
                           edit_comment_form=edit_comment_form,
                           user=user)


@app.route("/delete_comment")
@login_required
def delete_comment():
    post_id = request.args.get("post_id")
    comment_id = request.args.get("comment_id")
    comment_to_delete = read_comment_by_id(comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for("show_post", post_id=post_id))


if __name__ == "__main__":
    app.run(debug=True)
