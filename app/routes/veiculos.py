from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Veiculo, User, ModeloVeiculo, Agendamento
from app.utils.security import validate_placa, error_response
from datetime import datetime

veiculos_bp = Blueprint('veiculos', __name__)

@veiculos_bp.route('', methods=['GET'])
@jwt_required()
def listar_veiculos():
    try:
        current_user_id = get_jwt_identity()
        veiculos = Veiculo.query.filter_by(usuario_id=current_user_id).all()

        veiculos_completos = []
        for veiculo in veiculos:
            veiculo_dict = veiculo.to_dict()
            modelo = ModeloVeiculo.query.get(veiculo.modelo_veiculo_id)
            veiculo_dict['modelo_nome'] = modelo.nome if modelo else 'N/A'
            veiculos_completos.append(veiculo_dict)

        return jsonify({
            'veiculos': veiculos_completos
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@veiculos_bp.route('', methods=['POST'])
@jwt_required()
def criar_veiculo():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return error_response('Dados JSON são obrigatórios')

        required_fields = ['placa', 'nome_proprietario', 'telefone', 'modelo_veiculo_id']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'Campo {field} é obrigatório')

        is_valid, message = validate_placa(data['placa'])
        if not is_valid:
            return error_response(message)

        placa_limpa = data['placa'].upper().replace('-', '').replace(' ', '')
        
        # Verificar se já existe veículo com esta placa (para qualquer usuário)
        veiculo_existente = Veiculo.query.filter_by(placa=placa_limpa).first()
        if veiculo_existente:
            return error_response('Veículo com esta placa já cadastrado', 409)

        # Verificar limite de veículos por usuário
        MAX_VEICULOS_POR_USUARIO = 5
        veiculos_count = Veiculo.query.filter_by(usuario_id=current_user_id).count()
        if veiculos_count >= MAX_VEICULOS_POR_USUARIO:
            return error_response(f'Limite máximo de {MAX_VEICULOS_POR_USUARIO} veículos atingido', 400)

        # Verificar se o modelo existe
        modelo = ModeloVeiculo.query.get(data['modelo_veiculo_id'])
        if not modelo:
            return error_response('Modelo de veículo não encontrado', 404)

        novo_veiculo = Veiculo(
            placa=placa_limpa,
            nome_proprietario=data['nome_proprietario'],
            telefone=data['telefone'],
            modelo_veiculo_id=data['modelo_veiculo_id'],
            usuario_id=current_user_id
        )

        db.session.add(novo_veiculo)
        db.session.commit()

        veiculo_dict = novo_veiculo.to_dict()
        veiculo_dict['modelo_nome'] = modelo.nome

        return jsonify({
            'message': 'Veículo cadastrado com sucesso',
            'veiculo': veiculo_dict
        }), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@veiculos_bp.route('/<int:veiculo_id>', methods=['PUT'])
@jwt_required()
def atualizar_veiculo(veiculo_id):
    try:
        current_user_id = get_jwt_identity()
        veiculo = Veiculo.query.get_or_404(veiculo_id)

        if veiculo.usuario_id != current_user_id:
            return error_response('Acesso negado', 403)

        data = request.get_json()

        if 'nome_proprietario' in data:
            veiculo.nome_proprietario = data['nome_proprietario'].strip()

        if 'telefone' in data:
            veiculo.telefone = data['telefone'].strip()

        if 'modelo_veiculo_id' in data:
            modelo = ModeloVeiculo.query.get(data['modelo_veiculo_id'])
            if not modelo:
                return error_response('Modelo de veículo não encontrado', 404)
            veiculo.modelo_veiculo_id = data['modelo_veiculo_id']

        db.session.commit()

        veiculo_dict = veiculo.to_dict()
        veiculo_dict['modelo_nome'] = modelo.nome if veiculo.modelo else 'N/A'

        return jsonify({
            'message': 'Veículo atualizado com sucesso',
            'veiculo': veiculo_dict
        }), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@veiculos_bp.route('/<int:veiculo_id>', methods=['DELETE'])
@jwt_required()
def deletar_veiculo(veiculo_id):
    try:
        current_user_id = get_jwt_identity()
        veiculo = Veiculo.query.get_or_404(veiculo_id)

        if veiculo.usuario_id != current_user_id:
            return error_response('Acesso negado', 403)

        # Verificar se existem agendamentos futuros para este veículo
        agendamentos_futuros = Agendamento.query.filter(
            Agendamento.veiculo_id == veiculo_id,
            Agendamento.data_agendamento >= datetime.now().date(),
            Agendamento.status.in_(['pendente', 'confirmado'])
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