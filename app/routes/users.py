from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User
from app.utils.security import (
    validate_email, validate_password_strength, validate_phone, 
    validate_name, error_response
)

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['POST'])
def create_user():
    try:
        data = request.get_json()

        if not data:
            return error_response('Dados JSON são obrigatórios')

        required_fields = ['nome', 'email', 'senha', 'confirmar_senha']
        for field in required_fields:
            if field not in data or not data[field]:
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

        if data.get('telefone'):
            is_valid, message = validate_phone(data['telefone'])
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

        return jsonify({
            'message': 'Usuário criado com sucesso',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return error_response('Usuário não encontrado', 404)

        return jsonify({
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@users_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return error_response('Usuário não encontrado', 404)
            
        data = request.get_json()

        if 'nome' in data:
            is_valid, message = validate_name(data['nome'])
            if not is_valid:
                return error_response(message)
            current_user.nome = data['nome'].strip()

        if 'telefone' in data:
            is_valid, message = validate_phone(data['telefone'])
            if not is_valid:
                return error_response(message)
            current_user.telefone = data['telefone']

        db.session.commit()

        return jsonify({
            'message': 'Dados atualizados com sucesso',
            'user': current_user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@users_bp.route('/me/password', methods=['PUT'])
@jwt_required()
def update_password():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return error_response('Usuário não encontrado', 404)

        data = request.get_json()

        required = ['senha_atual', 'nova_senha', 'confirmar_senha']
        for field in required:
            if not data.get(field):
                return error_response(f'Campo {field} é obrigatório')

        if not current_user.check_password(data['senha_atual']):
            return error_response('Senha atual incorreta')

        if data['nova_senha'] != data['confirmar_senha']:
            return error_response('Novas senhas não coincidem')

        is_valid, message = validate_password_strength(data['nova_senha'])
        if not is_valid:
            return error_response(message)

        current_user.set_password(data['nova_senha'])
        db.session.commit()

        return jsonify({
            'message': 'Senha atualizada com sucesso'
        }), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)