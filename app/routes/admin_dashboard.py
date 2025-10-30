from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Agendamento, User, Veiculo, Servico, HorarioFuncionamento, Administrador
from datetime import datetime, date, timedelta
from app.utils.security import error_response
from app.routes.modelos_veiculo import ModeloVeiculo

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)

def is_admin(user_id):
    """Verifica se o usuário é admin"""
    user = User.query.get(user_id)
    if user and hasattr(user, 'is_admin') and user.is_admin:
        return True
    admin = Administrador.query.get(user_id)
    return admin is not None

@admin_dashboard_bp.route('/agendamentos-hoje', methods=['GET'])
@jwt_required()
def agendamentos_hoje():
    try:
        current_user_id = get_jwt_identity()
        if not is_admin(current_user_id):
            return error_response('Acesso não autorizado', 403)

        hoje = date.today()
        agendamentos = Agendamento.query.filter(
            Agendamento.data_agendamento == hoje
        ).order_by(Agendamento.horario_agendamento.asc()).all()

        agendamentos_enriquecidos = []
        for ag in agendamentos:
            ag_dict = ag.to_dict()
            usuario = User.query.get(ag.user_id)
            veiculo = Veiculo.query.get(ag.veiculo_id)
            servico = Servico.query.get(ag.servico_id)

            ag_dict.update({
                'cliente_nome': usuario.nome if usuario else 'N/A',
                'cliente_telefone': usuario.telefone if usuario else 'N/A',
                'veiculo_placa': veiculo.placa if veiculo else 'N/A',
                'modelo_veiculo_nome': veiculo.modelo.nome if veiculo and veiculo.modelo else 'N/A',
                'nome_proprietario': veiculo.nome_proprietario if veiculo else 'N/A',
                'servico_nome': servico.nome if servico else 'N/A',
                'servico_duracao': servico.duracao_minutos if servico else 0
            })
            agendamentos_enriquecidos.append(ag_dict)

        return jsonify({'agendamentos': agendamentos_enriquecidos}), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@admin_dashboard_bp.route('/agendamentos/<int:agendamento_id>/concluir', methods=['PUT'])
@jwt_required()
def concluir_agendamento(agendamento_id):
    try:
        current_user_id = get_jwt_identity()
        if not is_admin(current_user_id):
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

@admin_dashboard_bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def estatisticas_admin():
    try:
        current_user_id = get_jwt_identity()
        if not is_admin(current_user_id):
            return error_response('Acesso não autorizado', 403)

        hoje = date.today()

        # Estatísticas
        agendamentos_hoje = Agendamento.query.filter(
            Agendamento.data_agendamento == hoje
        ).count()

        agendamentos_confirmados = Agendamento.query.filter(
            Agendamento.status == 'confirmado',
            Agendamento.data_agendamento >= hoje
        ).count()

        total_clientes = User.query.count()

        receita_hoje = db.session.query(db.func.sum(Agendamento.valor_total)).filter(
            Agendamento.data_agendamento == hoje,
            Agendamento.status == 'concluido'
        ).scalar() or 0

        concluidos_hoje = Agendamento.query.filter(
            Agendamento.data_agendamento == hoje,
            Agendamento.status == 'concluido'
        ).count()

        # Agendamentos da semana
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        agendamentos_semana = Agendamento.query.filter(
            Agendamento.data_agendamento >= inicio_semana,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).count()

        return jsonify({
            'agendamentos_hoje': agendamentos_hoje,
            'agendamentos_confirmados': agendamentos_confirmados,
            'agendamentos_semana': agendamentos_semana,
            'total_clientes': total_clientes,
            'receita_hoje': float(receita_hoje),
            'concluidos_hoje': concluidos_hoje,
            'data_consulta': hoje.isoformat()
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@admin_dashboard_bp.route('/agendamentos', methods=['GET'])
@jwt_required()
def listar_todos_agendamentos():
    try:
        current_user_id = get_jwt_identity()
        if not is_admin(current_user_id):
            return error_response('Acesso não autorizado', 403)

        # Filtros opcionais
        status = request.args.get('status')
        data = request.args.get('data')

        query = Agendamento.query

        if status:
            query = query.filter(Agendamento.status == status)

        if data:
            try:
                data_filtro = datetime.strptime(data, '%Y-%m-%d').date()
                query = query.filter(Agendamento.data_agendamento == data_filtro)
            except ValueError:
                return error_response('Formato de data inválido')

        agendamentos = query.order_by(
            Agendamento.data_agendamento.desc(),
            Agendamento.horario_agendamento.desc()
        ).limit(100).all()

        agendamentos_enriquecidos = []
        for ag in agendamentos:
            ag_dict = ag.to_dict()
            usuario = User.query.get(ag.user_id)
            veiculo = Veiculo.query.get(ag.veiculo_id)
            servico = Servico.query.get(ag.servico_id)
            
            # CORREÇÃO: Buscar modelo separadamente
            modelo_veiculo = ModeloVeiculo.query.get(veiculo.modelo_veiculo_id) if veiculo else None

            ag_dict.update({
                'cliente_nome': usuario.nome if usuario else 'N/A',
                'cliente_telefone': usuario.telefone if usuario else 'N/A',
                'veiculo_placa': veiculo.placa if veiculo else 'N/A',
                'modelo_veiculo_nome': modelo_veiculo.nome if modelo_veiculo else 'N/A',  # CORREÇÃO
                'nome_proprietario': veiculo.nome_proprietario if veiculo else 'N/A',
                'servico_nome': servico.nome if servico else 'N/A'
            })
            agendamentos_enriquecidos.append(ag_dict)

        return jsonify({
            'agendamentos': agendamentos_enriquecidos,
            'total': len(agendamentos_enriquecidos)
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)