from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Agendamento, Servico, Veiculo, User, HorarioFuncionamento, Configuracao
from datetime import datetime, timedelta, time, date
from app.utils.security import error_response, validate_placa

agendamentos_bp = Blueprint('agendamentos', __name__)

def calcular_valor_servico(preco_base, tipo_veiculo):
    multiplicadores = {
        'hatch': 1.0,
        'sedan': 1.1,
        'suv': 1.2,
        'caminhonete': 1.3,
        'van': 1.4
    }
    
    multiplicador = multiplicadores.get(tipo_veiculo.lower(), 1.0)
    return round(preco_base * multiplicador, 2)

def verificar_disponibilidade(data_agendamento, horario_agendamento, duracao_minutos):
    # CORREÇÃO: Usar datetime combinado corretamente
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
        Agendamento.status == 'confirmado'
    ).all()
    
    for agendamento in agendamentos_do_dia:
        servico_existente = Servico.query.get(agendamento.servico_id)
        if servico_existente:
            inicio_existente = datetime.combine(data_agendamento, agendamento.horario)
            fim_existente = inicio_existente + timedelta(minutes=servico_existente.duracao_minutos)
            
            # Verificar sobreposição
            if (data_hora_agendamento < fim_existente and fim_agendamento > inicio_existente):
                return False
    
    return True

@agendamentos_bp.route('', methods=['POST'])
@jwt_required()
def criar_agendamento():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        user_id = current_user.id

        data = request.get_json()

        required_fields = ['data_agendamento', 'horario', 'servico_id', 'placa_veiculo', 'telefone']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(f'Campo {field} é obrigatório')

        # CORREÇÃO: Validar placa
        is_valid, message = validate_placa(data['placa_veiculo'])
        if not is_valid:
            return error_response(message)

        servico = Servico.query.get(data['servico_id'])
        if not servico:
            return error_response('Serviço não encontrado', 404)

        placa_limpa = data['placa_veiculo'].upper().replace('-', '').replace(' ', '')
        veiculo = Veiculo.query.filter_by(placa=placa_limpa, user_id=user_id).first()
        
        if not veiculo:
            return error_response('Veículo não encontrado. Cadastre o veículo primeiro.', 404)

        # Converter data e horário
        try:
            data_agendamento = datetime.strptime(data['data_agendamento'], '%Y-%m-%d').date()
            horario_agendamento = datetime.strptime(data['horario'], '%H:%M').time()
        except ValueError as e:
            return error_response(f'Formato de data/horário inválido: {str(e)}')

        # CORREÇÃO: Usar datetime combinado para verificação
        data_hora_completa = datetime.combine(data_agendamento, horario_agendamento)
        if data_hora_completa <= datetime.now():
            return error_response('A data do agendamento deve ser futura', 400)

        if not verificar_disponibilidade(data_agendamento, horario_agendamento, servico.duracao_minutos):
            return error_response('Horário indisponível', 409)

        valor_total = calcular_valor_servico(servico.preco_base, veiculo.tipo)

        if data['telefone']:
            current_user.telefone = data['telefone']

        novo_agendamento = Agendamento(
            data_agendamento=data_agendamento,
            horario=horario_agendamento,
            valor_total=valor_total,
            user_id=user_id,
            veiculo_id=veiculo.id,
            servico_id=servico.id,
            observacoes=data.get('observacoes')
        )

        db.session.add(novo_agendamento)
        db.session.commit()

        return jsonify({
            'message': 'Agendamento criado com sucesso',
            'agendamento': novo_agendamento.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# NOVA ROTA: Detalhes do agendamento
@agendamentos_bp.route('/<int:agendamento_id>', methods=['GET'])
@jwt_required()
def detalhes_agendamento(agendamento_id):
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        
        if not current_user.is_admin and agendamento.user_id != current_user.id:
            return error_response('Não autorizado', 403)
        
        servico = Servico.query.get(agendamento.servico_id)
        veiculo = Veiculo.query.get(agendamento.veiculo_id)
        cliente = User.query.get(agendamento.user_id)
        
        agendamento_dict = agendamento.to_dict()
        agendamento_dict.update({
            'servico': servico.to_dict() if servico else None,
            'veiculo': veiculo.to_dict() if veiculo else None,
            'cliente': cliente.to_dict() if not current_user.is_admin else cliente.to_dict()
        })
        
        return jsonify({
            'agendamento': agendamento_dict
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@agendamentos_bp.route('', methods=['GET'])
@jwt_required()
def listar_agendamentos():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        user_id = current_user.id
        is_admin = current_user.is_admin
        
        if is_admin:
            agendamentos = Agendamento.query.order_by(
                Agendamento.data_agendamento.asc(), 
                Agendamento.horario.asc()
            ).all()
        else:
            agendamentos = Agendamento.query.filter_by(user_id=user_id).order_by(
                Agendamento.data_agendamento.asc(),
                Agendamento.horario.asc()
            ).all()
        
        return jsonify({
            'agendamentos': [ag.to_dict() for ag in agendamentos]
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@agendamentos_bp.route('/<int:agendamento_id>', methods=['DELETE'])
@jwt_required()
def cancelar_agendamento(agendamento_id):
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        user_id = current_user.id
        is_admin = current_user.is_admin
        
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        
        if not is_admin and agendamento.user_id != user_id:
            return error_response('Não autorizado', 403)
        
        if agendamento.status == 'cancelado':
            return error_response('Agendamento já cancelado', 400)
        
        multa = 0
        tempo_minimo = Configuracao.query.filter_by(chave='tempo_minimo_cancelamento').first()
        multa_percentual = Configuracao.query.filter_by(chave='multa_cancelamento').first()
        
        if tempo_minimo and multa_percentual:
            # CORREÇÃO: Usar datetime combinado
            data_hora_agendamento = datetime.combine(agendamento.data_agendamento, agendamento.horario)
            horas_antecedencia = (data_hora_agendamento - datetime.now()).total_seconds() / 3600
            
            if horas_antecedencia < int(tempo_minimo.valor):
                multa = agendamento.valor_total * (int(multa_percentual.valor) / 100)
        
        agendamento.status = 'cancelado'
        db.session.commit()
        
        return jsonify({
            'message': 'Agendamento cancelado com sucesso',
            'multa_aplicada': round(multa, 2) if multa > 0 else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
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
            # CORREÇÃO: Verificar disponibilidade corretamente
            if verificar_disponibilidade(data, hora_atual, servico.duracao_minutos):
                horarios_disponiveis.append(hora_atual.strftime('%H:%M'))
            
            hora_atual = (datetime.combine(datetime.today(), hora_atual) + 
                         timedelta(minutes=intervalo)).time()
        
        return jsonify({
            'horarios_disponiveis': horarios_disponiveis
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)