from flask import Flask, render_template 
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy

app = Flask (__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)
    