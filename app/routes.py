import csv
from io import StringIO
from flask import (Blueprint, Response, flash, redirect, render_template, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from app import db
from app.forms import IdeaForm, ImportForm, LoginForm, RegisterForm, SearchForm
from app.models import Idea, User
from flask_paginate import Pagination, get_page_args


bp = Blueprint('main', __name__)




@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('main.register'))
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!', 'success')
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
        flash('Invalid username or password', 'danger')
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
        tags = [t.strip().lower() for t in form.tags.data.split(',') if t.strip()]
        for tag in tags:
            ideas = ideas.filter(Idea.tags.contains(tag))
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 10
    total = ideas.count()
    ideas = ideas.order_by(Idea.timestamp.desc()).offset(offset).limit(per_page).all()
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
    return render_template('index.html', title='Dashboard', ideas=ideas, form=form, pagination=pagination)
"""
        [route for create,update and remove ideas] 
"""
@bp.route('/ideas', methods=['GET'])
@login_required
def ideas():
    return redirect(url_for('main.index'))

@bp.route('/idea/new', methods=['GET', 'POST'])
@login_required
def new_idea():
    form = IdeaForm()
    if form.validate_on_submit():
        idea = Idea(title=form.title.data, description=form.description.data, tags=form.tags.data, author=current_user)
        idea.status = form.status.data
        db.session.add(idea)
        db.session.commit()
        flash('Idea added!', 'success')
        return redirect(url_for('main.index'))
    return render_template('idea_form.html', form=form)

@bp.route('/idea/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_idea(id):
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash('Not authorized', 'danger')
        return redirect(url_for('main.index'))
    form = IdeaForm(obj=idea)
    if form.validate_on_submit():
        idea.title = form.title.data
        idea.description = form.description.data
        idea.tags = form.tags.data
        idea.status = form.status.data
        db.session.commit()
        flash('Idea updated!', 'success')
        return redirect(url_for('main.index'))
    return render_template('idea_form.html', form=form, idea=idea)

@bp.route('/idea/<int:id>/delete', methods=['POST'])
@login_required
def delete_idea(id):
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash('Not authorized', 'danger')
        return redirect(url_for('main.index'))
    db.session.delete(idea)
    db.session.commit()
    flash('Idea deleted!', 'success')
    return redirect(url_for('main.index'))


# exporter en csv
@bp.route('/ideas/export', methods=['GET'])
@login_required
def export_ideas():
    ideas = Idea.query.filter_by(user_id=current_user.id).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Description', 'Tags', 'Date'])
    for idea in ideas:
        writer.writerow([idea.title, idea.description, idea.tags, idea.timestamp.strftime('%Y-%m-%d %H:%M')])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=ideas.csv'}
    )


@bp.route('/ideas/import', methods=['GET', 'POST'])
@login_required
def import_ideas():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        reader = csv.DictReader(StringIO(file.read().decode('utf-8')))
        for row in reader:
            idea = Idea(
                title=row['Title'],
                description=row.get('Description', ''),
                tags=row.get('Tags', ''),
                status=row.get('Status', 'Draft'),
                author=current_user
            )
            db.session.add(idea)
        db.session.commit()
        flash('Ideas imported successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('import.html', form=form, title='Import Ideas')

# route for calendar view
@bp.route('/calendar', methods=['GET'])
@login_required
def calendar_view():
    ideas = Idea.query.filter_by(user_id=current_user.id).all()
    return render_template('calendar.html', ideas=ideas, title='Calendar View')
