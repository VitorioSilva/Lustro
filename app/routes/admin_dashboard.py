from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Agendamento, User, Veiculo, Servico, HorarioFuncionamento
from datetime import datetime, date
from app.utils.security import error_response

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)

# Agendamentos de hoje para admin
@admin_dashboard_bp.route('/agendamentos-hoje', methods=['GET'])
@jwt_required()
def agendamentos_hoje():
    try:
        # Verificar se é admin
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        hoje = date.today()
        agendamentos = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status == 'confirmado'
        ).order_by(Agendamento.data_agendamento.asc()).all()
        
        return jsonify({
            'agendamentos': [ag.to_dict() for ag in agendamentos]
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Buscar agendamentos por placa
@admin_dashboard_bp.route('/agendamentos/buscar', methods=['GET'])
@jwt_required()
def buscar_agendamentos_placa():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        placa = request.args.get('placa', '').upper()
        
        if not placa:
            return error_response('Placa é obrigatória para busca')
        
        agendamentos = Agendamento.query.join(Veiculo).filter(
            Veiculo.placa.like(f'%{placa}%')
        ).order_by(Agendamento.data_agendamento.desc()).all()
        
        return jsonify({
            'agendamentos': [ag.to_dict() for ag in agendamentos]
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Marcar agendamento como concluído
@admin_dashboard_bp.route('/agendamentos/<int:agendamento_id>/concluir', methods=['PUT'])
@jwt_required()
def concluir_agendamento(agendamento_id):
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        
        if agendamento.status == 'concluido':
            return error_response('Agendamento já concluído', 400)
        
        agendamento.status = 'concluido'
        db.session.commit()
        
        return jsonify({
            'message': 'Agendamento marcado como concluído com sucesso',
            'agendamento': agendamento.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Estatísticas para dashboard admin
@admin_dashboard_bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def estatisticas_admin():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        hoje = date.today()
        
        # Agendamentos de hoje
        agendamentos_hoje = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje
        ).count()
        
        # Agendamentos confirmados
        agendamentos_confirmados = Agendamento.query.filter_by(status='confirmado').count()
        
        # Total de clientes
        total_clientes = User.query.filter_by(is_admin=False).count()
        
        # Receita total do dia
        receita_hoje = db.session.query(db.func.sum(Agendamento.valor_total)).filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).scalar() or 0
        
        return jsonify({
            'agendamentos_hoje': agendamentos_hoje,
            'agendamentos_confirmados': agendamentos_confirmados,
            'total_clientes': total_clientes,
            'receita_hoje': float(receita_hoje)
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)