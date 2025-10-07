from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Agendamento, User, Veiculo, Servico, HorarioFuncionamento
from datetime import datetime, date, timedelta
from app.utils.security import error_response

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)

@admin_dashboard_bp.route('/agendamentos-hoje', methods=['GET'])
@jwt_required()
def agendamentos_hoje():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        hoje = date.today()
        agendamentos = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status == 'confirmado'
        ).order_by(Agendamento.horario.asc()).all()
        
        # MELHORIA: Dados enriquecidos
        agendamentos_enriquecidos = []
        for ag in agendamentos:
            ag_dict = ag.to_dict()
            cliente = User.query.get(ag.user_id)
            veiculo = Veiculo.query.get(ag.veiculo_id)
            servico = Servico.query.get(ag.servico_id)
            
            ag_dict.update({
                'cliente_nome': cliente.nome if cliente else 'N/A',
                'cliente_telefone': cliente.telefone if cliente else 'N/A',
                'veiculo_placa': veiculo.placa if veiculo else 'N/A',
                'veiculo_modelo': f"{veiculo.marca} {veiculo.modelo}" if veiculo and veiculo.marca and veiculo.modelo else veiculo.tipo if veiculo else 'N/A',
                'servico_nome': servico.nome if servico else 'N/A',
                'servico_duracao': servico.duracao_minutos if servico else 0
            })
            agendamentos_enriquecidos.append(ag_dict)
        
        return jsonify({'agendamentos': agendamentos_enriquecidos}), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@admin_dashboard_bp.route('/agendamentos/buscar', methods=['GET'])
@jwt_required()
def buscar_agendamentos_placa():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        placa = request.args.get('placa', '').upper().replace('-', '').replace(' ', '')
        
        if not placa or len(placa) < 3:
            return error_response('Informe pelo menos 3 caracteres da placa')
        
        agendamentos = Agendamento.query.join(Veiculo).filter(
            Veiculo.placa.like(f'%{placa}%')
        ).order_by(Agendamento.data_agendamento.desc(), Agendamento.horario.desc()).limit(20).all()
        
        agendamentos_enriquecidos = []
        for ag in agendamentos:
            ag_dict = ag.to_dict()
            cliente = User.query.get(ag.user_id)
            veiculo = Veiculo.query.get(ag.veiculo_id)
            servico = Servico.query.get(ag.servico_id)
            
            ag_dict.update({
                'cliente_nome': cliente.nome if cliente else 'N/A',
                'cliente_telefone': cliente.telefone if cliente else 'N/A',
                'veiculo_placa': veiculo.placa if veiculo else 'N/A',
                'veiculo_modelo': f"{veiculo.marca} {veiculo.modelo}" if veiculo and veiculo.marca and veiculo.modelo else veiculo.tipo if veiculo else 'N/A',
                'servico_nome': servico.nome if servico else 'N/A'
            })
            agendamentos_enriquecidos.append(ag_dict)
        
        return jsonify({
            'agendamentos': agendamentos_enriquecidos,
            'total_encontrado': len(agendamentos_enriquecidos)
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

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

@admin_dashboard_bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def estatisticas_admin():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        hoje = date.today()
        
        # MELHORIA: Estatísticas mais completas
        agendamentos_hoje = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).count()
        
        agendamentos_confirmados = Agendamento.query.filter(
            Agendamento.status == 'confirmado',
            Agendamento.data_agendamento >= hoje
        ).count()
        
        total_clientes = User.query.filter_by(is_admin=False).count()
        
        receita_hoje = db.session.query(db.func.sum(Agendamento.valor_total)).filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).scalar() or 0
        
        concluidos_hoje = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status == 'concluido'
        ).count()
        
        # NOVA ESTATÍSTICA: Agendamentos da semana
        inicio_semana = hoje
        while inicio_semana.weekday() != 0:  # Segunda-feira
            inicio_semana = inicio_semana - timedelta(days=1)
        
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

# NOVA ROTA: Listar todos os agendamentos (admin)
@admin_dashboard_bp.route('/agendamentos', methods=['GET'])
@jwt_required()
def listar_todos_agendamentos():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
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
            Agendamento.horario.desc()
        ).all()
        
        agendamentos_enriquecidos = []
        for ag in agendamentos:
            ag_dict = ag.to_dict()
            cliente = User.query.get(ag.user_id)
            veiculo = Veiculo.query.get(ag.veiculo_id)
            servico = Servico.query.get(ag.servico_id)
            
            ag_dict.update({
                'cliente_nome': cliente.nome if cliente else 'N/A',
                'cliente_telefone': cliente.telefone if cliente else 'N/A',
                'veiculo_placa': veiculo.placa if veiculo else 'N/A',
                'servico_nome': servico.nome if servico else 'N/A'
            })
            agendamentos_enriquecidos.append(ag_dict)
        
        return jsonify({
            'agendamentos': agendamentos_enriquecidos,
            'total': len(agendamentos_enriquecidos)
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)