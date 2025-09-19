from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Agendamento, Servico, Veiculo, User, HorarioFuncionamento, Configuracao
from datetime import datetime, timedelta
from app.utils.security import error_response

agendamentos_bp = Blueprint('agendamentos', __name__)

# Função auxiliar para verificar disponibilidade
def verificar_disponibilidade(data_agendamento, duracao_minutos):
    # Verificar se está dentro do horário de funcionamento
    dia_semana = data_agendamento.weekday()
    horario_func = HorarioFuncionamento.query.filter_by(dia_semana=dia_semana).first()
    
    if not horario_func or not horario_func.aberto:
        return False
    
    hora_agendamento = data_agendamento.time()
    if hora_agendamento < horario_func.hora_abertura or hora_agendamento > horario_func.hora_fechamento:
        return False
    
    # Verificar conflitos com outros agendamentos
    fim_agendamento = data_agendamento + timedelta(minutes=duracao_minutos)
    
    # Buscar todos os agendamentos confirmados com seus serviços
    agendamentos = db.session.query(Agendamento, Servico).join(Servico).filter(
        Agendamento.status == 'confirmado'
    ).all()
    
    for agendamento, servico in agendamentos:
        fim_existente = agendamento.data_agendamento + timedelta(minutes=servico.duracao_minutos)
        
        # Verificar se há sobreposição
        if (data_agendamento < fim_existente and fim_agendamento > agendamento.data_agendamento):
            return False
    
    return True

# Função auxiliar para calcular valor com adicional por tipo de veículo
def calcular_valor_servico(preco_base, tipo_veiculo):
    # Definir multiplicadores por tipo de veículo
    multiplicadores = {
        'hatch': 1.0,
        'sedan': 1.1,
        'suv': 1.2,
        'caminhonete': 1.3,
        'van': 1.4
    }
    
    multiplicador = multiplicadores.get(tipo_veiculo.lower(), 1.0)
    return round(preco_base * multiplicador, 2)

# Criar agendamento
@agendamentos_bp.route('', methods=['POST'])
@jwt_required()
def criar_agendamento():
    try:
        # Obter usuário atual
        current_user = User.query.get(int(get_jwt_identity()))
        user_id = current_user.id

        data = request.get_json()

        # Validar campos obrigatórios
        required_fields = ['data_agendamento', 'servico_id', 'placa_veiculo', 'telefone']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(f'Campo {field} é obrigatório')

        # Verificar se serviço existe
        servico = Servico.query.get(data['servico_id'])
        if not servico:
            return error_response('Serviço não encontrado', 404)

        # Buscar ou criar veículo
        veiculo = current_user.get_veiculo_by_placa(data['placa_veiculo'])
        if not veiculo:
            # Criar novo veículo se não existir
            if 'tipo_veiculo' not in data:
                return error_response('Tipo do veículo é obrigatório para novo veículo')
            
            veiculo = Veiculo(
                placa=data['placa_veiculo'],
                tipo=data['tipo_veiculo'],
                user_id=user_id,
                marca=data.get('marca'),
                modelo=data.get('modelo'),
                cor=data.get('cor')
            )
            db.session.add(veiculo)
            db.session.flush()  # Para obter o ID sem commit

        # Converter string para datetime (remover timezone se existir)
        try:
            data_agendamento = datetime.fromisoformat(data['data_agendamento'].replace('Z', '+00:00'))
            # Remover informação de timezone para evitar conflitos
            data_agendamento = data_agendamento.replace(tzinfo=None)
        except ValueError:
            return error_response('Formato de data inválido. Use ISO format (ex: 2025-01-01T10:00:00Z)')

        # Verificar se a data é futura (ambos naive para comparação)
        if data_agendamento <= datetime.now():
            return error_response('A data do agendamento deve ser futura', 400)

        # Verificar disponibilidade
        if not verificar_disponibilidade(data_agendamento, servico.duracao_minutos):
            return error_response('Horário indisponível', 409)

        # Calcular valor total
        valor_total = calcular_valor_servico(servico.preco_base, veiculo.tipo)

        # Criar agendamento
        novo_agendamento = Agendamento(
            data_agendamento=data_agendamento,
            valor_total=valor_total,
            user_id=user_id,
            veiculo_id=veiculo.id,
            servico_id=servico.id,
            observacoes=data.get('observacoes')
        )

        # Atualizar telefone do usuário se fornecido
        if data['telefone']:
            current_user.telefone = data['telefone']

        db.session.add(novo_agendamento)
        db.session.commit()

        return jsonify({
            'message': 'Agendamento criado com sucesso',
            'agendamento': novo_agendamento.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Listar agendamentos do usuário
@agendamentos_bp.route('', methods=['GET'])
@jwt_required()
def listar_agendamentos():
    try:
        # Obter usuário atual
        current_user = User.query.get(int(get_jwt_identity()))
        user_id = current_user.id
        is_admin = current_user.is_admin
        
        # Admin vê todos os agendamentos, usuário vê apenas os seus
        if is_admin:
            agendamentos = Agendamento.query.order_by(Agendamento.data_agendamento.asc()).all()
        else:
            agendamentos = Agendamento.query.filter_by(user_id=user_id).order_by(Agendamento.data_agendamento.asc()).all()
        
        return jsonify({
            'agendamentos': [ag.to_dict() for ag in agendamentos]
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Cancelar agendamento
@agendamentos_bp.route('/<int:agendamento_id>', methods=['DELETE'])
@jwt_required()
def cancelar_agendamento(agendamento_id):
    try:
        # Obter usuário atual
        current_user = User.query.get(int(get_jwt_identity()))
        user_id = current_user.id
        is_admin = current_user.is_admin
        
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        
        # Verificar permissões
        if not is_admin and agendamento.user_id != user_id:
            return error_response('Não autorizado', 403)
        
        # Verificar se já está cancelado
        if agendamento.status == 'cancelado':
            return error_response('Agendamento já cancelado', 400)
        
        # Calcular multa se necessário
        multa = 0
        tempo_minimo = Configuracao.query.filter_by(chave='tempo_minimo_cancelamento').first()
        multa_percentual = Configuracao.query.filter_by(chave='multa_cancelamento').first()
        
        if tempo_minimo and multa_percentual:
            # Usar datetime naive para comparação
            horas_antecedencia = (agendamento.data_agendamento - datetime.now()).total_seconds() / 3600
            if horas_antecedencia < int(tempo_minimo.valor):
                multa = agendamento.valor_total * (int(multa_percentual.valor) / 100)
        
        # Cancelar agendamento
        agendamento.status = 'cancelado'
        db.session.commit()
        
        return jsonify({
            'message': 'Agendamento cancelado com sucesso',
            'multa_aplicada': round(multa, 2) if multa > 0 else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

# Obter horários disponíveis
@agendamentos_bp.route('/horarios-disponiveis', methods=['GET'])
@jwt_required()
def horarios_disponiveis():
    try:
        # Obter usuário atual
        current_user = User.query.get(int(get_jwt_identity()))
        
        data_str = request.args.get('data')
        servico_id = request.args.get('servico_id')
        
        if not data_str or not servico_id:
            return error_response('Parâmetros data e servico_id são obrigatórios')
        
        # Converter data
        try:
            data = datetime.fromisoformat(data_str).date()
        except ValueError:
            return error_response('Formato de data inválido. Use YYYY-MM-DD')
        
        # Verificar serviço
        servico = Servico.query.get(servico_id)
        if not servico:
            return error_response('Serviço não encontrado')
        
        # Verificar dia de funcionamento
        dia_semana = data.weekday()
        horario_func = HorarioFuncionamento.query.filter_by(dia_semana=dia_semana).first()
        
        if not horario_func or not horario_func.aberto:
            return jsonify({'horarios_disponiveis': []})
        
        # Gerar todos os horários possíveis
        intervalo = int(Configuracao.query.filter_by(chave='intervalo_agendamento').first().valor or 30)
        horarios_disponiveis = []
        
        hora_atual = horario_func.hora_abertura
        while hora_atual < horario_func.hora_fechamento:
            # Calcular fim do serviço
            hora_fim = (datetime.combine(datetime.today(), hora_atual) + 
                       timedelta(minutes=servico.duracao_minutos)).time()
            
            # Verificar se cabe no horário de funcionamento
            if hora_fim <= horario_func.hora_fechamento:
                # Verificar disponibilidade
                data_hora_agendamento = datetime.combine(data, hora_atual)
                if verificar_disponibilidade(data_hora_agendamento, servico.duracao_minutos):
                    horarios_disponiveis.append(hora_atual.strftime('%H:%M'))
            
            # Próximo horário
            hora_atual = (datetime.combine(datetime.today(), hora_atual) + 
                         timedelta(minutes=intervalo)).time()
        
        return jsonify({
            'horarios_disponiveis': horarios_disponiveis
        }), 200
        
    except Exception as e:
        return error_response(f'Erro interno do servidor: {str(e)}', 500)