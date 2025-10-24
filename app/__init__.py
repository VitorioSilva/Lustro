from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
import os

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuração TOTALMENTE por variáveis de ambiente
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '3306')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    
    # MELHORIA: Configuração mais robusta
    if all([db_host, db_user, db_password, db_name]):
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        print("Conectando ao MySQL...")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/lustro.db'
        print("Usando SQLite (desenvolvimento)")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # MELHORIA: JWT mais seguro
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if not jwt_secret:
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            jwt_secret = 'chave-temporaria-para-testes-local'
            print("Usando JWT key temporária (APENAS DESENVOLVIMENTO)")
        else:
            raise ValueError("JWT_SECRET_KEY é obrigatória em produção")
    
    app.config['JWT_SECRET_KEY'] = jwt_secret
    
    # CORS para frontend
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
    
    # Handlers de erro JWT
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({'error': 'Token de acesso não fornecido'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Token de acesso inválido'}), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({'error': 'Token expirado'}), 401
    
    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.agendamentos import agendamentos_bp
    from app.routes.servicos import servicos_bp
    from app.routes.veiculos import veiculos_bp
    from app.routes.admin import admin_bp
    from app.routes.admin_dashboard import admin_dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(agendamentos_bp, url_prefix='/api/agendamentos')
    app.register_blueprint(servicos_bp, url_prefix='/api/servicos')
    app.register_blueprint(veiculos_bp, url_prefix='/api/veiculos')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_dashboard_bp, url_prefix='/api/admin/dashboard')
    
    # Rota health check
    @app.route('/')
    def health_check():
        return jsonify({
            'status': 'OK', 
            'message': 'Lustro API running',
            'version': '1.0.0'
        })
    
    # Rota para inicializar o banco
    @app.route('/api/init-db', methods=['POST'])
    def init_database_route():
        try:
            from app.utils.database_init import init_database
            db.create_all()
            init_database()
            return jsonify({
                'message': 'Banco inicializado com sucesso!',
                'next_steps': 'Configure o admin através do painel'
            }), 200
        except Exception as e:
            return jsonify({'error': f'Erro ao inicializar banco: {str(e)}'}), 500

    # Rota para verificar status do banco
    @app.route('/api/check-db', methods=['GET'])
    def check_database():
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

    @app.route('/api/debug-db')
    def debug_database():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        using_mysql = 'mysql' in db_uri
        
        return jsonify({
            'database_type': 'MySQL' if using_mysql else 'SQLite',
            'using_production_db': using_mysql,
            'db_host_configurado': bool(os.getenv('DB_HOST')),
            'db_user_configurado': bool(os.getenv('DB_USER')),
            'todas_variaveis_presentes': all([
                os.getenv('DB_HOST'),
                os.getenv('DB_USER'), 
                os.getenv('DB_PASSWORD'),
                os.getenv('DB_NAME')
            ])
        })
    
    return app