# Created by Zhi 2024.9

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager 
from os import path
import os

db = SQLAlchemy()
DB_NAME = "database.db"


class Config:
    # 基本配置
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_NAME}'

    # cpabe相关配置
    CPABE_KEYS_DIR = 'website/keys'  # cpabe密钥存储位置

    # 角色相关配置
    ROLE_LEVELS = {
        'administrator': 3,
        'expert': 2,
        'contributor': 1
    }

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # 从Config类加载配置
    db.init_app(app)

    # 创建必要的目录
    for folder in ['metadata', app.config['CPABE_KEYS_DIR'], 'temp_decrypted']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f'Created folder: {folder}')

    # Define the folder for metadata
    metadata_folder = 'metadata'
    
    # Create the folder if it doesn't exist
    if not os.path.exists(metadata_folder):
        os.makedirs(metadata_folder)
        print(f'Created folder: {metadata_folder}')

    from .views import views
    from .auth import auth
    from . import fm
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User
    from .auth import create_users

    create_database(app)

    # Initialize LoginManager here
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Redirect to login page if not authenticated
    login_manager.init_app(app)

    # Define a user loader callback
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    with app.app_context():
        create_users()

    return app

def create_database(app):
    if not path.exists('website/'+ DB_NAME):
        with app.app_context():
            db.create_all()
            print('Created Database!')
