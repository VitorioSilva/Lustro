from flask import Blueprint, jsonify
from app.models import ModeloVeiculo

modelos_bp = Blueprint('modelos', __name__)

@modelos_bp.route('', methods=['GET'])
def listar_modelos():
    try:
        modelos = ModeloVeiculo.query.all()
        return jsonify({
            'modelos': [modelo.to_dict() for modelo in modelos]
        }), 200
    except Exception as e:
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500