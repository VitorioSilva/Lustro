from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Veiculo, User
from app.utils.security import validate_placa, error_response

veiculos_bp = Blueprint('veiculos', __name__)

@veiculos_bp.route('', methods=['GET'])
@jwt_required()
def listar_veiculos():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        veiculos = Veiculo.query.filter_by(user_id=current_user.id).all()
        
        return jsonify({
            'veiculos': [v.to_dict() for v in veiculos]
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@veiculos_bp.route('', methods=['POST'])
@jwt_required()
def criar_veiculo():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        data = request.get_json()
        
        if not data:
            return error_response('Dados JSON são obrigatórios')
        
        required_fields = ['placa', 'tipo']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'Campo {field} é obrigatório')
        
        # Validar placa
        if not validate_placa(data['placa']):
            return error_response('Formato de placa inválido')
        
        # Verificar se placa já existe para este usuário
        if Veiculo.query.filter_by(placa=data['placa'].upper(), user_id=current_user.id).first():
            return error_response('Veículo com esta placa já cadastrado', 409)
        
        # Validar tipo de veículo
        tipos_validos = ['hatch', 'sedan', 'suv', 'caminhonete', 'van']
        if data['tipo'].lower() not in tipos_validos:
            return error_response(f'Tipo de veículo inválido. Tipos válidos: {", ".join(tipos_validos)}')
        
        novo_veiculo = Veiculo(
            placa=data['placa'].upper().replace('-', ''),
            tipo=data['tipo'].lower(),
            user_id=current_user.id,
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