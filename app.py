import os
from datetime import datetime, timedelta
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.DEBUG)

# Initialize Flask-Login
login_manager = LoginManager()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("SESSION_SECRET")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import routes after app initialization to avoid circular imports
from models import User, TestType, TestAttempt
from forms import LoginForm, RegistrationForm

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/api/chart-data')
@login_required
def get_chart_data():
    # Get the last 6 months of test attempts
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    attempts = db.session.query(
        func.date_trunc('month', TestAttempt.attempt_date).label('month'),
        func.avg(TestAttempt.score).label('avg_score')
    ).filter(
        TestAttempt.attempt_date >= six_months_ago
    ).group_by(
        'month'
    ).order_by(
        'month'
    ).all()

    # Format data for Chart.js
    months = []
    scores = []
    for attempt in attempts:
        months.append(attempt.month.strftime('%b'))
        scores.append(float(attempt.avg_score) if attempt.avg_score else 0)

    return jsonify({
        'labels': months,
        'data': scores
    })

@app.route('/')
@login_required
def dashboard():
    # Get real-time statistics
    total_students = User.query.count()
    new_students = User.query.filter_by(is_new=True).count()
    test_types = TestType.query.count()
    total_attempts = TestAttempt.query.count()
    passed_attempts = TestAttempt.query.filter_by(passed=True).count()
    failed_attempts = TestAttempt.query.filter_by(passed=False).count()

    return render_template('dashboard.html',
                         total_students=total_students,
                         new_students=new_students,
                         test_types=test_types,
                         total_attempts=total_attempts,
                         passed_attempts=passed_attempts,
                         failed_attempts=failed_attempts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash('Passwords do not match', 'error')
            return render_template('register.html', form=form)

        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            password_hash=generate_password_hash(form.password.data),
            is_new=True
        )

        if form.profile_photo.data:
            filename = secure_filename(form.profile_photo.data.filename)
            form.profile_photo.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.profile_photo = filename

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            app.logger.error(f"Registration error: {str(e)}")

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Create tables
with app.app_context():
    db.create_all()