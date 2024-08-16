from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    total_pages = db.Column(db.Integer, nullable=False)
    pages_read = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@login_required
def index():
    books = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', books=books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        flash('File uploaded successfully', 'success')
    else:
        flash('Invalid file type. Please upload a PDF.', 'danger')
    return redirect(url_for('index'))

@app.route('/add_book', methods=['POST'])
@login_required
def add_book():
    title = request.form.get('title')
    total_pages = int(request.form.get('total_pages'))
    new_book = Book(title=title, total_pages=total_pages, user_id=current_user.id)
    db.session.add(new_book)
    db.session.commit()
    flash('Book added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/update_progress/<int:book_id>', methods=['POST'])
@login_required
def update_progress(book_id):
    book = Book.query.get(book_id)
    if book and book.user_id == current_user.id:
        pages_read = int(request.form.get('pages_read'))
        book.pages_read = pages_read
        db.session.commit()
        flash('Progress updated successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists('books.db'):
        db.create_all()
    app.run(debug=True)
