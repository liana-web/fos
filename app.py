from flask import Flask, render_template, request, redirect, url_for, flash
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
import sqlite3

app = Flask (__name__)
app.secret_key = 'liana1234' # required for flashing messages
DB_NAME = 'fos.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
        ''')
        conn.commit()

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    
    user = session.get('username')  # Try to get username from session
    if not user:
        user = "Guest"  # Default if no user is found
    return render_template('home.html', user=user)

@app.route('/register')
def register():
    return render_template('home.html')

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    """Add new customer"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO customers (name, email) VALUES (?, ?)', (name, email))
            conn.commit()
            flash("✅ User added successfully!", "success")
        except sqlite3.IntegrityError:
            return "Email already exists!"
        finally:
            conn.close()
        return redirect(url_for('add_customer'))

    return render_template('add_customer.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    