from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Servico, User
from app.utils.security import error_response

servicos_bp = Blueprint('servicos', __name__)

# Listar serviços (acesso público)
@servicos_bp.route('', methods=['GET'])
def listar_servicos():
    try:
        servicos = Servico.query.filter_by(ativo=True).all()
        return jsonify({
            'servicos': [s.to_dict() for s in servicos]
        }), 200
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Criar serviço (apenas admin)
@servicos_bp.route('', methods=['POST'])
@jwt_required()
def criar_servico():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso negado. Apenas administradores.', 403)
        
        data = request.get_json()
        required_fields = ['nome', 'descricao', 'preco_base', 'duracao_minutos']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'Campo {field} é obrigatório')
        
        if Servico.query.filter_by(nome=data['nome']).first():
            return error_response('Serviço com este nome já existe', 409)
        
        novo_servico = Servico(
            nome=data['nome'],
            descricao=data['descricao'],
            preco_base=float(data['preco_base']),
            duracao_minutos=int(data['duracao_minutos'])
        )
        
        db.session.add(novo_servico)
        db.session.commit()
        
        return jsonify({
            'message': 'Serviço criado com sucesso',
            'servico': novo_servico.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Atualizar serviço (apenas admin)
@servicos_bp.route('/<int:servico_id>', methods=['PUT'])
@jwt_required()
def atualizar_servico(servico_id):
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso negado. Apenas administradores.', 403)
        
        servico = Servico.query.get_or_404(servico_id)
        data = request.get_json()
        
        if 'nome' in data:
            servico.nome = data['nome']
        if 'descricao' in data:
            servico.descricao = data['descricao']
        if 'preco_base' in data:
            servico.preco_base = float(data['preco_base'])
        if 'duracao_minutos' in data:
            servico.duracao_minutos = int(data['duracao_minutos'])
        if 'ativo' in data:
            servico.ativo = bool(data['ativo'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Serviço atualizado com sucesso',
            'servico': servico.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Deletar serviço (apenas admin - soft delete)
@servicos_bp.route('/<int:servico_id>', methods=['DELETE'])
@jwt_required()
def deletar_servico(servico_id):
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso negado. Apenas administradores.', 403)
        
        servico = Servico.query.get_or_404(servico_id)
        servico.ativo = False
        
        db.session.commit()
        
        return jsonify({
            'message': 'Serviço desativado com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)