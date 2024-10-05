from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    fullname = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

class UserTelegram(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    id_user_telegram = db.Column(db.String(150), unique=True)
    name = db.Column(db.String(150))
    phone_number = db.Column(db.String(20), nullable=True, default='-')
    riwayat_diagnosa = db.relationship('RiwayatDiagnosa', backref ='user_telegram', passive_deletes = True)

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(20))
    nilai_cf = db.Column(db.Float)
    rules = db.relationship('Rule', backref ='term', passive_deletes = True)

class Stadium(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(3), unique=True)
    stadium = db.Column(db.String(150))
    rules = db.relationship('Rule', backref ='stadium', passive_deletes = True)
    riwayat_diagnosa = db.relationship('RiwayatDiagnosa', backref ='stadium', passive_deletes = True)

class Gejala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(5), unique=True)
    gejala = db.Column(db.String(250))
    rules = db.relationship('Rule', backref ='gejala', passive_deletes = True)
    proses_diagnosa = db.relationship('ProsesDiagnosa', backref ='gejala', passive_deletes = True)

class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gejala_id = db.Column(db.Integer, db.ForeignKey('gejala.id',ondelete="CASCADE"), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id',ondelete="CASCADE"), nullable=False)
    cf = db.Column(db.Integer, db.ForeignKey('term.id',ondelete="CASCADE"), nullable=False)

class RiwayatDiagnosa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_telegram_id = db.Column(db.String(150), db.ForeignKey('user_telegram.id_user_telegram',ondelete="CASCADE"), nullable=False)
    hasil_diagnosa = db.Column(db.Integer, db.ForeignKey('stadium.id',ondelete="CASCADE"))
    hasil_cf = db.Column(db.Float)
    tanggal = db.Column(db.DateTime(timezone=True),default=func.now())
    proses_diagnosa = db.relationship('ProsesDiagnosa', backref ='riwayat', passive_deletes = True)

class ProsesDiagnosa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    riwayat_id = db.Column(db.Integer, db.ForeignKey('riwayat_diagnosa.id', ondelete="CASCADE"),nullable=False)
    gejala_id = db.Column(db.Integer, db.ForeignKey('gejala.id', ondelete="CASCADE"),nullable=False)
    cf = db.Column(db.Float)