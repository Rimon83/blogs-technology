from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey

# flask login
from flask_login import UserMixin, login_user
import os


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def database_config(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_CONNECT")
    db.init_app(app)
    return db


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post_comment")


# Create a User table for all your registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    posts = relationship("BlogPost", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author_comment", cascade="all, delete-orphan")


# comment table that each user has many comments and each post has many comments
class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_posts.id"), nullable=False)
    author_comment = relationship("User", back_populates="comments")
    post_comment = relationship("BlogPost", back_populates="comments")


# read all posts
def read_all_posts():
    result = db.session.execute(db.select(BlogPost).order_by(BlogPost.title))
    posts = result.scalars()
    return posts


# read specific post by id
def read_post_by_id(post_id):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    return post


# create new post
def insert_new_post(form):
    post = BlogPost(title=form["title"], author_id=form["author_id"], subtitle=form["subtitle"],
                    img_url=form["img_url"],
                    body=form["body"],
                    date=form["date"])
    db.session.add(post)
    db.session.commit()


# edit specific post
def edit_one_post(old_post, new_post):
    old_post.title = new_post.title.data
    old_post.subtitle = new_post.subtitle.data
    old_post.img_url = new_post.img_url.data
    old_post.body = new_post.body.data
    db.session.commit()


# create new user
def insert_new_user(form):
    new_user = User(email=form["email"], name=form["name"], password=form["hashed_password"])

    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)


# read user by email
def read_user_by_email(email):
    result = db.session.execute(db.select(User).where(User.email == email))
    user = result.scalar()
    return user


# read specific comment by id
def read_comment_by_id(comment_id):
    result = db.session.execute(db.select(Comment).where(Comment.id == comment_id))
    comment = result.scalars()
    return comment


# edit specific post
def edit_one_comment(old_comment, new_comment):
    old_comment.text = new_comment["text"]
    db.session.commit()

# insert one comment
def insert_comment(data):
    comment = Comment(text=data["text"], author_id=data["author_id"], post_id=data["post_id"])
    db.session.add(comment)
    db.session.commit()
