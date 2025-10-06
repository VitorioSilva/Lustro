from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models import User
from app.utils.security import validate_email, error_response

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data:
            return error_response('Dados JSON são obrigatórios')
        
        email = data.get('email')
        senha = data.get('senha')
        
        if not email or not senha:
            return error_response('Email e senha são obrigatórios')
        
        # Validar formato do email
        if not validate_email(email):
            return error_response('Formato de email inválido')
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        # Verificar se usuário existe e senha está correta
        if not user or not user.check_password(senha):
            return error_response('Credenciais inválidas', 401)
        
        # Criar token JWT
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)