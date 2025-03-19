import os
from datetime import datetime, timedelta
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import random
import string
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
from models import User, TestType, TestAttempt, TestMaster # Added TestMaster import
from forms import LoginForm, RegistrationForm, TestTypeForm, TestMasterForm, AllocateTestForm, StartTestForm # Added TestMasterForm and AllocateTestForm import


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

@app.route('/users')
@login_required
def user_list():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    form = RegistrationForm()
    if form.validate_on_submit():
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
            flash('User added successfully!', 'success')
            return redirect(url_for('user_list'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to add user. Please try again.', 'error')
            app.logger.error(f"User creation error: {str(e)}")

    return render_template('add_user.html', form=form)


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete user. Please try again.', 'error')
        app.logger.error(f"User deletion error: {str(e)}")
    return redirect(url_for('user_list'))

#New routes for test type management
@app.route('/test-types')
@login_required
def test_types():
    test_types = TestType.query.all()
    return render_template('test_types.html', test_types=test_types)

@app.route('/test-types/add', methods=['GET', 'POST'])
@login_required
def add_test_type():
    form = TestTypeForm()
    if form.validate_on_submit():
        test_type = TestType(
            name=form.name.data, #Corrected field name here. Assuming 'name' is the correct field.
            language=form.language.data
        )
        try:
            db.session.add(test_type)
            db.session.commit()
            flash('Test type added successfully!', 'success')
            return redirect(url_for('test_types'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to add test type. Please try again.', 'error')
            app.logger.error(f"Test type creation error: {str(e)}")

    return render_template('add_test_type.html', form=form)

@app.route('/test-types/delete/<int:test_type_id>', methods=['POST'])
@login_required
def delete_test_type(test_type_id):
    test_type = TestType.query.get_or_404(test_type_id)
    try:
        db.session.delete(test_type)
        db.session.commit()
        flash('Test type deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete test type. Please try again.', 'error')
        app.logger.error(f"Test type deletion error: {str(e)}")
    return redirect(url_for('test_types'))

# Add these routes after the existing routes in app.py
@app.route('/test-master')
@login_required
def test_master_list():
    test_masters = TestMaster.query.all()
    return render_template('test_master.html', test_masters=test_masters)

@app.route('/test-master/add', methods=['GET', 'POST'])
@login_required
def add_test_master():
    form = TestMasterForm()
    form.test_type.choices = [(t.id, t.name) for t in TestType.query.all()]

    if form.validate_on_submit():
        test_master = TestMaster(
            test_type_id=form.test_type.data,
            question=form.question.data,
            answer_a=form.answer_a.data,
            answer_b=form.answer_b.data,
            answer_c=form.answer_c.data,
            answer_d=form.answer_d.data,
            correct_answer=form.correct_answer.data,
            created_by=current_user.id
        )

        if form.question_image.data:
            filename = secure_filename(form.question_image.data.filename)
            form.question_image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            test_master.question_image = filename

        try:
            db.session.add(test_master)
            db.session.commit()
            flash('Test question added successfully!', 'success')
            return redirect(url_for('test_master_list'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to add test question. Please try again.', 'error')
            app.logger.error(f"Test master creation error: {str(e)}")

    return render_template('add_test_master.html', form=form)

@app.route('/test-master/delete/<int:test_master_id>', methods=['POST'])
@login_required
def delete_test_master(test_master_id):
    test_master = TestMaster.query.get_or_404(test_master_id)
    try:
        db.session.delete(test_master)
        db.session.commit()
        flash('Test question deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete test question. Please try again.', 'error')
        app.logger.error(f"Test master deletion error: {str(e)}")
    return redirect(url_for('test_master_list'))

@app.route('/allocate-test', methods=['GET', 'POST'])
@login_required
def allocate_test():
    form = AllocateTestForm()
    form.user.choices = [(u.id, f"{u.first_name} {u.last_name}") for u in User.query.all()]
    form.test_type.choices = [(t.id, t.name) for t in TestType.query.all()]

    if form.validate_on_submit():
        # Handle form submission here
        flash('Test allocated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('allocate_test.html', form=form)

# Create tables
with app.app_context():
    db.create_all()


@app.route('/start-test', methods=['GET', 'POST'])
@login_required
def start_test():
    form = StartTestForm()
    form.test_type.choices = [(t.id, t.name) for t in TestType.query.all()]

    if form.validate_on_submit():
        return redirect(url_for('take_test', test_type_id=form.test_type.data))

    return render_template('start_test.html', form=form)

@app.route('/take-test/<int:test_type_id>', methods=['GET', 'POST'])
@login_required
def take_test(test_type_id):
    test_type = TestType.query.get_or_404(test_type_id)
    questions = TestMaster.query.filter_by(test_type_id=test_type_id).all()
    
    if request.method == 'POST':
        score = 0
        total_questions = len(questions)
        
        for question in questions:
            answer_key = f'answer_{question.id}'
            if answer_key in request.form:
                if request.form[answer_key] == question.correct_answer:
                    score += 1
        
        percentage = (score / total_questions) * 100
        passed = percentage >= 60  # Pass mark is 60%
        
        test_attempt = TestAttempt(
            user_id=current_user.id,
            test_type_id=test_type_id,
            score=percentage,
            passed=passed
        )
        
        try:
            db.session.add(test_attempt)
            db.session.commit()
            flash(f'Test completed! Your score: {percentage:.2f}%', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error saving test results. Please try again.', 'error')
            app.logger.error(f"Test attempt save error: {str(e)}")
    
    return render_template('take_test.html', test_type=test_type, questions=questions, form=StartTestForm())
