from app import db
from app.models import User, Servico, HorarioFuncionamento, Configuracao
from datetime import time
import os

def init_database():
    # Criar administrador padrão - SEM credenciais fixas
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if admin_email and admin_password:
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                nome='Administrador Sistema',
                email=admin_email,
                telefone='(00) 00000-0000',
                is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            print("Administrador criado com as credenciais das variáveis de ambiente")

    # Serviços disponíveis (dados não sensíveis)
    servicos = [
        {
            'nome': 'Lavagem Externa',
            'descricao': 'Lavagem completa da parte externa do veículo',
            'preco_base': 30.00,
            'duracao_minutos': 30
        },
        {
            'nome': 'Lavagem Interna', 
            'descricao': 'Limpeza completa do interior do veículo',
            'preco_base': 40.00,
            'duracao_minutos': 45
        },
        {
            'nome': 'Lavagem Completa',
            'descricao': 'Lavagem interna e externa completa', 
            'preco_base': 60.00,
            'duracao_minutos': 75
        }
    ]
    
    for servico_data in servicos:
        servico = Servico.query.filter_by(nome=servico_data['nome']).first()
        if not servico:
            servico = Servico(**servico_data)
            db.session.add(servico)
            print(f"Serviço criado: {servico_data['nome']}")
    
    # Horários de funcionamento (dados não sensíveis)
    dias_semana = [
        {'dia': 'domingo', 'aberto': False, 'nome': 'Domingo'},
        {'dia': 'segunda', 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Segunda'},
        {'dia': 'terça', 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Terça'},
        {'dia': 'quarta', 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Quarta'},
        {'dia': 'quinta', 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Quinta'},
        {'dia': 'sexta', 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Sexta'},
        {'dia': 'sábado', 'aberto': True, 'abertura': time(8,0), 'fechamento': time(12,0), 'nome': 'Sábado'},
    ]
    
    for dia_data in dias_semana:
        horario = HorarioFuncionamento.query.filter_by(dia_semana=dia_data['dia']).first()
        if not horario:
            horario = HorarioFuncionamento(
                dia_semana=dia_data['dia'],
                aberto=dia_data['aberto']
            )
            if dia_data['aberto']:
                horario.hora_abertura = dia_data['abertura']
                horario.hora_fechamento = dia_data['fechamento']
            db.session.add(horario)
    
    # Configurações do sistema (dados não sensíveis)
    configuracoes = [
        {'chave': 'multa_cancelamento', 'valor': '20', 'descricao': 'Percentual de multa para cancelamento com menos de 24h'},
        {'chave': 'tempo_minimo_cancelamento', 'valor': '24', 'descricao': 'Horas mínimas para cancelamento sem multa'},
        {'chave': 'intervalo_agendamento', 'valor': '30', 'descricao': 'Intervalo entre agendamentos em minutos'}
    ]
    
    for config_data in configuracoes:
        config = Configuracao.query.filter_by(chave=config_data['chave']).first()
        if not config:
            config = Configuracao(**config_data)
            db.session.add(config)
    
    db.session.commit()