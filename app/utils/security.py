from flask import jsonify
import re

def validate_email(email):
    # Valida formato do email
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # Valida força da senha
    if not password or not isinstance(password, str):
        return False, "Senha é obrigatória"
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    return True, "Senha válida"

def validate_phone(telefone):
    # Valida formato básico de telefone
    if not telefone:
        return True  # Telefone é opcional
    pattern = r'^\(\d{2}\) \d{4,5}-\d{4}$'
    return re.match(pattern, telefone) is not None

def validate_placa(placa):
    # Valida formato de placa (antigo e Mercosul)
    if not placa or not isinstance(placa, str):
        return False
    pattern = r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$|^[A-Z]{3}-?[0-9]{4}$'
    return re.match(pattern, placa.upper().replace('-', '')) is not None

def error_response(message, status_code=400):
    # Retorna resposta de erro padronizada
    return jsonify({'error': message}), status_code