from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_paginate import Pagination, get_page_args
from app import db
from app.models import User, Idea
from app.forms import IdeaForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")

def check_admin():
    """Vérifie si l'utilisateur est un administrateur."""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash("⛔ Accès non autorisé. Vous devez être administrateur.", "danger")
        return redirect(url_for("main.login"))
    return None

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    # Vérifier si l'utilisateur est admin
    admin_check = check_admin()
    if admin_check:
        return admin_check

    # Statistiques
    user_count = User.query.count()
    idea_count = Idea.query.count()
    last_idea = Idea.query.order_by(Idea.timestamp.desc()).first()
    last_idea_date = last_idea.timestamp.strftime('%Y-%m-%d') if last_idea else None

    # Pagination pour les idées
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 10
    ideas_query = Idea.query.order_by(Idea.timestamp.desc())
    total = ideas_query.count()
    ideas = ideas_query.offset(offset).limit(per_page).all()
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')

    return render_template("admin/dashboard.html", 
                         user_count=user_count, 
                         idea_count=idea_count, 
                         last_idea_date=last_idea_date, 
                         ideas=ideas, 
                         pagination=pagination)

@admin_bp.route("/new_idea", methods=["GET", "POST"])
@login_required
def new_idea():
    # Vérifier si l'utilisateur est admin
    admin_check = check_admin()
    if admin_check:
        return admin_check

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
        flash("✅ Idée ajoutée avec succès !", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/idea_form.html", form=form, title="Nouvelle idée")

@admin_bp.route("/edit_idea/<int:id>", methods=["GET", "POST"])
@login_required
def edit_idea(id):
    # Vérifier si l'utilisateur est admin
    admin_check = check_admin()
    if admin_check:
        return admin_check

    idea = Idea.query.get_or_404(id)
    form = IdeaForm(obj=idea)
    if form.validate_on_submit():
        idea.title = form.title.data
        idea.description = form.description.data
        idea.tags = form.tags.data
        idea.status = form.status.data
        db.session.commit()
        flash("✅ Idée mise à jour avec succès !", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/idea_form.html", form=form, idea=idea, title="Modifier l'idée")

@admin_bp.route("/delete_idea/<int:id>", methods=["GET", "POST"])
@login_required
def delete_idea(id):
    # Vérifier si l'utilisateur est admin
    admin_check = check_admin()
    if admin_check:
        return admin_check

    idea = Idea.query.get_or_404(id)
    db.session.delete(idea)
    db.session.commit()
    flash("🗑️ Idée supprimée avec succès !", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/users")
@login_required
def users():
    # Vérifier si l'utilisateur est admin
    admin_check = check_admin()
    if admin_check:
        return admin_check

    # Pagination pour les utilisateurs
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 10
    users_query = User.query.order_by(User.created_at.desc())
    total = users_query.count()
    users = users_query.offset(offset).limit(per_page).all()
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')

    return render_template("admin/users.html", users=users, pagination=pagination)