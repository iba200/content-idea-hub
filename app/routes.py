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
from app.models import Idea, User, Setting
from app.utils.settings_manager import get_setting
from datetime import timedelta, datetime
from flask import current_app, session
from flask_paginate import Pagination, get_page_args
from google import genai
import os
from app import limiter
import markdown


bp = Blueprint('main', __name__)


# ------------------ AUTH ------------------ #
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        # Settings: allow registration
        if get_setting('allow_registration', 'on') != 'on':
            flash('⛔ Registration is currently disabled by the administrator.', 'danger')
            return redirect(url_for('main.login'))
        # Settings: password min length
        try:
            min_len = int(get_setting('password_min_length', '8'))
        except Exception:
            min_len = 8
        if len(form.password.data or '') < min_len:
            flash(f'❌ Password must be at least {min_len} characters.', 'danger')
            return redirect(url_for('main.register'))
        if User.query.filter_by(username=form.username.data).first():
            flash('❌ Username already exists', 'danger')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=form.email.data).first():
            flash('❌ Email already registered', 'danger')
            return redirect(url_for('main.register'))
        
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        # Generate verification token
        from app.utils.email_manager import EmailManager
        email_manager = EmailManager()
        user.email_verification_token = email_manager.generate_verification_token(form.email.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        if email_manager.send_verification_email(user):
            flash('✅ Registration successful! Please check your email to verify your account.', 'success')
        else:
            flash('⚠️ Registration successful, but verification email could not be sent. Please contact support.', 'warning')
        
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form, title='Register')


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            # Check if email is verified
            if not user.email_verified:
                flash('❌ Please verify your email address before logging in. Check your inbox for the verification link.', 'warning')
                return redirect(url_for('main.login'))
            
            login_user(user)
            # Apply session timeout from settings (minutes)
            try:
                minutes = int(get_setting('session_timeout', '30'))
            except Exception:
                minutes = 30
            current_app.permanent_session_lifetime = timedelta(minutes=minutes)
            session.permanent = True
            # Update last_seen if logging enabled
            if get_setting('log_user_activity', 'on') == 'on':
                user.last_seen = datetime.utcnow()
                db.session.commit()
            return redirect(url_for('main.index'))
        flash('❌ Invalid username or password', 'danger')
    return render_template('login.html', form=form, title='Login')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for('main.login'))


@bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify user email with token."""
    from app.utils.email_manager import EmailManager
    email_manager = EmailManager()
    
    email = email_manager.verify_token(token, 'email-verification')
    if email is None:
        flash('❌ Invalid or expired verification link.', 'danger')
        return redirect(url_for('main.login'))
    
    user = User.query.filter_by(email=email).first()
    if user is None:
        flash('❌ User not found.', 'danger')
        return redirect(url_for('main.login'))
    
    if user.email_verified:
        flash('✅ Email already verified. You can now log in.', 'info')
        return redirect(url_for('main.login'))
    
    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()
    
    flash('✅ Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('main.login'))


@bp.route('/request-password-reset', methods=['GET', 'POST'])
def request_password_reset():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            from app.utils.email_manager import EmailManager
            email_manager = EmailManager()
            
            # Generate reset token
            user.password_reset_token = email_manager.generate_password_reset_token(form.email.data)
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send reset email
            if email_manager.send_password_reset_email(user):
                flash('✅ Password reset email sent! Check your inbox.', 'success')
            else:
                flash('⚠️ Password reset email could not be sent. Please try again later.', 'warning')
        else:
            # Don't reveal if email exists or not
            flash('✅ If the email exists, a password reset link has been sent.', 'success')
        
        return redirect(url_for('main.login'))
    
    return render_template('request_password_reset.html', form=form, title='Request Password Reset')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    from app.utils.email_manager import EmailManager
    email_manager = EmailManager()
    
    email = email_manager.verify_token(token, 'password-reset')
    if email is None:
        flash('❌ Invalid or expired reset link.', 'danger')
        return redirect(url_for('main.request_password_reset'))
    
    user = User.query.filter_by(email=email).first()
    if user is None:
        flash('❌ User not found.', 'danger')
        return redirect(url_for('main.request_password_reset'))
    
    # Check if token is expired
    if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
        flash('❌ Reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('main.request_password_reset'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash('❌ Passwords do not match.', 'danger')
            return redirect(url_for('main.reset_password', token=token))
        
        # Check password length
        try:
            min_len = int(get_setting('password_min_length', '8'))
        except Exception:
            min_len = 8
        if len(form.password.data) < min_len:
            flash(f'❌ Password must be at least {min_len} characters.', 'danger')
            return redirect(url_for('main.reset_password', token=token))
        
        user.set_password(form.password.data)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        flash('✅ Password reset successfully! You can now log in with your new password.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('reset_password.html', form=form, title='Reset Password')


# ------------------ DASHBOARD ------------------ #
@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = SearchForm()
    ideas = Idea.query.filter_by(user_id=current_user.id)
    name_site = Setting.query.get(1)
    
    # recherche par tags
    if form.validate_on_submit() and form.tags.data:
        tags = [t.strip().lower() for t in form.tags.data.split(',') if t.strip()]
        for tag in tags:
            ideas = ideas.filter(Idea.tags.contains(tag))

    # pagination using settings
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    try:
        per_page = int(get_setting('items_per_page', '10'))
    except Exception:
        per_page = 10
    total = ideas.count()
    ideas = ideas.order_by(Idea.timestamp.desc()).offset(offset).limit(per_page).all()
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')

    return render_template('index.html', title='Dashboard', ideas=ideas, form=form, pagination=pagination, name_site=name_site)


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
        # Enforce max ideas per user
        try:
            max_ideas = int(get_setting('max_ideas_per_user', '100'))
        except Exception:
            max_ideas = 100
        user_ideas_count = Idea.query.filter_by(user_id=current_user.id).count()
        if user_ideas_count >= max_ideas:
            flash('⛔ You have reached the maximum number of ideas allowed.', 'danger')
            return redirect(url_for('main.index'))
        # Auto-approve
        status_value = form.status.data
        if get_setting('auto_approve_ideas', 'on') == 'on':
            status_value = 'Published'
        idea = Idea(
            title=form.title.data,
            description=form.description.data,
            tags=form.tags.data,
            status=status_value,
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
@limiter.limit("5 per minute")
@login_required
def import_ideas():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = getattr(file, 'filename', '') or ''
        if not filename.lower().endswith('.csv'):
            flash('❌ Invalid file type. Please upload a CSV.', 'danger')
            return render_template('import.html', form=form, title='Import Ideas')

        try:
            content = file.read()
            if len(content) > 2 * 1024 * 1024:
                flash('❌ File too large (max 2 MB).', 'danger')
                return render_template('import.html', form=form, title='Import Ideas')
            reader = csv.DictReader(StringIO(content.decode('utf-8')))
        except Exception:
            flash('❌ Could not read CSV. Check encoding (UTF-8) and columns.', 'danger')
            return render_template('import.html', form=form, title='Import Ideas')

        required_columns = {'Title'}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            flash('❌ Missing required column: Title', 'danger')
            return render_template('import.html', form=form, title='Import Ideas')
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
@limiter.limit("10 per minute")
@login_required
def suggest_idea():
    form = SearchForm()
    suggestions = []
    if form.validate_on_submit() and form.tags.data:
        tags = form.tags.data
        api_key = os.environ.get('GENAI_API_KEY')
        if not api_key:
            flash('⚠️ AI suggestions unavailable: missing GENAI_API_KEY.', 'warning')
            return render_template('suggest.html', form=form, title='Suggest Ideas')
        client = genai.Client(api_key=api_key)
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
@limiter.limit("30 per minute")
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