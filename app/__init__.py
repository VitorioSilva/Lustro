from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuração do banco
    if os.getenv('VERCEL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/lustro.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///lustro.db')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'chave-temporaria-local')
    
    # Validar configs críticas
    if not app.config['JWT_SECRET_KEY']:
        raise ValueError("JWT_SECRET_KEY não definido")
    
    # CORS para frontend
    CORS(app, origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.now.sh"
    ])
    
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
    
    # Handlers de erro JWT
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({'error': 'Token de acesso não fornecido'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Token de acesso inválido'}), 401
    
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
    
    # Rota health check
    @app.route('/')
    def health_check():
        return jsonify({'status': 'OK', 'message': 'Lustro API running'})
    
    # Comando CLI para inicializar o banco
    @app.route('/api/init-db', methods=['POST'])
    def init_database_route():
        """Rota para inicializar o banco no Vercel"""
        try:
            from app.utils.database_init import init_database
            db.create_all()
            init_database()
            return jsonify({
                'message': '✅ Banco inicializado com sucesso!',
                'admin': 'admin@gmail.com / admin12345678',
                'servicos': 'Lavagem Externa, Interna e Completa criados'
            }), 200
        except Exception as e:
            return jsonify({'error': f'Erro ao inicializar banco: {str(e)}'}), 500

    @app.route('/api/check-db', methods=['GET'])
    def check_database():
        """Rota para verificar status do banco"""
        try:
            from app.models import User, Servico
            user_count = User.query.count()
            servico_count = Servico.query.count()
            
            return jsonify({
                'database_status': 'OK',
                'users_count': user_count,
                'servicos_count': servico_count,
                'tables_created': True
            }), 200
        except Exception as e:
            return jsonify({
                'database_status': 'NOT_INITIALIZED',
                'error': str(e)
            }), 500
    
    return app