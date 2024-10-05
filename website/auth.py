from flask import Blueprint, render_template, redirect, url_for, request, session
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth",__name__)

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password,password):
                login_user(user, remember=True)
                session['fullname'] = user.fullname
                return redirect(url_for('views.dashboard'))
    return render_template('auth/login.html')   

@auth.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        fullname = request.form.get("fullname")
        password = request.form.get("password")

        user_exist = User.query.filter_by(username=username).first()
        if user_exist:
            return "username already exist"
        else:
            new_user = User(username=username,fullname=fullname, password=generate_password_hash(password, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user,remember=True)
            session['username'] = username
            return redirect(url_for('views.dashboard'))

    return render_template('auth/signup.html')   

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("views.home"))   