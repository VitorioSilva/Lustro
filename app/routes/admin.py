from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import HorarioFuncionamento, User, Administrador
from app.utils.security import error_response
from datetime import time

admin_bp = Blueprint('admin', __name__)

def is_admin(user_id):
    """Verifica se o usuário é admin"""
    # Primeiro tenta encontrar como User (se tiver campo is_admin)
    user = User.query.get(user_id)
    if user and hasattr(user, 'is_admin') and user.is_admin:
        return True
    
    # Se não, verifica se é Administrador
    admin = Administrador.query.get(user_id)
    return admin is not None

@admin_bp.route('/horarios-funcionamento', methods=['GET', 'PUT'])
@jwt_required()
def gerenciar_horarios_funcionamento():
    try:
        current_user_id = get_jwt_identity()
        
        if not is_admin(current_user_id):
            return error_response('Acesso não autorizado', 403)

        if request.method == 'GET':
            horarios = HorarioFuncionamento.query.order_by(HorarioFuncionamento.dia_semana.asc()).all()
            return jsonify({'horarios': [h.to_dict() for h in horarios]}), 200

        elif request.method == 'PUT':
            data = request.get_json()

            if not isinstance(data, list):
                return error_response('Dados devem ser uma lista de horários')

            for dia_data in data:
                horario = HorarioFuncionamento.query.filter_by(dia_semana=dia_data['dia_semana']).first()

                if not horario:
                    horario = HorarioFuncionamento(dia_semana=dia_data['dia_semana'])
                    db.session.add(horario)

                horario.aberto = dia_data.get('aberto', False)
                
                if horario.aberto:
                    if not dia_data.get('hora_abertura') or not dia_data.get('hora_fechamento'):
                        return error_response(f'Horários são obrigatórios para dia {dia_data["dia_semana"]} quando aberto')
                    
                    hora_abertura = time.fromisoformat(dia_data['hora_abertura'])
                    hora_fechamento = time.fromisoformat(dia_data['hora_fechamento'])

                    if hora_abertura >= hora_fechamento:
                        return error_response(f'Horário de abertura deve ser anterior ao fechamento no dia {dia_data["dia_semana"]}')

                    horario.hora_abertura = hora_abertura
                    horario.hora_fechamento = hora_fechamento
                else:
                    horario.hora_abertura = None
                    horario.hora_fechamento = None

            db.session.commit()
            
            # Retornar horários atualizados
            horarios = HorarioFuncionamento.query.order_by(HorarioFuncionamento.dia_semana.asc()).all()
            return jsonify({
                'message': 'Horários atualizados com sucesso',
                'horarios': [h.to_dict() for h in horarios]
            }), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@admin_bp.route('/agendamentos/buscar', methods=['GET'])
@jwt_required()
def buscar_agendamentos_placa():
    try:
        current_user_id = get_jwt_identity()
        
        if not is_admin(current_user_id):
            return error_response('Acesso não autorizado', 403)

        placa = request.args.get('placa', '').upper().replace('-', '').replace(' ', '')

        if not placa or len(placa) < 3:
            return error_response('Informe pelo menos 3 caracteres da placa')

        from app.models import Agendamento, Veiculo, Servico, User, ModeloVeiculo

        agendamentos = Agendamento.query.join(Veiculo).filter(
            Veiculo.placa.like(f'%{placa}%')
        ).order_by(Agendamento.data_agendamento.desc(), Agendamento.horario_agendamento.desc()).limit(50).all()

        agendamentos_enriquecidos = []
        for ag in agendamentos:
            ag_dict = ag.to_dict()
            veiculo = Veiculo.query.get(ag.veiculo_id)
            servico = Servico.query.get(ag.servico_id)
            usuario = User.query.get(ag.user_id)
            
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
            'total_encontrado': len(agendamentos_enriquecidos)
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)