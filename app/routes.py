from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from app import db, login_manager
from app.models import User
from app.forms import RegisterForm, LoginForm, SearchForm
from app.models import Idea
from app.forms import IdeaForm
bp = Blueprint('main', __name__)




@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form, title='Register')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid username or password')
    return render_template('login.html', form=form, title='Login')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = SearchForm()
    ideas = Idea.query.filter_by(user_id=current_user.id)
    if form.validate_on_submit() and form.tags.data:
        tags = [t.strip() for t in form.tags.data.split(',')]
        for tag in tags:
            ideas = ideas.filter(Idea.tags.like(f'%{tag}%'))
    ideas = ideas.order_by(Idea.timestamp.desc()).all()
    return render_template('index.html', ideas=ideas, form=form)

"""
        [route for create,update and remove ideas] 
"""
@bp.route('/ideas', methods=['GET'])
@login_required
def ideas():
    ideas = Idea.query.filter_by(user_id=current_user.id).order_by(Idea.timestamp.desc()).all()
    return render_template('index.html', ideas=ideas)  # Reuse index as dashboard

@bp.route('/idea/new', methods=['GET', 'POST'])
@login_required
def new_idea():
    form = IdeaForm()
    if form.validate_on_submit():
        idea = Idea(title=form.title.data, description=form.description.data, tags=form.tags.data, author=current_user)
        db.session.add(idea)
        db.session.commit()
        flash('Idea added!')
        return redirect(url_for('main.index'))
    return render_template('idea_form.html', form=form)

@bp.route('/idea/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_idea(id):
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash('Not authorized')
        return redirect(url_for('main.index'))
    form = IdeaForm(obj=idea)
    if form.validate_on_submit():
        idea.title = form.title.data
        idea.description = form.description.data
        idea.tags = form.tags.data
        db.session.commit()
        flash('Idea updated!')
        return redirect(url_for('main.index'))
    return render_template('idea_form.html', form=form, idea=idea)

@bp.route('/idea/<int:id>/delete', methods=['POST'])
@login_required
def delete_idea(id):
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash('Not authorized')
        return redirect(url_for('main.index'))
    db.session.delete(idea)
    db.session.commit()
    flash('Idea deleted!')
    return redirect(url_for('main.index'))

