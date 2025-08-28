#!/usr/bin/env python3
"""Script pour créer un compte admin."""

from app import create_app, db
from app.models import User

def create_admin_user():
    """Créer un utilisateur admin."""
    app = create_app()
    
    with app.app_context():
        # Vérifier si l'admin existe déjà
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("❌ L'utilisateur 'admin' existe déjà!")
            return
        
        # Créer l'utilisateur admin
        admin = User(
            username='Admin',
            email='admin@contentideahub.com',
            email_verified=True  # Admin n'a pas besoin de vérification
        )
        admin.set_password('password123')
        admin.is_admin = True
        
        # Ajouter à la base de données
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Compte admin créé avec succès!")
        print("   Username: admin")
        print("   Password: password123")
        print("   Email: admin@contentideahub.com")
        print("   Admin: Oui")

if __name__ == "__main__":
    create_admin_user()
