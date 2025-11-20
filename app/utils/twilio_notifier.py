import os
from twilio.rest import Client
from flask import current_app
from datetime import datetime

class TwilioNotifier:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')
        self.client = None
        
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                print("✅ Twilio client inicializado com sucesso")
                print(f"📞 Usando número: {self.whatsapp_from}")
            except Exception as e:
                print(f"❌ Erro ao inicializar Twilio: {str(e)}")
        else:
            print("⚠️ Twilio não configurado")
            print(f"Account SID: {bool(self.account_sid)}")
            print(f"Auth Token: {bool(self.auth_token)}")
    
    def is_configured(self):
        return self.client is not None
    
    def send_whatsapp(self, to_phone, message):
        """Envia mensagem WhatsApp via Twilio"""
        if not self.is_configured():
            print("❌ Twilio não configurado")
            return False
            
        try:
            # Formatar número (remover caracteres especiais)
            to_phone = ''.join(filter(str.isdigit, to_phone))
            
            # Garantir formato internacional (55 para Brasil)
            if to_phone.startswith('0'):
                to_phone = to_phone[1:]
            if not to_phone.startswith('55'):
                to_phone = '55' + to_phone
                
            print(f"📤 Enviando WhatsApp para +{to_phone}")
            print(f"📝 Mensagem: {message}")
            print(f"🕒 Hora: {datetime.now().strftime('%H:%M:%S')}")
            
            message_obj = self.client.messages.create(
                body=message,
                from_=self.whatsapp_from,
                to=f'whatsapp:+{to_phone}'
            )
            
            print(f"✅ WhatsApp enviado! SID: {message_obj.sid}")
            print(f"📊 Status: {message_obj.status}")
            print(f"🔗 URI: {message_obj.uri}")
            return True
            
        except Exception as e:
            print(f"❌ Erro Twilio: {str(e)}")
            return False
    
    def notify_agendamento_confirmado(self, telefone_cliente, nome_cliente, data, horario, servico_nome, valor):
        message = f"""✅ *Agendamento Confirmado - Lustro Lavagem*

Olá {nome_cliente}! Seu agendamento foi confirmado:

📅 *Data:* {data}
⏰ *Horário:* {horario}
🚗 *Serviço:* {servico_nome}
💵 *Valor:* R$ {valor:.2f}

Agradecemos pela preferência! 🚗💦

_Enviado automaticamente_"""
        return self.send_whatsapp(telefone_cliente, message)
    
    def notify_agendamento_cancelado(self, telefone_cliente, nome_cliente, data, horario, servico_nome):
        message = f"""❌ *Agendamento Cancelado - Lustro Lavagem*

Olá {nome_cliente}! Seu agendamento foi cancelado:

📅 *Data:* {data}
⏰ *Horário:* {horario}
🚗 *Serviço:* {servico_nome}

Esperamos vê-lo em uma próxima oportunidade!

_Enviado automaticamente_"""
        return self.send_whatsapp(telefone_cliente, message)
    
    def notify_status_atualizado(self, telefone_cliente, nome_cliente, data, horario, servico_nome, novo_status):
        status_map = {
            'andamento': '🔄 EM ANDAMENTO',
            'concluido': '✅ CONCLUÍDO', 
            'confirmado': '📋 CONFIRMADO',
            'pendente': '⏳ PENDENTE'
        }
        
        status_text = status_map.get(novo_status, novo_status.upper())
        
        message = f"""📋 *Status do Agendamento - Lustro Lavagem*

Olá {nome_cliente}! Seu agendamento foi atualizado:

📅 *Data:* {data}
⏰ *Horário:* {horario}  
🚗 *Serviço:* {servico_nome}
🔄 *Status:* {status_text}

Obrigado por escolher nossos serviços!

_Enviado automaticamente_"""
        return self.send_whatsapp(telefone_cliente, message)
    
    def test_connection(self):
        """Testa a conexão com o Twilio"""
        if not self.is_configured():
            return {'error': 'Twilio não configurado'}
        
        try:
            # Testa listando mensagens recentes (método leve)
            messages = self.client.messages.list(limit=1)
            return {
                'connected': True,
                'account_sid': self.account_sid,
                'whatsapp_from': self.whatsapp_from,
                'test_message': 'Conexão com Twilio estabelecida com sucesso'
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

# Instância global
twilio_notifier = TwilioNotifier()