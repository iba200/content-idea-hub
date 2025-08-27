# admin_routes.py - À ajouter dans votre dossier app/

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import User, Idea

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
    
    users_query = User.query
    if search:
        users_query = users_query.filter(User.username.contains(search))
    
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
                         user_stats=user_stats)

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
                         idea_stats=idea_stats)

@admin_bp.route('/ideas/<int:idea_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_idea(idea_id):
    """Supprimer une idée"""
    idea = Idea.query.get_or_404(idea_id)
    db.session.delete(idea)
    db.session.commit()
    
    flash(f'🗑️ Idea "{idea.title}" deleted successfully', 'success')
    return jsonify({'success': True})

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Page d'analytics détaillées"""
    # Données pour les graphiques
    
    # Évolution des utilisateurs sur 12 mois
    months = []
    user_counts = []
    for i in range(12, 0, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        count = User.query.filter(
            User.created_at >= month_start,
            User.created_at < month_end
        ).count()
        months.append(month_start.strftime('%b %Y'))
        user_counts.append(count)
    
    # Répartition des idées par catégorie (basé sur les tags)
    tag_counts = {}
    ideas_with_tags = Idea.query.filter(Idea.tags.isnot(None)).all()
    for idea in ideas_with_tags:
        if idea.tags:
            tags = [tag.strip().lower() for tag in idea.tags.split(',')]
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Top 5 des tags
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    published_ideas = Idea.query.filter_by(status='Published').count()
    # Activité par jour de la semaine
    weekday_activity = {}
    for i in range(7):  # 0 = lundi, 6 = dimanche
        count = Idea.query.filter(
            func.extract('dow', Idea.timestamp) == i
        ).count()
        weekday_activity[i] = count
    
    return render_template('admin/analytics.html',
                         total_users=User.query.count(),
                         total_ideas=Idea.query.count(),
                         published_ideas=published_ideas,
                         active_users=User.query.filter(User.created_at >= datetime.utcnow() - timedelta(days=30)).count(),
                         months=months,
                         user_counts=user_counts,
                         top_tags=top_tags,
                         weekday_activity=weekday_activity)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Paramètres du système"""
    if request.method == 'POST':
        # Ici vous pouvez implémenter la sauvegarde des paramètres
        # dans une table de configuration ou un fichier
        flash('⚙️ Settings saved successfully', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html')

@admin_bp.route('/logs')
@login_required
@admin_required
def system_logs():
    """Logs du système"""
    # Ici vous pourriez implémenter la lecture des logs
    # depuis un fichier ou une base de données
    logs = [
        {
            'timestamp': datetime.utcnow() - timedelta(minutes=2),
            'level': 'INFO',
            'message': f'User login: {current_user.username}'
        },
        {
            'timestamp': datetime.utcnow() - timedelta(minutes=5),
            'level': 'DEBUG',
            'message': 'Database connection established'
        },
        {
            'timestamp': datetime.utcnow() - timedelta(minutes=8),
            'level': 'WARN',
            'message': 'High memory usage detected: 85%'
        }
    ]
    
    return render_template('admin/logs.html', logs=logs)

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