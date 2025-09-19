from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Veiculo, User
from app.utils.security import error_response

veiculos_bp = Blueprint('veiculos', __name__)

@veiculos_bp.route('', methods=['GET'])
@jwt_required()
def listar_veiculos():
    try:
        # Obter usuário atual
        current_user = User.query.get(int(get_jwt_identity()))
        user_id = current_user.id
        
        veiculos = Veiculo.query.filter_by(user_id=user_id).all()
        return jsonify({
            'veiculos': [v.to_dict() for v in veiculos]
        }), 200
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@veiculos_bp.route('', methods=['POST'])
@jwt_required()
def criar_veiculo():
    try:
        # Obter usuário atual
        current_user = User.query.get(int(get_jwt_identity()))
        user_id = current_user.id
        
        data = request.get_json()
        
        required_fields = ['placa', 'tipo']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(f'Campo {field} é obrigatório')
        
        # Verificar se placa já existe para este usuário
        if Veiculo.query.filter_by(placa=data['placa'], user_id=user_id).first():
            return error_response('Veículo com esta placa já cadastrado', 409)
        
        novo_veiculo = Veiculo(
            placa=data['placa'],
            tipo=data['tipo'],
            user_id=user_id,
            marca=data.get('marca'),
            modelo=data.get('modelo'),
            cor=data.get('cor')
        )
        
        db.session.add(novo_veiculo)
        db.session.commit()
        
        return jsonify({
            'message': 'Veículo cadastrado com sucesso',
            'veiculo': novo_veiculo.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)