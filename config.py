"""Configuration pour l'application Flask, y compris la configuration de la base de données."""
import os
import secrets


class Config:
    """
    Configuration pour l'application Flask.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # DB locale SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False
