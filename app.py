from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Замените на свой секретный ключ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


# Модель заметки
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('notes', lazy=True))


@app.route('/')
def index():
    if 'user_id' in session:
        notes = Note.query.filter_by(user_id=session['user_id']).all()
        return render_template('notebook.html', notes=notes)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists!', 'danger')
            return redirect(url_for('register'))

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Invalid credentials!', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/add_note', methods=['POST'])
def add_note():
    if 'user_id' in session:
        content = request.form['content']
        user_id = session['user_id']
        new_note = Note(content=content, user_id=user_id)
        db.session.add(new_note)
        db.session.commit()
        flash('Note added successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/edit_note/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id != session['user_id']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        note.content = request.form['content']
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_note.html', note=note)


@app.route('/delete_note/<int:id>')
def delete_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id == session['user_id']:
        db.session.delete(note)
        db.session.commit()
        flash('Note deleted!', 'success')
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3000, debug=True)