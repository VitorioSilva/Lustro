from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import HorarioFuncionamento, Configuracao, User
from app.utils.security import error_response
from datetime import time

admin_bp = Blueprint('admin', __name__)

def inicializar_horarios_padrao():
    # Inicializa horários padrão se a tabela estiver vazia
    if HorarioFuncionamento.query.count() == 0:
        horarios_padrao = [
            (0, True, time(8, 0), time(18, 0)),  # Segunda
            (1, True, time(8, 0), time(18, 0)),  # Terça
            (2, True, time(8, 0), time(18, 0)),  # Quarta
            (3, True, time(8, 0), time(18, 0)),  # Quinta
            (4, True, time(8, 0), time(18, 0)),  # Sexta
            (5, True, time(8, 0), time(16, 0)),  # Sábado
            (6, False, time(8, 0), time(18, 0))  # Domingo
        ]
        
        for dia, aberto, abertura, fechamento in horarios_padrao:
            horario = HorarioFuncionamento(
                dia_semana=dia,
                aberto=aberto,
                hora_abertura=abertura,
                hora_fechamento=fechamento
            )
            db.session.add(horario)
        
        db.session.commit()
        return True
    return False

def inicializar_configuracoes_padrao():
    # Inicializa configurações padrão
    if Configuracao.query.count() == 0:
        configs_padrao = [
            ('tempo_minimo_cancelamento', '24', 'Horas mínimas para cancelamento sem multa'),
            ('multa_cancelamento', '20', 'Percentual de multa por cancelamento tardio'),
            ('intervalo_agendamento', '30', 'Intervalo entre agendamentos em minutos')
        ]
        
        for chave, valor, descricao in configs_padrao:
            config = Configuracao(
                chave=chave,
                valor=valor,
                descricao=descricao
            )
            db.session.add(config)
        
        db.session.commit()
        return True
    return False

def validar_horario_funcionamento(hora_abertura, hora_fechamento, aberto):
    if not aberto:
        return True, "Dia fechado"
    
    if hora_abertura >= hora_fechamento:
        return False, "Horário de abertura deve ser anterior ao fechamento"
    
    if hora_abertura < time(0, 0) or hora_fechamento > time(23, 59):
        return False, "Horários devem estar entre 00:00 e 23:59"
    
    return True, "Horário válido"

@admin_bp.route('/horarios-funcionamento', methods=['GET', 'PUT'])
@jwt_required()
def gerenciar_horarios_funcionamento():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        # Inicializar horários se necessário
        if HorarioFuncionamento.query.count() == 0:
            inicializar_horarios_padrao()
            
        if request.method == 'GET':
            horarios = HorarioFuncionamento.query.order_by(HorarioFuncionamento.dia_semana.asc()).all()
            return jsonify({'horarios': [h.to_dict() for h in horarios]}), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            for dia_data in data:
                horario = HorarioFuncionamento.query.filter_by(dia_semana=dia_data['dia_semana']).first()
                
                if not horario:
                    horario = HorarioFuncionamento(dia_semana=dia_data['dia_semana'])
                    db.session.add(horario)
                
                # Validar horários
                if dia_data.get('aberto', False):
                    hora_abertura = time.fromisoformat(dia_data['hora_abertura'])
                    hora_fechamento = time.fromisoformat(dia_data['hora_fechamento'])
                    
                    is_valid, message = validar_horario_funcionamento(
                        hora_abertura, hora_fechamento, dia_data['aberto']
                    )
                    if not is_valid:
                        return error_response(f'Dia {dia_data["dia_semana"]}: {message}')
                
                horario.aberto = dia_data.get('aberto', False)
                if horario.aberto:
                    horario.hora_abertura = time.fromisoformat(dia_data['hora_abertura'])
                    horario.hora_fechamento = time.fromisoformat(dia_data['hora_fechamento'])
            
            db.session.commit()
            return jsonify({'message': 'Horários atualizados com sucesso'}), 200
            
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)

@admin_bp.route('/configuracoes', methods=['GET', 'PUT'])
@jwt_required()
def gerenciar_configuracoes():
    try:
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
        
        # Inicializar configurações se necessário
        if Configuracao.query.count() == 0:
            inicializar_configuracoes_padrao()
            
        if request.method == 'GET':
            configuracoes = Configuracao.query.all()
            return jsonify({'configuracoes': [c.to_dict() for c in configuracoes]}), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            for config_data in data:
                config = Configuracao.query.filter_by(chave=config_data['chave']).first()
                
                if not config:
                    config = Configuracao(
                        chave=config_data['chave'],
                        valor=config_data['valor'],
                        descricao=config_data.get('descricao', '')
                    )
                    db.session.add(config)
                else:
                    config.valor = config_data['valor']
                    if 'descricao' in config_data:
                        config.descricao = config_data['descricao']
            
            db.session.commit()
            return jsonify({'message': 'Configurações atualizadas com sucesso'}), 200
            
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)