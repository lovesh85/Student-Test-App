from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_photo = db.Column(db.String(255))
    is_new = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    test_attempts = db.relationship('TestAttempt', backref='user', lazy=True)

class TestType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    test_attempts = db.relationship('TestAttempt', backref='test_type', lazy=True)

class TestAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_type_id = db.Column(db.Integer, db.ForeignKey('test_type.id'), nullable=False)
    passed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)