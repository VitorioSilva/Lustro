from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Veiculo, User
from app.utils.security import validate_placa, error_response
from datetime import datetime

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
        
        is_valid, message = validate_placa(data['placa'])
        if not is_valid:
            return error_response(message)
        
        placa_limpa = data['placa'].upper().replace('-', '').replace(' ', '')
        if Veiculo.query.filter_by(placa=placa_limpa, user_id=current_user.id).first():
            return error_response('Veículo com esta placa já cadastrado', 409)
        
        tipos_validos = ['hatch', 'sedan', 'suv', 'caminhonete', 'van']
        if data['tipo'].lower() not in tipos_validos:
            return error_response(f'Tipo de veículo inválido. Tipos válidos: {", ".join(tipos_validos)}')
        
        MAX_VEICULOS_POR_USUARIO = 5
        veiculos_count = Veiculo.query.filter_by(user_id=current_user.id).count()
        if veiculos_count >= MAX_VEICULOS_POR_USUARIO:
            return error_response(f'Limite máximo de {MAX_VEICULOS_POR_USUARIO} veículos atingido', 400)
        
        novo_veiculo = Veiculo(
            placa=placa_limpa,
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

# NOVA ROTA: Atualizar veículo
@veiculos_bp.route('/<int:veiculo_id>', methods=['PUT'])
@jwt_required()
def atualizar_veiculo(veiculo_id):
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        veiculo = Veiculo.query.get_or_404(veiculo_id)
        
        if veiculo.user_id != current_user.id:
            return error_response('Acesso negado', 403)
        
        data = request.get_json()
        
        if 'marca' in data:
            veiculo.marca = data['marca'].strip() if data['marca'] else None
        
        if 'modelo' in data:
            veiculo.modelo = data['modelo'].strip() if data['modelo'] else None
        
        if 'cor' in data:
            veiculo.cor = data['cor'].strip() if data['cor'] else None
        
        if 'tipo' in data:
            tipos_validos = ['hatch', 'sedan', 'suv', 'caminhonete', 'van']
            if data['tipo'].lower() not in tipos_validos:
                return error_response(f'Tipo de veículo inválido')
            veiculo.tipo = data['tipo'].lower()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Veículo atualizado com sucesso',
            'veiculo': veiculo.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# NOVA ROTA: Deletar veículo
@veiculos_bp.route('/<int:veiculo_id>', methods=['DELETE'])
@jwt_required()
def deletar_veiculo(veiculo_id):
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        veiculo = Veiculo.query.get_or_404(veiculo_id)
        
        if veiculo.user_id != current_user.id:
            return error_response('Acesso negado', 403)
        
        from app.models import Agendamento
        
        agendamentos_futuros = Agendamento.query.filter(
            Agendamento.veiculo_id == veiculo_id,
            Agendamento.data_agendamento >= datetime.now(),
            Agendamento.status == 'confirmado'
        ).count()
        
        if agendamentos_futuros > 0:
            return error_response(
                'Não é possível excluir veículo com agendamentos futuros. Cancele os agendamentos primeiro.',
                400
            )
        
        db.session.delete(veiculo)
        db.session.commit()
        
        return jsonify({
            'message': 'Veículo excluído com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)