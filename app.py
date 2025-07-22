import os
import datetime
# ✅ NEW: Import jsonify
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler

# --- App Initialization & Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_change_this' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Database Model Definitions ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    events = db.relationship('Event', backref='author', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False, default='Personal') 
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Routes ---
@app.route("/")
@login_required
def index():
    query = Event.query.filter_by(user_id=current_user.id)
    search_term = request.args.get('search')
    if search_term:
        query = query.filter(Event.title.ilike(f'%{search_term}%'))
    category_filter = request.args.get('category')
    if category_filter:
        query = query.filter_by(category=category_filter)
    event_list = query.order_by(Event.event_date, Event.event_time).all()
    return render_template("index.html", events=event_list, search_term=search_term, category_filter=category_filter)

# ✅ NEW: Route to render the calendar page
@app.route("/calendar")
@login_required
def calendar():
    return render_template("calendar.html")

# ✅ NEW: API endpoint to provide event data as JSON
@app.route("/api/events")
@login_required
def api_events():
    event_list = Event.query.filter_by(user_id=current_user.id).all()
    events_json = []
    for event in event_list:
        # FullCalendar needs 'start' and 'title' keys
        events_json.append({
            'title': event.title,
            'start': datetime.datetime.combine(event.event_date, event.event_time).isoformat(),
            'description': event.description,
            # You can add more data here, like colors based on category
            'color': {
                'Personal': '#3498db',
                'Work': '#9b59b6',
                'Urgent': '#e74c3c',
                'Shopping': '#2ecc71'
            }.get(event.category, '#808080')
        })
    return jsonify(events_json)


# --- Other routes remain the same ---
@app.route("/add", methods=["POST"])
@login_required
def add():
    # ... existing add code ...
    title = request.form.get("title")
    description = request.form.get("description")
    category = request.form.get("category")
    date_str = request.form.get("date")
    time_str = request.form.get("time")
    
    event_date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    event_time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()

    new_event = Event(author=current_user, title=title, description=description, category=category, event_date=event_date_obj, event_time=event_time_obj)
    db.session.add(new_event)
    db.session.commit()
    
    flash(f"Event '{title}' added!", "success")
    return redirect(url_for("index"))

@app.route("/delete/<int:event_id>", methods=["POST"])
@login_required
def delete(event_id):
    # ... existing delete code ...
    event_to_delete = db.session.get(Event, event_id)
    if event_to_delete and event_to_delete.author == current_user:
        db.session.delete(event_to_delete)
        db.session.commit()
        flash("Event deleted.", "success")
    else:
        flash("Event not found or you don't have permission to delete it.", "danger")
    return redirect(url_for("index"))

@app.route("/edit/<int:event_id>", methods=["POST"])
@login_required
def edit(event_id):
    # ... existing edit code ...
    event_to_edit = db.session.get(Event, event_id)
    if not event_to_edit or event_to_edit.author != current_user:
        flash("Event not found or you don't have permission.", "danger")
        return redirect(url_for("index"))

    event_to_edit.title = request.form.get("title")
    event_to_edit.description = request.form.get("description")
    event_to_edit.category = request.form.get("category")
    event_to_edit.event_date = datetime.datetime.strptime(request.form.get("date"), '%Y-%m-%d').date()
    event_to_edit.event_time = datetime.datetime.strptime(request.form.get("time"), '%H:%M').time()
    db.session.commit()
    flash(f"Event '{event_to_edit.title}' updated!", "success")
    return redirect(url_for("index"))

# --- Authentication Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    # ... existing login code ...
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()
        if user and bcrypt.check_password_hash(user.password_hash, request.form.get("password")):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Login Unsuccessful. Please check email and password.", "danger")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    # ... existing signup code ...
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        hashed_password = bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8')
        new_user = User(username=request.form.get("username"), email=request.form.get("email"), password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Your account has been created! You are now able to log in.", "success")
        return redirect(url_for('login'))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)