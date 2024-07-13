# wtform form
from wtforms.widgets import TextInput
from wtforms.validators import DataRequired
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf import FlaskForm
# textarea
from flask_ckeditor import CKEditor, CKEditorField


class BootstrapTextInput(TextInput):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class', 'form-control')
        return super().__call__(field, **kwargs)


class PostForm(FlaskForm):
    title = StringField(label='Title', widget=BootstrapTextInput(), validators=[DataRequired()])
    subtitle = StringField(label='Subtitle', widget=BootstrapTextInput(), validators=[DataRequired()])
    img_url = StringField(label='Image URL', widget=BootstrapTextInput(), validators=[DataRequired()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField(label="Submit", render_kw={'class': 'btn btn-primary'})


# user form
class RegisterForm(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()])
    email = StringField(label='Email', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    register = SubmitField(label="Register", render_kw={'class': 'btn btn-primary'})


class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    login = SubmitField(label="Login", render_kw={'class': 'btn btn-primary'})


class CommentForm(FlaskForm):
    text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField(label="Submit")


class EditCommentForm(FlaskForm):
    text = CKEditorField("Edit Comment", validators=[DataRequired()])
    submit = SubmitField(label="Update")
