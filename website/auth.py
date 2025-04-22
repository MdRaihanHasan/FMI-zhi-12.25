# Created by Zhi 2024.9

from flask import Blueprint, render_template, request, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

def create_users():
    # This function will be called to create users
    if not User.query.first():  # Only create users if the table is empty
        User0 = User(username="zhi", password=generate_password_hash("zhi123", method='pbkdf2:sha256'), attribute="administrator")
        User1 = User(username="sashini", password=generate_password_hash("sashini123", method='pbkdf2:sha256'), attribute="contributor")
        User2 = User(username="daming", password=generate_password_hash("daming123", method='pbkdf2:sha256'), attribute="expert")
        User3 = User(username="josh", password=generate_password_hash("josh123", method='pbkdf2:sha256'), attribute="administrator")

        db.session.add(User0)
        db.session.add(User1)
        db.session.add(User2)
        db.session.add(User3)
        db.session.commit()

@auth.route("/", methods=['GET', 'POST'])
@auth.route("/userlogin", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)  # login_user provided by flask_login
                print('Logged in successfully')
                return redirect(url_for('views.welcome'))  # Ensure correct redirection here
            else:
                print('Incorrect password')
        else:
            print('User does not exist')
    return render_template("userlogin.html")

@auth.route('/logout')
@login_required
def logout():
    return redirect(url_for('auth.login'))