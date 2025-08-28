import csv
from io import StringIO
import os
from flask import (
    Blueprint, Response, flash, redirect,
    render_template, url_for, request, jsonify, send_from_directory
)
from flask_login import current_user, login_required, login_user, logout_user
from app import db
from app.forms import IdeaForm, ImportForm, LoginForm, RegisterForm, SearchForm
from app.models import Idea, User
from flask_paginate import Pagination, get_page_args
from google import genai
import markdown


bp = Blueprint('main', __name__)

# ------------------ AUTH ------------------ #
@bp.route('/google98da10251afd3590.html')
def google_verification():
    return send_from_directory('static', 'google98da10251afd3590.html')


# ------------------ AUTH ------------------ #
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('❌ Username already exists', 'danger')
            return redirect(url_for('main.register'))
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('✅ Registered successfully! You can now log in.', 'success')
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
        flash('❌ Invalid username or password', 'danger')
    return render_template('login.html', form=form, title='Login')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for('main.login'))


# ------------------ DASHBOARD ------------------ #
@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = SearchForm()
    ideas = Idea.query.filter_by(user_id=current_user.id)

    # recherche par tags
    if form.validate_on_submit() and form.tags.data:
        tags = [t.strip().lower() for t in form.tags.data.split(',') if t.strip()]
        for tag in tags:
            ideas = ideas.filter(Idea.tags.contains(tag))

    # pagination
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 10
    total = ideas.count()
    ideas = ideas.order_by(Idea.timestamp.desc()).offset(offset).limit(per_page).all()
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')

    return render_template('index.html', title='Dashboard', ideas=ideas, form=form, pagination=pagination)


# ------------------ IDEAS CRUD ------------------ #
@bp.route('/idea/<int:id>')
@login_required
def idea_detail(id):
    """Vue d’une idée spécifique"""
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash("⛔ Not authorized.", "danger")
        return redirect(url_for('main.index'))
    return render_template('idea_detail.html', idea=idea)


@bp.route('/idea/new', methods=['GET', 'POST'])
@login_required
def new_idea():
    form = IdeaForm()
    if form.validate_on_submit():
        idea = Idea(
            title=form.title.data,
            description=form.description.data,
            tags=form.tags.data,
            status=form.status.data,
            author=current_user
        )
        db.session.add(idea)
        db.session.commit()
        flash('✅ Idea added!', 'success')
        return redirect(url_for('main.index'))
    return render_template('idea_form.html', form=form)


@bp.route('/idea/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_idea(id):
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash('⛔ Not authorized', 'danger')
        return redirect(url_for('main.index'))
    form = IdeaForm(obj=idea)
    if form.validate_on_submit():
        idea.title = form.title.data
        idea.description = form.description.data
        idea.tags = form.tags.data
        idea.status = form.status.data
        db.session.commit()
        flash('✅ Idea updated!', 'success')
        return redirect(url_for('main.index'))
    return render_template('idea_form.html', form=form, idea=idea)


@bp.route('/idea/<int:id>/delete', methods=['POST'])
@login_required
def delete_idea(id):
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash('⛔ Not authorized', 'danger')
        return redirect(url_for('main.index'))
    db.session.delete(idea)
    db.session.commit()
    flash('🗑️ Idea deleted!', 'success')
    return redirect(url_for('main.index'))


@bp.route('/idea/<int:id>/duplicate', methods=['POST'])
@login_required
def duplicate_idea(id):
    """Permet de copier une idée en brouillon"""
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash('⛔ Not authorized', 'danger')
        return redirect(url_for('main.index'))
    copy = Idea(
        title=idea.title + " (copy)",
        description=idea.description,
        tags=idea.tags,
        status="Draft",
        author=current_user
    )
    db.session.add(copy)
    db.session.commit()
    flash("📑 Idea duplicated as draft.", "info")
    return redirect(url_for('main.index'))


# ------------------ EXPORT / IMPORT ------------------ #
@bp.route('/ideas/export', methods=['GET'])
@login_required
def export_ideas():
    ideas = Idea.query.filter_by(user_id=current_user.id).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Description', 'Tags', 'Status', 'Date'])
    for idea in ideas:
        writer.writerow([idea.title, idea.description, idea.tags, idea.status, idea.timestamp.strftime('%Y-%m-%d %H:%M')])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=ideas.csv'}
    )


@bp.route('/ideas/<int:id>/export_md')
@login_required
def export_markdown(id):
    """Exporter une idée unique en Markdown"""
    idea = Idea.query.get_or_404(id)
    if idea.author != current_user:
        flash('⛔ Not authorized', 'danger')
        return redirect(url_for('main.index'))
    md_content = f"# {idea.title}\n\n{idea.description}\n\n**Tags:** {idea.tags}\n**Status:** {idea.status}"
    return Response(
        md_content,
        mimetype='text/markdown',
        headers={'Content-Disposition': f'attachment; filename=idea_{id}.md'}
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
        flash('✅ Ideas imported successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('import.html', form=form, title='Import Ideas')


# ------------------ CALENDAR ------------------ #
@bp.route('/calendar')
@login_required
def calendar():
    ideas = Idea.query.filter_by(user_id=current_user.id).order_by(Idea.timestamp.desc()).all()
    print(f"Utilisateur: {current_user.id}")
    print(f"Nombre d'idées trouvées: {len(ideas)}")
    for idea in ideas:
        print(f"Idée: {idea.title}, Date: {idea.timestamp}, Status: {idea.status}")
    return render_template('calendar.html', title='Calendar', ideas=ideas)

# ------------------ CALENDAR DEBUG ------------------ #
@bp.route('/debug/ideas')
@login_required
def debug_ideas():
    ideas = Idea.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': idea.id,
        'title': idea.title,
        'status': idea.status,
        'timestamp': idea.timestamp.isoformat()
    } for idea in ideas])
# ------------------ AI SUGGESTIONS ------------------ #
@bp.route('/idea/suggest', methods=['GET', 'POST'])
@login_required
def suggest_idea():
    form = SearchForm()
    suggestions = []
    if form.validate_on_submit() and form.tags.data:
        tags = form.tags.data
        client = genai.Client(api_key="AIzaSyDmeXKxN1lCxwsyua5zCZm3pK44_a08fdI")
        prompt = f"Suggest creative content ideas for these tags: {tags}. Return a list of hashtags and titles."
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        if response and hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            # Convert suggestion to markdown
                            md_text = markdown.markdown(part.text)
                            suggestions.append(md_text)
        return render_template('suggest_results.html', suggestions=suggestions, tags=tags)
    return render_template('suggest.html', form=form, title='Suggest Ideas')

@bp.route('/idea/create_from_suggestion', methods=['POST'])
@login_required
def create_from_suggestion():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    idea = Idea(
        title=data.get('title'),
        description=data.get('description'),
        tags=data.get('tags', ''),
        status=data.get('status', 'Draft'),
        author=current_user
    )
    db.session.add(idea)
    db.session.commit()
    return jsonify({"success": True, "id": idea.id})


# ------------------ ABOUT ------------------ #
@bp.route('/about')
def about():
    """Page À propos"""
    return render_template('about.html', title='About')
# ------------------ FAQ ------------------ #
@bp.route('/faq')
def faq():
    """Page FAQ"""
    return render_template('faq.html', title='FAQ')

# ------------------ ROBOTS AND SITEMAP ------------------ #

@bp.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@bp.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')