from flask import jsonify
import re
from datetime import datetime

def validate_email(email):
    # CORREÇÃO: Permitir qualquer email válido
    if not email or not isinstance(email, str):
        return False, "Email deve ser uma string"
    
    email = email.lower().strip()
    
    if len(email) > 120:
        return False, "Email muito longo (máx. 120 caracteres)"
    
    # CORREÇÃO: Pattern para qualquer email válido
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    return True, "Email válido"

# CORREÇÃO: Senha mais amigável
def validate_password_strength(password):
    if not password or not isinstance(password, str):
        return False, "Senha é obrigatória"
    
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if len(password) > 50:
        return False, "Senha muito longa (máx. 50 caracteres)"
    
    # Verificar caracteres repetidos
    if re.search(r'(.)\1{3,}', password):
        return False, "Senha contém muitos caracteres repetidos"
    
    # Verificar sequências
    sequences = ['1234', '2345', '3456', '4567', '5678', '6789', '7890',
                'abcd', 'bcde', 'cdef', 'defg', 'efgh', 'fghi', 'ghij',
                'ijkl', 'jklm', 'klmn', 'lmno', 'mnop', 'nopq', 'opqr',
                'pqrs', 'qrst', 'rstu', 'stuv', 'tuvw', 'uvwx', 'vwxy', 'wxyz']
    
    password_lower = password.lower()
    for seq in sequences:
        if seq in password_lower:
            return False, "Senha contém sequência muito óbvia"
    
    # Verificar senhas comuns
    common_passwords = ['123456', 'password', 'senha123', 'admin123', 'qwerty']
    if password_lower in common_passwords:
        return False, "Senha muito comum"
    
    # CORREÇÃO: Exigências reduzidas
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos um número"
    
    return True, "Senha forte"

def validate_phone(telefone):
    # Valida formato de telefone brasileiro
    if not telefone:
        return True, "Telefone opcional"
    
    if not isinstance(telefone, str):
        return False, "Telefone deve ser uma string"
    
    pattern = r'^\(\d{2}\) \d{4,5}-\d{4}$'
    if not re.match(pattern, telefone):
        return False, "Formato de telefone inválido. Use: (00) 00000-0000"
    
    return True, "Telefone válido"

def validate_placa(placa):
    # Valida formato de placa
    if not placa or not isinstance(placa, str):
        return False, "Placa é obrigatória"
    
    placa = placa.upper().replace('-', '').replace(' ', '')
    
    if len(placa) != 7:
        return False, "Placa deve ter 7 caracteres"
    
    pattern_mercosul = r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$'
    pattern_antigo = r'^[A-Z]{3}[0-9]{4}$'
    
    if not (re.match(pattern_mercosul, placa) or re.match(pattern_antigo, placa)):
        return False, "Formato de placa inválido"
    
    return True, "Placa válida"

def validate_name(nome):
    # CORREÇÃO: Nome mais flexível
    if not nome or not isinstance(nome, str):
        return False, "Nome é obrigatório"
    
    nome = nome.strip()
    
    if len(nome) < 2:
        return False, "Nome muito curto"
    
    if len(nome) > 100:
        return False, "Nome muito longo (máx. 100 caracteres)"
    
    if len(nome.split()) < 2:
        return False, "Informe nome completo"
    
    # CORREÇÃO: Permitir números e caracteres comuns
    if not re.match(r'^[a-zA-ZÀ-ÿ0-9\s\.\-]+$', nome):
        return False, "Nome contém caracteres inválidos"
    
    return True, "Nome válido"

def validate_date_format(date_string):
    # Valida formato de data ISO
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True, "Data válida"
    except ValueError:
        return False, "Formato de data inválido. Use: YYYY-MM-DDTHH:MM:SS"

def validate_vehicle_type(tipo):
    # Valida tipo de veículo
    tipos_validos = ['hatch', 'sedan', 'suv', 'caminhonete', 'van']
    
    if not tipo or not isinstance(tipo, str):
        return False, "Tipo de veículo é obrigatório"
    
    tipo = tipo.lower().strip()
    
    if tipo not in tipos_validos:
        return False, f"Tipo de veículo inválido. Use: {', '.join(tipos_validos)}"
    
    return True, "Tipo de veículo válido"

def error_response(message, status_code=400):
    # Retorna resposta de erro padronizada
    return jsonify({'error': message}), status_code