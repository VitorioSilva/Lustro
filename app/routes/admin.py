from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import HorarioFuncionamento, Configuracao, User
from app.utils.security import error_response
from datetime import time

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/horarios-funcionamento', methods=['GET', 'PUT'])
@jwt_required()
def gerenciar_horarios_funcionamento():
    try:
        # Verificar se é admin
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
            
        if request.method == 'GET':
            horarios = HorarioFuncionamento.query.order_by(HorarioFuncionamento.dia_semana.asc()).all()
            return jsonify({
                'horarios': [h.to_dict() for h in horarios]
            }), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            for dia_data in data:
                horario = HorarioFuncionamento.query.filter_by(dia_semana=dia_data['dia_semana']).first()
                if horario:
                    horario.aberto = dia_data['aberto']
                    if dia_data['aberto']:
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
        # Verificar se é admin
        current_user = User.query.get(int(get_jwt_identity()))
        if not current_user.is_admin:
            return error_response('Acesso não autorizado', 403)
            
        if request.method == 'GET':
            configuracoes = Configuracao.query.all()
            return jsonify({
                'configuracoes': [c.to_dict() for c in configuracoes]
            }), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            for config_data in data:
                config = Configuracao.query.filter_by(chave=config_data['chave']).first()
                if config:
                    config.valor = config_data['valor']
            
            db.session.commit()
            return jsonify({'message': 'Configurações atualizadas com sucesso'}), 200
            
    except Exception as e:
        db.session.rollback()
        return error_response(f'Erro interno do servidor: {str(e)}', 500)