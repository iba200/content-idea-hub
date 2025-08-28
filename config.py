"""Configuration pour l'application Flask, y compris la configuration de la base de données."""
from datetime import timedelta
import os
import secrets


class Config:
    """
    Configuration pour l'application Flask.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///site.db')  # DB locale SQLite par défaut
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.environ.get('SESSION_HOURS', '2')))

    # Cookies sécurisés (à activer pleinement en prod derrière HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'

    # Taille max upload (ex: 2 Mo)
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 2 * 1024 * 1024))

    # Rate limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per hour')
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # Talisman / Security headers
    CONTENT_SECURITY_POLICY = {
        'default-src': ["'self'"],
        'img-src': ["'self'", 'data:'],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            'https://cdn.tailwindcss.com',
            'https://cdnjs.cloudflare.com',
            'https://fonts.googleapis.com',
            'https://ka-f.fontawesome.com'
        ],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            'https://cdn.tailwindcss.com',
            'https://cdnjs.cloudflare.com',
            'https://kit.fontawesome.com'
        ],
        'connect-src': [
            "'self'",
            'https://kit.fontawesome.com',
            'https://ka-f.fontawesome.com'
        ],
        'font-src': [
            "'self'",
            'data:',
            'https://cdnjs.cloudflare.com',
            'https://kit.fontawesome.com',
            'https://ka-f.fontawesome.com',
            'https://fonts.gstatic.com'
        ]
    }
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'False').lower() == 'true'
    
    # Configuration email
    MAIL_SERVER="smtp.gmail.com"
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USE_SSL=False
    MAIL_USERNAME="ibrahimathiongane2006@gmail.com"
    MAIL_PASSWORD="oqmumyhkauphemuc" 
    MAIL_DEFAULT_SENDER = "fausse.address@gmail.com"