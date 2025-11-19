from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, JWTManager
from app import db
from app.models import User, Administrador
from app.utils.security import validate_email, validate_password_strength, validate_name, error_response

auth_bp = Blueprint('auth', __name__)

# Adicione uma blacklist para tokens (em produção use Redis ou database)
token_blacklist = set()

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        if not data:
            return error_response('Dados JSON são obrigatórios')

        email = data.get('email')
        senha = data.get('senha')

        if not email or not senha:
            return error_response('Email e senha são obrigatórios')

        is_valid, message = validate_email(email)
        if not is_valid:
            return error_response(message)

        # Primeiro tenta encontrar como usuário normal
        user = User.query.filter_by(email=email.lower().strip()).first()

        if user and user.check_password(senha):
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                'message': 'Login realizado com sucesso',
                'access_token': access_token,
                'user': user.to_dict(),
                'tipo': 'cliente'
            }), 200

        # Se não encontrou usuário, tenta como admin
        admin = Administrador.query.filter_by(email=email.lower().strip()).first()
        if admin and admin.check_password(senha):
            access_token = create_access_token(identity=str(admin.id))
            return jsonify({
                'message': 'Login administrativo realizado com sucesso',
                'access_token': access_token,
                'user': admin.to_dict(),
                'tipo': 'admin'
            }), 200

        return error_response('Email ou senha incorretos', 401)

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        if not data:
            return error_response('Dados JSON são obrigatórios')

        required_fields = ['nome', 'email', 'senha', 'confirmar_senha']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'Campo {field} é obrigatório')

        if data['senha'] != data['confirmar_senha']:
            return error_response('Senhas não coincidem')

        is_valid, message = validate_name(data['nome'])
        if not is_valid:
            return error_response(message)

        is_valid, message = validate_email(data['email'])
        if not is_valid:
            return error_response(message)

        is_valid, message = validate_password_strength(data['senha'])
        if not is_valid:
            return error_response(message)

        email_clean = data['email'].lower().strip()
        if User.query.filter_by(email=email_clean).first():
            return error_response('Email já cadastrado', 409)

        new_user = User(
            nome=data['nome'].strip(),
            email=email_clean,
            telefone=data.get('telefone')
        )
        new_user.set_password(data['senha'])

        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=str(new_user.id))

        return jsonify({
            'message': 'Usuário criado com sucesso',
            'access_token': access_token,
            'user': new_user.to_dict(),
            'tipo': 'cliente'
        }), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()

        if not data:
            return error_response('Dados JSON são obrigatórios')

        email = data.get('email')
        senha = data.get('senha')

        if not email or not senha:
            return error_response('Email e senha são obrigatórios')

        admin = Administrador.query.filter_by(email=email.lower().strip()).first()

        if not admin or not admin.check_password(senha):
            return error_response('Credenciais administrativas incorretas', 401)

        access_token = create_access_token(identity=str(admin.id))

        return jsonify({
            'message': 'Login administrativo realizado com sucesso',
            'access_token': access_token,
            'user': admin.to_dict(),
            'tipo': 'admin'
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Rota de logout para cliente
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        # Adiciona o token à blacklist
        jti = get_jwt()["jti"]
        token_blacklist.add(jti)
        
        return jsonify({
            'message': 'Logout realizado com sucesso'
        }), 200
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Rota de logout para admin
@auth_bp.route('/admin/logout', methods=['POST'])
@jwt_required()
def admin_logout():
    try:
        # Adiciona o token à blacklist
        jti = get_jwt()["jti"]
        token_blacklist.add(jti)
        
        return jsonify({
            'message': 'Logout administrativo realizado com sucesso'
        }), 200
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)