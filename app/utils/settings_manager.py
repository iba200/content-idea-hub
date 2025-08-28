# app/utils/settings_manager.py
from app.models import Setting, db

# Valeurs par défaut globales
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

def get_setting(key, default=None):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default

def set_setting(key, value):
    setting = Setting.query.filter_by(key=key).first()
    if not setting:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    else:
        setting.value = value
    db.session.commit()

def reset_settings(defaults=DEFAULT_SETTINGS):
    for key, value in defaults.items():
        set_setting(key, value)
