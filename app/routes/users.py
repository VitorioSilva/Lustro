from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils.security import validate_email, validate_password, validate_phone, error_response

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data:
            return error_response('Dados JSON são obrigatórios')
        
        required_fields = ['nome', 'email', 'senha']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'Campo {field} é obrigatório')
        
        # Validar email
        if not validate_email(data['email']):
            return error_response('Email inválido')
        
        # Validar senha
        is_valid, message = validate_password(data['senha'])
        if not is_valid:
            return error_response(message)
        
        # Validar telefone se fornecido
        if data.get('telefone') and not validate_phone(data['telefone']):
            return error_response('Formato de telefone inválido. Use (00) 00000-0000')
        
        # Verificar se email já existe
        if User.query.filter_by(email=data['email']).first():
            return error_response('Email já cadastrado', 409)
        
        # Criar novo usuário
        new_user = User(
            nome=data['nome'].strip(),
            email=data['email'].lower().strip(),
            telefone=data.get('telefone')
        )
        new_user.set_password(data['senha'])
        
        # Salvar no banco
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário criado com sucesso',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)