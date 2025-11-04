from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Agendamento, Servico, Veiculo, User, HorarioFuncionamento, ModeloVeiculo
from datetime import datetime, timedelta, date
from app.utils.security import error_response, validate_placa

agendamentos_bp = Blueprint('agendamentos', __name__)

def verificar_disponibilidade(data_agendamento, horario_agendamento, duracao_minutos):
    data_hora_agendamento = datetime.combine(data_agendamento, horario_agendamento)

    dia_semana = data_agendamento.weekday()
    horario_func = HorarioFuncionamento.query.filter_by(dia_semana=dia_semana).first()

    if not horario_func or not horario_func.aberto:
        return False

    # Verificar se está dentro do horário de funcionamento
    if horario_agendamento < horario_func.hora_abertura:
        return False

    hora_fim_servico = (datetime.combine(datetime.today(), horario_agendamento) + 
                       timedelta(minutes=duracao_minutos)).time()

    if hora_fim_servico > horario_func.hora_fechamento:
        return False

    # Verificar conflitos com outros agendamentos
    fim_agendamento = data_hora_agendamento + timedelta(minutes=duracao_minutos)

    agendamentos_do_dia = Agendamento.query.filter(
        Agendamento.data_agendamento == data_agendamento,
        Agendamento.status.in_(['pendente', 'confirmado'])
    ).all()

    for agendamento in agendamentos_do_dia:
        servico_existente = Servico.query.get(agendamento.servico_id)
        if servico_existente:
            inicio_existente = datetime.combine(data_agendamento, agendamento.horario_agendamento)
            fim_existente = inicio_existente + timedelta(minutes=servico_existente.duracao_minutos)

            # Verificar sobreposição
            if (data_hora_agendamento < fim_existente and fim_agendamento > inicio_existente):
                return False

    return True

@agendamentos_bp.route('', methods=['POST'])
@jwt_required()
def criar_agendamento():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        required_fields = ['data_agendamento', 'horario_agendamento', 'servico_id', 'placa', 'nome_proprietario', 'telefone', 'modelo_veiculo_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(f'Campo {field} é obrigatório')

        # Validar placa
        is_valid, message = validate_placa(data['placa'])
        if not is_valid:
            return error_response(message)

        servico = Servico.query.get(data['servico_id'])
        if not servico:
            return error_response('Serviço não encontrado', 404)

        # Converter data e horário
        try:
            data_agendamento = datetime.strptime(data['data_agendamento'], '%Y-%m-%d').date()
            horario_agendamento = datetime.strptime(data['horario_agendamento'], '%H:%M').time()
        except ValueError as e:
            return error_response(f'Formato de data/horário inválido: {str(e)}')

        # Verificar se é data futura
        data_hora_completa = datetime.combine(data_agendamento, horario_agendamento)
        if data_hora_completa <= datetime.now():
            return error_response('A data do agendamento deve ser futura', 400)

        # Verificar disponibilidade
        if not verificar_disponibilidade(data_agendamento, horario_agendamento, servico.duracao_minutos):
            return error_response('Horário indisponível', 409)

        # Encontrar ou criar veículo
        placa_limpa = data['placa'].upper().replace('-', '').replace(' ', '')
        veiculo = Veiculo.query.filter_by(placa=placa_limpa).first()

        if not veiculo:
            # Criar novo veículo
            veiculo = Veiculo(
                usuario_id=current_user_id,
                nome_proprietario=data['nome_proprietario'],
                placa=placa_limpa,
                modelo_veiculo_id=data['modelo_veiculo_id'],
                telefone=data['telefone']
            )
            db.session.add(veiculo)
            db.session.flush()  # Para obter o ID

        # Buscar o modelo do veículo separadamente (sem relacionamento)
        modelo_veiculo = ModeloVeiculo.query.get(veiculo.modelo_veiculo_id)

        # Criar agendamento com user_id
        novo_agendamento = Agendamento(
            data_agendamento=data_agendamento,
            horario_agendamento=horario_agendamento,
            valor_total=float(servico.preco),
            user_id=current_user_id,
            veiculo_id=veiculo.id,
            servico_id=servico.id,
            observacoes=data.get('observacoes'),
            status='confirmado'
        )

        db.session.add(novo_agendamento)
        db.session.commit()

        # Retornar dados completos
        agendamento_dict = novo_agendamento.to_dict()
        agendamento_dict.update({
            'servico_nome': servico.nome,
            'veiculo_placa': veiculo.placa,
            'modelo_veiculo_nome': modelo_veiculo.nome if modelo_veiculo else 'N/A',  # CORREÇÃO AQUI
            'nome_proprietario': veiculo.nome_proprietario
        })

        return jsonify({
            'message': 'Agendamento criado com sucesso',
            'agendamento': agendamento_dict
        }), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@agendamentos_bp.route('', methods=['GET'])
@jwt_required()
def listar_agendamentos():
    try:
        current_user_id = get_jwt_identity()
        
        # Verificar se é admin
        current_user = User.query.get(current_user_id)
        is_admin = current_user and hasattr(current_user, 'is_admin') and current_user.is_admin

        if is_admin:
            agendamentos = Agendamento.query.order_by(
                Agendamento.data_agendamento.desc(), 
                Agendamento.horario_agendamento.desc()
            ).all()
        else:
            # Filtrar por user_id do usuário logado
            agendamentos = Agendamento.query.filter_by(user_id=current_user_id).order_by(
                Agendamento.data_agendamento.desc(),
                Agendamento.horario_agendamento.desc()
            ).all()

        agendamentos_completos = []
        for ag in agendamentos:
            ag_dict = ag.to_dict()
            servico = Servico.query.get(ag.servico_id)
            veiculo = Veiculo.query.get(ag.veiculo_id)
            usuario = User.query.get(ag.user_id) if is_admin else None
            
            # Buscar modelo do veículo separadamente
            modelo_veiculo = ModeloVeiculo.query.get(veiculo.modelo_veiculo_id) if veiculo else None

            ag_dict.update({
                'servico_nome': servico.nome if servico else 'N/A',
                'veiculo_placa': veiculo.placa if veiculo else 'N/A',
                'modelo_veiculo_nome': modelo_veiculo.nome if modelo_veiculo else 'N/A',  # CORREÇÃO
                'nome_proprietario': veiculo.nome_proprietario if veiculo else 'N/A'
            })

            if is_admin and usuario:
                ag_dict['cliente_nome'] = usuario.nome
                ag_dict['cliente_telefone'] = usuario.telefone

            agendamentos_completos.append(ag_dict)

        return jsonify({
            'agendamentos': agendamentos_completos
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@agendamentos_bp.route('/<int:agendamento_id>', methods=['DELETE'])
@jwt_required()
def cancelar_agendamento(agendamento_id):
    try:
        current_user_id = get_jwt_identity()
        agendamento = Agendamento.query.get_or_404(agendamento_id)

        # CORREÇÃO: Verificação simplificada e funcional
        from app.models import Administrador
        
        # Verificar se é admin
        is_admin = Administrador.query.get(current_user_id) is not None
        
        # Se não é admin E não é dono do agendamento, bloqueia
        if not is_admin and agendamento.user_id != int(current_user_id):
            return error_response('Não autorizado', 403)

        if agendamento.status in ['cancelado', 'concluido']:
            return error_response('Agendamento já cancelado ou concluído', 400)

        agendamento.status = 'cancelado'
        db.session.commit()

        return jsonify({
            'message': 'Agendamento cancelado com sucesso'
        }), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@agendamentos_bp.route('/<int:agendamento_id>', methods=['GET'])
@jwt_required()
def detalhes_agendamento(agendamento_id):
    try:
        current_user_id = get_jwt_identity()
        agendamento = Agendamento.query.get_or_404(agendamento_id)

        # CORREÇÃO: Verificação simplificada e funcional
        from app.models import Administrador
        
        # Verificar se é admin
        is_admin = Administrador.query.get(current_user_id) is not None
        
        # Se não é admin E não é dono do agendamento, bloqueia
        if not is_admin and agendamento.user_id != int(current_user_id):
            return error_response('Não autorizado', 403)

        servico = Servico.query.get(agendamento.servico_id)
        veiculo = Veiculo.query.get(agendamento.veiculo_id)
        usuario = User.query.get(agendamento.user_id) if is_admin else None

        agendamento_dict = agendamento.to_dict()
        agendamento_dict.update({
            'servico': servico.to_dict() if servico else None,
            'veiculo': veiculo.to_dict() if veiculo else None,
            'cliente': usuario.to_dict() if usuario and is_admin else None
        })

        return jsonify({
            'agendamento': agendamento_dict
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)
    
@agendamentos_bp.route('/horarios-disponiveis', methods=['GET'])
@jwt_required()
def horarios_disponiveis():
    try:
        data_str = request.args.get('data')
        servico_id = request.args.get('servico_id')

        if not data_str or not servico_id:
            return error_response('Parâmetros data e servico_id são obrigatórios')

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return error_response('Formato de data inválido. Use YYYY-MM-DD')

        if data < datetime.now().date():
            return jsonify({'horarios_disponiveis': []})

        servico = Servico.query.get(servico_id)
        if not servico:
            return error_response('Serviço não encontrado')

        dia_semana = data.weekday()
        horario_func = HorarioFuncionamento.query.filter_by(dia_semana=dia_semana).first()

        if not horario_func or not horario_func.aberto:
            return jsonify({'horarios_disponiveis': []})

        intervalo = 30
        horarios_disponiveis = []

        hora_atual = horario_func.hora_abertura
        while hora_atual < horario_func.hora_fechamento:
            if verificar_disponibilidade(data, hora_atual, servico.duracao_minutos):
                horarios_disponiveis.append(hora_atual.strftime('%H:%M'))

            # Avançar para o próximo horário
            hora_atual = (datetime.combine(datetime.today(), hora_atual) + 
                         timedelta(minutes=intervalo)).time()

        return jsonify({
            'horarios_disponiveis': horarios_disponiveis
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@agendamentos_bp.route('/expirados', methods=['DELETE'])
@jwt_required()
def remover_agendamentos_expirados():
    try:
        current_user_id = get_jwt_identity()
        
        # CORREÇÃO: Verificação de admin correta
        from app.models import Administrador
        is_admin = Administrador.query.get(current_user_id) is not None
        
        if not is_admin:
            return error_response('Acesso não autorizado', 403)

        hoje = date.today()
        
        # Marcar agendamentos passados como expirados
        agendamentos_expirados = Agendamento.query.filter(
            Agendamento.data_agendamento < hoje,
            Agendamento.status.in_(['pendente', 'confirmado'])
        ).all()

        for agendamento in agendamentos_expirados:
            agendamento.status = 'expirado'

        db.session.commit()

        return jsonify({
            'message': f'{len(agendamentos_expirados)} agendamentos marcados como expirados',
            'expirados_count': len(agendamentos_expirados)
        }), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@agendamentos_bp.route('/<int:agendamento_id>/status', methods=['PUT'])
@jwt_required()
def atualizar_status_agendamento(agendamento_id):
    try:
        current_user_id = get_jwt_identity()
        agendamento = Agendamento.query.get_or_404(agendamento_id)

        # CORREÇÃO: Verificação de admin correta
        from app.models import Administrador
        is_admin = Administrador.query.get(current_user_id) is not None
        
        if not is_admin:
            return error_response('Acesso não autorizado', 403)

        data = request.get_json()
        novo_status = data.get('status')

        if novo_status not in ['pendente', 'confirmado', 'concluido', 'cancelado', 'expirado']:
            return error_response('Status inválido')

        agendamento.status = novo_status
        db.session.commit()

        return jsonify({
            'message': f'Status do agendamento atualizado para {novo_status}',
            'agendamento': agendamento.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@agendamentos_bp.route('/hoje', methods=['GET'])
@jwt_required()
def agendamentos_hoje():
    try:
        current_user_id = get_jwt_identity()
        
        # Apenas admin pode ver agendamentos do dia
        current_user = User.query.get(current_user_id)
        if not current_user or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)

        hoje = date.today()
        agendamentos = Agendamento.query.filter(
            Agendamento.data_agendamento == hoje,
            Agendamento.status.in_(['confirmado', 'pendente'])
        ).order_by(Agendamento.horario_agendamento.asc()).all()

        agendamentos_completos = []
        for ag in agendamentos:
            ag_dict = ag.to_dict()
            servico = Servico.query.get(ag.servico_id)
            veiculo = Veiculo.query.get(ag.veiculo_id)
            usuario = User.query.get(ag.user_id)
            
            # Buscar modelo do veículo separadamente
            modelo_veiculo = ModeloVeiculo.query.get(veiculo.modelo_veiculo_id) if veiculo else None

            ag_dict.update({
                'servico_nome': servico.nome if servico else 'N/A',
                'veiculo_placa': veiculo.placa if veiculo else 'N/A',
                'modelo_veiculo_nome': modelo_veiculo.nome if modelo_veiculo else 'N/A',  # CORREÇÃO
                'nome_proprietario': veiculo.nome_proprietario if veiculo else 'N/A',
                'cliente_nome': usuario.nome if usuario else 'N/A',
                'cliente_telefone': usuario.telefone if usuario else 'N/A'
            })
            agendamentos_completos.append(ag_dict)

        return jsonify({
            'agendamentos': agendamentos_completos
        }), 200

    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)