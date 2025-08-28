# admin_routes.py - À ajouter dans votre dossier app/
from sqlalchemy import func
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import timedelta
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import User, Idea
from flask_paginate import Pagination
from app.utils.settings_manager import set_setting, get_setting, reset_settings

import io
import csv

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Décorateur pour s'assurer que seuls les admins peuvent accéder aux routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('❌ Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Page principale du tableau de bord admin"""
    # Statistiques générales
    total_users = User.query.count()
    total_ideas = Idea.query.count()
    active_users = User.query.filter(
        User.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Calcul du taux d'engagement (exemple basique)
    published_ideas = Idea.query.filter_by(status='Published').count()
    draft_ideas = Idea.query.filter_by(status='Draft').count()
    engagement_rate = (published_ideas / total_ideas * 100) if total_ideas > 0 else 0
    
    # Croissance mensuelle des utilisateurs
    last_month = datetime.utcnow() - timedelta(days=30)
    users_last_month = User.query.filter(User.created_at >= last_month).count()
    previous_month = User.query.filter(
        User.created_at < last_month,
        User.created_at >= datetime.utcnow() - timedelta(days=60)
    ).count()
    user_growth = ((users_last_month - previous_month) / previous_month * 100) if previous_month > 0 else 0
    
    # Statistiques des idées par statut
    ideas_by_status = db.session.query(
        Idea.status, func.count(Idea.id)
    ).group_by(Idea.status).all()
    
    # Activité récente
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_ideas = Idea.query.order_by(Idea.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_ideas=total_ideas,
                         active_users=active_users,
                         engagement_rate=round(engagement_rate, 1),
                         user_growth=round(user_growth, 1),
                         ideas_by_status=dict(ideas_by_status),
                         recent_users=recent_users,
                         recent_ideas=recent_ideas)

@admin_bp.route('/users')
@login_required
@admin_required
def users_management():
    """Gestion des utilisateurs"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    sort = request.args.get('sort', 'created_desc')
    
    users_query = User.query
    if search:
        users_query = users_query.filter(User.username.contains(search))
    if role == 'admin':
        users_query = users_query.filter_by(is_admin=True)
    elif role == 'user':
        users_query = users_query.filter_by(is_admin=False)

    if sort == 'created_asc':
        users_query = users_query.order_by(User.created_at.asc())
    elif sort == 'name_asc':
        users_query = users_query.order_by(User.username.asc())
    elif sort == 'name_desc':
        users_query = users_query.order_by(User.username.desc())
    else:
        users_query = users_query.order_by(User.created_at.desc())
    
    users = users_query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques des utilisateurs
    user_stats = {
        'total': User.query.count(),
        'active': User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count(),
        'admin': User.query.filter_by(is_admin=True).count()
    }
    
    return render_template('admin/users.html', 
                         users=users, 
                         search=search,
                         user_stats=user_stats,
                         role=role,
                         sort=sort)

@admin_bp.route('/users/export')
@login_required
@admin_required
def export_users():
    """Export all users (optionally filtered by search) as CSV"""
    search = request.args.get('search', '')
    users_query = User.query
    if search:
        users_query = users_query.filter(User.username.contains(search))
    users = users_query.order_by(User.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Username', 'Is Admin', 'Ideas Count', 'Created At', 'Last Seen'])
    for u in users:
        writer.writerow([
            u.username,
            'yes' if u.is_admin else 'no',
            len(u.ideas) if hasattr(u, 'ideas') else 0,
            u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else '',
            u.last_seen.strftime('%Y-%m-%d %H:%M') if u.last_seen else ''
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='users.csv'
    )

@admin_bp.route('/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Activer/désactiver les privilèges admin d'un utilisateur"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot modify your own admin status'}), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted' if user.is_admin else 'revoked'
    current_app.logger.info('admin_toggle', extra={'actor': current_user.username, 'target': user.username, 'new_is_admin': user.is_admin})
    flash(f'✅ Admin privileges {status} for {user.username}', 'success')
    
    return jsonify({'success': True, 'is_admin': user.is_admin})

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    # Supprimer aussi toutes les idées de l'utilisateur
    Idea.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    current_app.logger.warning('admin_delete_user', extra={'actor': current_user.username, 'target': user.username})
    
    flash(f'🗑️ User {user.username} deleted successfully', 'success')
    return jsonify({'success': True})

@admin_bp.route('/ideas')
@login_required
@admin_required
def ideas_management():
    """Gestion des idées"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    ideas_query = Idea.query
    if status_filter:
        ideas_query = ideas_query.filter_by(status=status_filter)
    if search:
        ideas_query = ideas_query.filter(Idea.title.contains(search))
    sort = request.args.get('sort', 'created_desc')
    if sort == 'created_asc':
        ideas_query = ideas_query.order_by(Idea.timestamp.asc())
    elif sort == 'title_asc':
        ideas_query = ideas_query.order_by(Idea.title.asc())
    elif sort == 'title_desc':
        ideas_query = ideas_query.order_by(Idea.title.desc())
    else:
        ideas_query = ideas_query.order_by(Idea.timestamp.desc())

    ideas = ideas_query.order_by(Idea.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques des idées
    idea_stats = {
        'total': Idea.query.count(),
        'draft': Idea.query.filter_by(status='Draft').count(),
        'published': Idea.query.filter_by(status='Published').count(),
        'to_film': Idea.query.filter_by(status='To Film').count()
    }
    
    return render_template('admin/ideas.html', 
                         ideas=ideas, 
                         search=search,
                         status_filter=status_filter,
                         sort=sort,
                         idea_stats=idea_stats)

@admin_bp.route('/ideas/export')
@login_required
@admin_required
def export_ideas_admin():
    """Export ideas (respecting current filters) as CSV"""
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    ideas_query = Idea.query
    if status_filter:
        ideas_query = ideas_query.filter_by(status=status_filter)
    if search:
        ideas_query = ideas_query.filter(Idea.title.contains(search))
    ideas = ideas_query.order_by(Idea.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Author', 'Status', 'Tags', 'Created At'])
    for idea in ideas:
        writer.writerow([
            idea.title,
            idea.author.username if idea.author else '',
            idea.status,
            idea.tags or '',
            idea.timestamp.strftime('%Y-%m-%d %H:%M') if idea.timestamp else ''
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='ideas.csv'
    )

@admin_bp.route('/ideas/<int:idea_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_idea(idea_id):
    """Supprimer une idée"""
    idea = Idea.query.get_or_404(idea_id)
    db.session.delete(idea)
    db.session.commit()
    current_app.logger.info('admin_delete_idea', extra={'actor': current_user.username, 'idea_id': idea_id, 'title': idea.title})
    
    flash(f'🗑️ Idea "{idea.title}" deleted successfully', 'success')
    return jsonify({'success': True})

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Analytics dashboard"""

    # --- Statistiques de base ---
    total_users = User.query.count()
    total_ideas = Idea.query.count()
    published_ideas = Idea.query.filter(Idea.status.ilike("published")).count()
    active_users = User.query.filter(User.last_seen >= datetime.utcnow() - timedelta(days=7)).count()

    # --- Croissance des utilisateurs par mois ---
    user_growth = (
        User.query.with_entities(
            func.strftime("%Y-%m", User.created_at).label("month"),
            func.count(User.id)
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    months = [m for m, _ in user_growth]
    user_counts = [c for _, c in user_growth]

    # --- Top tags (comme tu stockes dans une string séparée par virgules) ---
    tags_counter = {}
    ideas = Idea.query.all()
    for idea in ideas:
        if idea.tags:
            for tag in idea.tags.split(","):
                tag = tag.strip().lower()
                if tag:
                    tags_counter[tag] = tags_counter.get(tag, 0) + 1

    # On trie par nombre décroissant
    top_tags = sorted(tags_counter.items(), key=lambda x: x[1], reverse=True)[:5]

    # --- Activité par jour de la semaine ---
    weekday_activity = {i: 0 for i in range(7)}  # 0=Monday ... 6=Sunday
    for idea in ideas:
        if idea.timestamp:
            weekday_activity[idea.timestamp.weekday()] += 1

    return render_template(
        "admin/analytics.html",
        total_users=total_users,
        total_ideas=total_ideas,
        published_ideas=published_ideas,
        active_users=active_users,
        months=months,
        user_counts=user_counts,
        top_tags=top_tags,
        weekday_activity=weekday_activity,
    )

DEFAULT_SETTINGS = {
    "site_name": "Content Idea Hub",
    "site_description": "Manage your content ideas efficiently",
    "items_per_page": "20",
    "timezone": "UTC",
    "allow_registration": "on",
    "require_email_verification": "",
    "auto_approve_ideas": "on",
    "max_ideas_per_user": "100",
    "enable_2fa": "",
    "log_user_activity": "on",
    "session_timeout": "30",
    "password_min_length": "8",
    "email_notifications": "on",
    "admin_alerts": "on",
    "admin_email": "admin@contentideahub.com",
    "auto_backup": "on",
    "backup_frequency": "daily",
}

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Paramètres du système"""
    if request.method == 'POST':
        if "reset" in request.form:
            reset_settings(DEFAULT_SETTINGS)
            flash("🔄 Settings reset to default", "info")
        else:
            for key in DEFAULT_SETTINGS.keys():
                value = request.form.get(key, "")
                set_setting(key, value)
            flash('⚙️ Settings saved successfully', 'success')
        return redirect(url_for('admin.settings'))
    
    # Charger les paramètres depuis la base
    settings_data = {key: get_setting(key, default) for key, default in DEFAULT_SETTINGS.items()}
    return render_template('admin/settings.html', settings=settings_data)

@admin_bp.route('/logs')
@login_required
@admin_required
def system_logs():
    """Logs du système"""
    page = request.args.get('page', 1, type=int)
    level_filter = request.args.get('level', '')
    search = request.args.get('search', '')
    
    # Mock log data (replace with actual log storage in production)
    logs_data = [
        {'timestamp': datetime.utcnow() - timedelta(minutes=2), 'level': 'INFO', 'message': f'User login: {current_user.username}'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=5), 'level': 'DEBUG', 'message': 'Database connection established'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=8), 'level': 'WARN', 'message': 'High memory usage detected: 85%'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=10), 'level': 'ERROR', 'message': 'Failed to process request'},
    ]
    
    # Filtering logs
    filtered_logs = logs_data
    if level_filter:
        filtered_logs = [log for log in filtered_logs if log['level'] == level_filter]
    if search:
        filtered_logs = [log for log in filtered_logs if search.lower() in log['message'].lower()]
    
    # Pagination
    per_page = 20
    total = len(filtered_logs)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_logs = filtered_logs[start:end]
    
    # logs = Pagination(None, page, per_page, total, paginated_logs)
    logs = Pagination(page=page, total=total, per_page=per_page, record_name='logs', css_framework='bootstrap4')
    
    return render_template('admin/logs.html', 
                         logs=logs, 
                         level_filter=level_filter, 
                         search=search)

@admin_bp.route('/export_logs')
@login_required
@admin_required
def export_logs():
    """Export logs as CSV"""
    level_filter = request.args.get('level', '')
    search = request.args.get('search', '')
    
    # Mock log data (replace with actual log storage in production)
    logs_data = [
        {'timestamp': datetime.utcnow() - timedelta(minutes=2), 'level': 'INFO', 'message': f'User login: {current_user.username}'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=5), 'level': 'DEBUG', 'message': 'Database connection established'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=8), 'level': 'WARN', 'message': 'High memory usage detected: 85%'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=10), 'level': 'ERROR', 'message': 'Failed to process request'},
    ]
    
    # Filtering logs
    filtered_logs = logs_data
    if level_filter:
        filtered_logs = [log for log in filtered_logs if log['level'] == level_filter]
    if search:
        filtered_logs = [log for log in filtered_logs if search.lower() in log['message'].lower()]
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Level', 'Message'])
    for log in filtered_logs:
        writer.writerow([log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), log['level'], log['message']])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='system_logs.csv'
    )

@admin_bp.route('/api/logs')
@login_required
@admin_required
def api_logs():
    """API pour les logs en temps réel"""
    # Mock log data (replace with actual log storage in production)
    logs = [
        {
            'timestamp': (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
            'level': 'INFO',
            'message': f'User login: {current_user.username}'
        },
        {
            'timestamp': (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            'level': 'DEBUG',
            'message': 'Database connection established'
        },
        {
            'timestamp': (datetime.utcnow() - timedelta(minutes=8)).isoformat(),
            'level': 'WARN',
            'message': 'High memory usage detected: 85%'
        },
        {
            'timestamp': (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
            'level': 'ERROR',
            'message': 'Failed to process request'
        }
    ]
    
    return jsonify({'logs': logs})

# API endpoints pour les données en temps réel
@admin_bp.route('/api/dashboard/stats')
@login_required
@admin_required
def dashboard_stats():
    """API pour les statistiques du dashboard"""
    return jsonify({
        'total_users': User.query.count(),
        'total_ideas': Idea.query.count(),
        'active_users': User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count(),
        'recent_activity': [
            {
                'type': 'user_registered',
                'user': user.username,
                'timestamp': user.created_at.isoformat()
            }
            for user in User.query.order_by(User.created_at.desc()).limit(5)
        ]
    })

@admin_bp.route('/api/charts/user-growth')
@login_required
@admin_required
def chart_user_growth():
    """Données pour le graphique de croissance des utilisateurs"""
    data = []
    for i in range(30, 0, -1):
        date = datetime.utcnow() - timedelta(days=i)
        count = User.query.filter(
            func.date(User.created_at) == date.date()
        ).count()
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    return jsonify(data)