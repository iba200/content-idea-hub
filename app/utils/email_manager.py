"""Email manager for sending verification and password reset emails."""
import os
from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_mail import Message
from app import mail
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature


class EmailManager:
    """Manages email sending for the application."""
    
    def __init__(self):
        self.serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    def send_verification_email(self, user):
        """Send email verification email to user."""
        token = self.serializer.dumps(user.email, salt='email-verification')
        
        msg = Message(
            'Verify Your Email - Content Idea Hub',
            recipients=[user.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        verification_url = url_for('main.verify_email', token=token, _external=True)
        
        msg.html = f"""
        <html>
        <body>
            <h2>Welcome to Content Idea Hub!</h2>
            <p>Hi {user.username},</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>If you didn't create an account, you can safely ignore this email.</p>
            <p>Best regards,<br>Content Idea Hub Team</p>
        </body>
        </html>
        """
        
        msg.body = f"""
        Welcome to Content Idea Hub!
        
        Hi {user.username},
        
        Please verify your email address by visiting this link:
        {verification_url}
        
        If you didn't create an account, you can safely ignore this email.
        
        Best regards,
        Content Idea Hub Team
        """
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {e}")
            return False
    
    def send_password_reset_email(self, user):
        """Send password reset email to user."""
        token = self.serializer.dumps(user.email, salt='password-reset')
        
        msg = Message(
            'Reset Your Password - Content Idea Hub',
            recipients=[user.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        reset_url = url_for('main.reset_password', token=token, _external=True)
        
        msg.html = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi {user.username},</p>
            <p>You requested a password reset. Click the link below to reset your password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, you can safely ignore this email.</p>
            <p>Best regards,<br>Content Idea Hub Team</p>
        </body>
        </html>
        """
        
        msg.body = f"""
        Password Reset Request
        
        Hi {user.username},
        
        You requested a password reset. Visit this link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        Best regards,
        Content Idea Hub Team
        """
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email: {e}")
            return False
    
    def verify_token(self, token, salt, expiration=3600):
        """Verify a token with the given salt."""
        try:
            email = self.serializer.loads(token, salt=salt, max_age=expiration)
            return email
        except SignatureExpired:
            return None
        except BadTimeSignature:
            return None
    
    def generate_verification_token(self, email):
        """Generate a verification token for email verification."""
        return self.serializer.dumps(email, salt='email-verification')
    
    def generate_password_reset_token(self, email):
        """Generate a password reset token."""
        return self.serializer.dumps(email, salt='password-reset')
