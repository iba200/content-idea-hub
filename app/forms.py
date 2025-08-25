from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, Length

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class IdeaForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    tags = StringField('Tags (comma-separated)', validators=[Length(max=200)])
    status = SelectField('Status', choices=[('Draft', 'Draft'), ('To Film', 'To Film'), ('Published', 'Published')], default='Draft')
    submit = SubmitField('Save')

    def validate_tags(self, tags):
        if tags.data:
            tags.data = ','.join([t.strip().lower() for t in tags.data.split(',') if t.strip()])



class SearchForm(FlaskForm):
    tags = StringField('Filter by Tags')
    submit = SubmitField('Search')



class ImportForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Import')
