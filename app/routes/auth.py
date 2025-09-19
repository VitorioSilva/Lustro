from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models import User
from app.utils.security import error_response

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        # Validar dados obrigatórios
        if not data or 'email' not in data or 'senha' not in data:
            return error_response('Email e senha são obrigatórios')

        # Buscar usuário
        user = User.query.filter_by(email=data['email']).first()

        # Verificar se usuário existe e senha está correta
        if not user or not user.check_password(data['senha']):
            return error_response('Credenciais inválidas', 401)

        # Criar token JWT - usar apenas o ID como string
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'message': 'Login realizado com sucesso',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)