from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import pdfkit
db = SQLAlchemy()
username = 'root'
password = ''
host = 'localhost'
db_name = 'hivabot_db'

app = Flask(__name__)

def create_app():
    # Inisialisasi DB
    app.config['SECRET_KEY'] = "bot-tele"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{username}:{password}@{host}/{db_name}'
    db.init_app(app)

    #konfigurasi wkhtmltopdf
    path_wkhtmltopdf = 'E:/wkhtmltopdf/bin/wkhtmltopdf.exe'  # Sesuaikan dengan path wkhtmltopdf Anda
    app.config['PDFKIT_CONFIG'] = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    from .views import views
    from .auth import auth
    from .webhooks import webhook_bp
    from .message_handler import message_handler
    from .diagnosa import diagnosa

    app.register_blueprint(views,url_prefix ="/")
    app.register_blueprint(auth,url_prefix ="/")
    app.register_blueprint(webhook_bp,url_prefix ="/")
    app.register_blueprint(message_handler,url_prefix ="/")
    app.register_blueprint(diagnosa,url_prefix ="/")

    from .models import User, Stadium, Term, Gejala, Rule, UserTelegram
 
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    return app

