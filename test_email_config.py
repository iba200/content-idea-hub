#!/usr/bin/env python3
"""Script de test pour vérifier la configuration email."""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_env_config():
    """Test de la configuration des variables d'environnement."""
    print("🔍 Vérification de la configuration email:")
    print("=" * 50)
    
    # Vérifier chaque variable
    mail_vars = [
        'MAIL_SERVER',
        'MAIL_PORT', 
        'MAIL_USE_TLS',
        'MAIL_USE_SSL',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER'
    ]
    
    for var in mail_vars:
        value = os.environ.get(var)
        if value:
            # Masquer le mot de passe
            if 'PASSWORD' in var:
                display_value = '*' * len(value)
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NON DÉFINI")
    
    print("\n" + "=" * 50)
    
    # Test de connexion SMTP basique
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        print("\n🧪 Test de connexion SMTP...")
        
        # Récupérer les valeurs
        server = 'smtp.gmail.com'
        port = int(os.environ.get('MAIL_PORT', 587))
        username = 'ibrahimathiongane2006@gmail.com'
        password = 'oqmumyhkauphemuc'
        
        if not all([server, username, password]):
            print("❌ Configuration incomplète pour le test SMTP")
            return
        
        # Test de connexion
        print(f"Connexion à {server}:{port}...")
        smtp = smtplib.SMTP(server, port)
        smtp.starttls()
        
        print("Authentification...")
        smtp.login(username, password)
        
        print("✅ Connexion SMTP réussie!")
        smtp.quit()
        
    except Exception as e:
        print(f"❌ Erreur de connexion SMTP: {e}")
        print("\n💡 Solutions possibles:")
        print("1. Vérifier que l'authentification à 2 facteurs est activée sur Gmail")
        print("2. Générer un mot de passe d'application spécifique")
        print("3. Vérifier que le compte n'est pas bloqué par Google")

if __name__ == "__main__":
    test_env_config()
