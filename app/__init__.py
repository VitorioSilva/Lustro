from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configurações seguras via .env
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///lustro.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    
    # Validar configs críticas
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("DATABASE_URL não definido no .env")
    if not app.config['JWT_SECRET_KEY']:
        raise ValueError("JWT_SECRET_KEY não definido no .env")
    
    # Inicializar extensões
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    return app