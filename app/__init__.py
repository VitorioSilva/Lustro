from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    # Validar configs críticas
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("DATABASE_URL não definido no .env")
    if not app.config['JWT_SECRET_KEY']:
        raise ValueError("JWT_SECRET_KEY não definido no .env")

    # Habilitar CORS
    CORS(app)

    # Inicializar extensões
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Configurar user loader para JWT
    from app.models import User
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.get(int(identity))

    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.agendamentos import agendamentos_bp
    from app.routes.servicos import servicos_bp
    from app.routes.veiculos import veiculos_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(agendamentos_bp, url_prefix='/api/agendamentos')
    app.register_blueprint(servicos_bp, url_prefix='/api/servicos')
    app.register_blueprint(veiculos_bp, url_prefix='/api/veiculos')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Comando CLI para inicializar o banco
    @app.cli.command("init-db")
    def init_db_command():
        # Inicializa o banco de dados com dados padrão
        from app.utils.database_init import init_database
        db.create_all()
        init_database()
        print("Banco inicializado com dados padrão!")

    return app