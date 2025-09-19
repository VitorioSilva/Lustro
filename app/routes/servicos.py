from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Servico, User

servicos_bp = Blueprint('servicos', __name__)

@servicos_bp.route('', methods=['GET'])
@jwt_required()
def listar_servicos():
    try:
        # Obter usuário atual (apenas para verificar autenticação)
        current_user = User.query.get(int(get_jwt_identity()))
        
        servicos = Servico.query.filter_by(ativo=True).all()
        return jsonify({
            'servicos': [s.to_dict() for s in servicos]
        }), 200
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500