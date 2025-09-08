from flask import jsonify
import re

def validate_email(email):
    # Valida formato do email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # Valida força da senha
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    return True, "Senha válida"

def error_response(message, status_code=400):
    # Retorna resposta de erro padronizada
    return jsonify({'error': message}), status_code