from flask import Blueprint, request, jsonify
import os
from datetime import datetime

twilio_webhook_bp = Blueprint('twilio_webhook', __name__)

@twilio_webhook_bp.route('/webhook', methods=['POST'])
def twilio_webhook():
    """Webhook para receber mensagens do Twilio"""
    try:
        # Obter dados da mensagem
        from_number = request.form.get('From', '')
        body = request.form.get('Body', '')
        message_sid = request.form.get('MessageSid', '')
        
        print(f"📩 Mensagem recebida do Twilio:")
        print(f"   De: {from_number}")
        print(f"   Mensagem: {body}")
        print(f"   SID: {message_sid}")
        print(f"   Hora: {datetime.now().strftime('%H:%M:%S')}")
        
        # Log completo para debug
        print("📋 Dados completos da requisição:")
        for key, value in request.form.items():
            print(f"   {key}: {value}")
        
        # Aqui você pode processar respostas dos clientes
        # Ex: confirmar cancelamentos, responder dúvidas, etc.
        
        return '', 200
        
    except Exception as e:
        print(f"❌ Erro no webhook: {str(e)}")
        return '', 500

@twilio_webhook_bp.route('/status', methods=['POST'])
def twilio_status():
    """Webhook para receber status das mensagens"""
    try:
        message_sid = request.form.get('MessageSid', '')
        message_status = request.form.get('MessageStatus', '')
        error_code = request.form.get('ErrorCode', '')
        error_message = request.form.get('ErrorMessage', '')
        
        print(f"📊 Status atualizado:")
        print(f"   SID: {message_sid}")
        print(f"   Status: {message_status}")
        print(f"   Error Code: {error_code}")
        print(f"   Error Message: {error_message}")
        print(f"   Hora: {datetime.now().strftime('%H:%M:%S')}")
        
        # Log completo para debug
        print("📋 Dados completos do status:")
        for key, value in request.form.items():
            print(f"   {key}: {value}")
        
        # Log do status para debug
        if message_status == 'undelivered':
            print(f"❌ MENSAGEM NÃO ENTREGUE: {message_sid}")
            print(f"   Código do erro: {error_code}")
            print(f"   Mensagem do erro: {error_message}")
        elif message_status == 'delivered':
            print(f"✅ MENSAGEM ENTREGUE: {message_sid}")
        elif message_status == 'sent':
            print(f"📤 MENSAGEM ENVIADA: {message_sid}")
        
        return '', 200
        
    except Exception as e:
        print(f"❌ Erro no status webhook: {str(e)}")
        return '', 500

@twilio_webhook_bp.route('/test', methods=['GET'])
def test_webhook():
    """Teste simples do webhook"""
    return jsonify({
        'message': 'Webhook Twilio está funcionando!',
        'timestamp': datetime.now().isoformat(),
        'webhook_url': 'https://lustro-black.vercel.app/api/twilio/webhook',
        'status_url': 'https://lustro-black.vercel.app/api/twilio/status'
    }), 200