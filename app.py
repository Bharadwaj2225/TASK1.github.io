from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db, login_manager
from models import User, Task, TimeLog

# App setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('User already exists.')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None

        new_task = Task(
            title=title,
            description=description,
            due_date=due_date,
            user_id=current_user.id
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_task.html')

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        task.completed = 'completed' in request.form
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_task.html', task=task)

@app.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/start_timer/<int:task_id>')
@login_required
def start_timer(task_id):
    new_log = TimeLog(task_id=task_id, user_id=current_user.id, start_time=datetime.utcnow())
    db.session.add(new_log)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/stop_timer/<int:log_id>')
@login_required
def stop_timer(log_id):
    log = TimeLog.query.get_or_404(log_id)
    if log.user_id != current_user.id:
        return "Unauthorized", 403
    log.end_time = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logs/<int:task_id>')
@login_required
def view_logs(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return "Unauthorized", 403
    logs = TimeLog.query.filter_by(task_id=task_id).all()
    return render_template('view_logs.html', task=task, logs=logs)
@app.route('/insights')
@login_required
def insights():
    # Query time logs and tasks
    logs = TimeLog.query.filter_by(user_id=current_user.id).all()
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    # Process data (e.g., total time per task)
    insights_data = {}  # you’ll fill this in
    return render_template('insights.html', logs=logs, tasks=tasks, insights=insights_data)


# Run server
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
