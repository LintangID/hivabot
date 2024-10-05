from flask import Blueprint, render_template, redirect, url_for, request, make_response, current_app
from . import db
from datetime import datetime
from sqlalchemy import and_
from flask_login import login_required
from werkzeug.security import generate_password_hash
from .models import User, Stadium, Gejala, Rule, Term, ProsesDiagnosa, UserTelegram
from .diagnosa import *
import pdfkit

views = Blueprint("views",__name__)

@views.route("/")
def home():
    return render_template('index.html')

@views.route("/dashboard")
@login_required
def dashboard():
    user_telegram = UserTelegram.query.all()
    riwayat = RiwayatDiagnosa.query.filter(RiwayatDiagnosa.hasil_diagnosa.isnot(None)).all()
    rule = Rule.query.all()
    jml_rule = len(rule)
    jml_user_telegram = len(user_telegram)
    jml_riwayat = len(riwayat)
    jml_stadium1 = sum(1 for item in riwayat if item.stadium.stadium == "Stadium 1") 
    jml_stadium2 = sum(1 for item in riwayat if item.stadium.stadium == "Stadium 2") 
    jml_stadium3 = sum(1 for item in riwayat if item.stadium.stadium == "Stadium 3") 
    jml_stadium4 = sum(1 for item in riwayat if item.stadium.stadium == "Stadium 4")
    if jml_riwayat > 0 :
        stadium1 =  (jml_stadium1/jml_riwayat)*100
        stadium2 =  (jml_stadium2/jml_riwayat)*100
        stadium3 =  (jml_stadium3/jml_riwayat)*100
        stadium4 =  (jml_stadium4/jml_riwayat)*100
    else :
        stadium1 =  0
        stadium2 =  0
        stadium3 =  0
        stadium4 =  0
    return render_template('pages/dashboard.html', 
                           current_page = 'dashboard',
                           user_telegram = user_telegram,
                           riwayat = riwayat,
                           jml_rule = jml_rule, 
                           jml_user_telegram = jml_user_telegram, 
                           jml_riwayat = jml_riwayat, 
                           stadium1 = stadium1, 
                           stadium2 = stadium2,
                           stadium3 = stadium3,
                           stadium4 = stadium4
                        )

# Riwayat
@views.route("/riwayat")
@login_required
def riwayat():
    riwayat = RiwayatDiagnosa.query.filter(RiwayatDiagnosa.hasil_diagnosa.isnot(None)).order_by(RiwayatDiagnosa.tanggal.desc()).all()
    stadiums = Stadium.query.all()
    return render_template('pages/riwayat/index-riwayat.html', current_page = 'riwayat', items = riwayat, stadiums = stadiums)

@views.route("/print-riwayat",methods=['POST'])
@login_required
def print_riwayat():
    tanggal_awal_str = request.form.get('tanggal1')
    tanggal_akhir_str = request.form.get('tanggal2')
    selected_stadium = request.form.get('stadium_id')

    waktu_awal = tanggal_awal_str + ' 00:00:00'
    waktu_akhir = tanggal_akhir_str + ' 23:59:59'

    # Konversi nilai string ke objek datetime
    tanggal_awal = datetime.strptime(waktu_awal, '%Y-%m-%d %H:%M:%S')
    tanggal_akhir = datetime.strptime(waktu_akhir, '%Y-%m-%d %H:%M:%S')

    if selected_stadium == "all":
        riwayat = RiwayatDiagnosa.query.filter(and_(RiwayatDiagnosa.tanggal.between(tanggal_awal, tanggal_akhir)), RiwayatDiagnosa.hasil_diagnosa.isnot(None)).all()
    else :
        riwayat = RiwayatDiagnosa.query.filter(and_(RiwayatDiagnosa.tanggal.between(tanggal_awal, tanggal_akhir)), RiwayatDiagnosa.hasil_diagnosa == selected_stadium ).all()

    rendered = render_template('pages/riwayat/riwayat-diagnosa-template.html', items = riwayat)
    pdf = pdfkit.from_string(rendered, False, configuration=current_app.config['PDFKIT_CONFIG'])
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=output.pdf'
    return response

@views.route("/delete-riwayat/<id>",methods=['POST'])
@login_required
def delete_riwayat(id):
    riwayat = RiwayatDiagnosa.query.filter_by(id=id).first()
    db.session.delete(riwayat)
    db.session.commit()
    return redirect(url_for('views.riwayat'))

# User Telegram
@views.route("/user-telegram")
@login_required
def user_telegram():
    user_telegram = UserTelegram.query.order_by(UserTelegram.id.desc()).all()
    return render_template('pages/user-telegram/index-user-telegram.html', current_page = 'user-telegram', items = user_telegram)

# Stadium
@views.route("/stadium",methods=['GET','POST'])
@login_required
def stadium():
    if request.method == 'POST':
        kode = request.form.get("kode")
        stadium = request.form.get("stadium")
        stadium_exist = Stadium.query.filter_by(kode=kode).first()
        if stadium_exist:
            return "stadium already exist"
        else:
            new_stadium = Stadium(kode=kode,stadium = stadium)
            db.session.add(new_stadium)
            db.session.commit()
    stadiums = Stadium.query.all()
    return render_template('pages/stadium/index-stadium.html', current_page = 'stadium', stadiums=stadiums)

@views.route("/delete-stadium/<id>",methods=['POST'])
@login_required
def delete_stadium(id):
    stadium = Stadium.query.filter_by(id=id).first()
    db.session.delete(stadium)
    db.session.commit()
    return redirect(url_for('views.stadium'))

# Gejala
@views.route("/gejala",methods=['GET','POST'])
@login_required
def gejala():
    if request.method == 'POST':
        kode = request.form.get("kode")
        gejala = request.form.get("gejala")
        gejala_exist = Gejala.query.filter_by(kode=kode).first()
        if gejala_exist:
            return "gejala already exist"
        else:
            new_gejala = Gejala(kode=kode,gejala = gejala)
            db.session.add(new_gejala)
            db.session.commit()
    items = Gejala.query.order_by(Gejala.kode.desc()).all()
    return render_template('pages/gejala/index-gejala.html', current_page = 'gejala', items=items)

@views.route("/edit-gejala/<id>",methods=['POST'])
@login_required
def edit_gejala(id):
    kode = request.form.get("kode")
    gejala = request.form.get("gejala")
    items = Gejala.query.filter_by(id=id).first()
    if not kode:
        items.kode = items.kode
    else:
        items.kode = kode
    if not gejala:
        items.gejala = items.gejala
    else:
        items.gejala = gejala
    db.session.commit()
    return redirect(url_for('views.gejala'))

@views.route("/delete-gejala/<id>",methods=['POST'])
@login_required
def delete_gejala(id):
    gejala = Gejala.query.filter_by(id=id).first()
    db.session.delete(gejala)
    db.session.commit()
    return redirect(url_for('views.gejala'))

# Rule
@views.route("/rule",methods=['GET','POST'])
@login_required
def rule():
    if request.method == 'POST':
        gejala_id = request.form.get("gejala_id")
        stadium_id = request.form.get("stadium_id")
        cf = request.form.get("cf")
        new_rule = Rule(gejala_id=gejala_id,stadium_id = stadium_id, cf = cf)
        db.session.add(new_rule)
        db.session.commit()
    items = Rule.query.order_by(Rule.id.asc()).all()
    gejalas = Gejala.query.all()
    stadiums = Stadium.query.all()
    terms = Term.query.all()
    return render_template('pages/rule/index-rule.html', current_page = 'rule', items=items, gejalas = gejalas, stadiums = stadiums, terms = terms )

@views.route("/edit-rule/<id>",methods=['POST'])
@login_required
def edit_rule(id):
    gejala_id = request.form.get("gejala_id")
    stadium_id = request.form.get("stadium_id")
    cf = request.form.get("cf")
    item = Rule.query.filter_by(id=id).first()
    if not gejala_id:
        item.gejala_id = item.gejala_id
    else:
        item.gejala_id = gejala_id
    if not stadium_id:
        item.stadium_id = item.stadium_id
    else:
        item.stadium_id = stadium_id
    if not cf:
        item.stadium_id = item.stadium_id
    else:
        item.cf = cf
    db.session.commit()
    return redirect(url_for('views.rule'))

@views.route("/delete-rule/<id>",methods=['POST'])
@login_required
def delete_rule(id):
    rule = Rule.query.filter_by(id=id).first()
    db.session.delete(rule)
    db.session.commit()
    return redirect(url_for('views.rule'))

# User
@views.route("/user",methods=['GET','POST'])
@login_required
def user():
    if request.method == 'POST':
        username = request.form.get("username")
        fullname = request.form.get("fullname")
        password = request.form.get("password")

        user_exist = User.query.filter_by(username=username).first()
        if user_exist:
            return "username already exist"
        else:
            new_user = User(username=username,fullname = fullname ,password=generate_password_hash(password, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
    users = User.query.order_by(User.id.desc()).all()
    return render_template('pages/user/index-user.html', current_page = 'user', users=users)

@views.route("/edit-user/<id>",methods=['POST'])
@login_required
def edit_user(id):
    username = request.form.get("username")
    fullname = request.form.get("fullname")
    password = request.form.get("password")
    user = User.query.filter_by(id=id).first()
    if not username:
        user.username = user.username
    else:
        user.username = username
    if not fullname:
        user.fullname = user.fullname
    else:
        user.fullname = fullname
    if not password:
        user.password = user.password
    else:
        user.password = generate_password_hash(password, method='pbkdf2:sha256')
    db.session.commit()
    return redirect(url_for('views.user'))

@views.route("/delete-user/<id>",methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('views.user'))