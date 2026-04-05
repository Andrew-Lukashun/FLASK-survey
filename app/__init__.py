# Инициализация Flask приложения
from flask import Flask
from app.config import APP_CONFIG

def create_app():
    app = Flask(__name__)
    app.secret_key = APP_CONFIG.get('secret_key')
    return app
