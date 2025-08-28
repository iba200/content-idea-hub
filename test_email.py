#!/usr/bin/env python3
"""Script de test pour vérifier la configuration email."""

import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import User
from app.utils.email_manager import EmailManager

# Charger les variables d'environnement
load_dotenv()

def test_email_config():
    """Test de la configuration email."""
    app = create_app()
    
    with app.app_context():
        # Vérifier la configuration
        print("Configuration email:")
        print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        
        # Créer un utilisateur de test
        test_user = User(
            username="test_user",
            email="test@example.com"
        )
        test_user.set_password("test123")
        test_user.email_verified = True
        
        # Tester l'EmailManager
        email_manager = EmailManager()
        
        print("\nTest de génération de token:")
        token = email_manager.generate_verification_token("test@example.com")
        print(f"Token généré: {token[:20]}...")
        
        # Vérifier le token
        email = email_manager.verify_token(token, 'email-verification')
        print(f"Email vérifié: {email}")
        
        print("\nTest terminé avec succès!")

if __name__ == "__main__":
    test_email_config()
