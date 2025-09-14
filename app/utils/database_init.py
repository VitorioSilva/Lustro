from app import db
from app.models import User, Servico, HorarioFuncionamento, Configuracao
from datetime import time

def init_database():    
    # Criar administrador padrão
    admin = User.query.filter_by(email='admin@gmail.com').first()
    if not admin:
        admin = User(
            nome='Administrador',
            email='admin@gmail.com',
            telefone='(00) 00000-0000',
            is_admin=True
        )
        admin.set_password('admin12345678')
        db.session.add(admin)
        print("Administrador criado: admin@gmail.com / admin12345678")
    
    # Serviços disponíveis
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
    
    # Horários de funcionamento padrão (Seg-Sex 8h-18h, Sáb 8h-12h)
    dias_semana = [
        {'dia': 0, 'aberto': False, 'nome': 'Domingo'},  # Domingo fechado
        {'dia': 1, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Segunda'},
        {'dia': 2, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Terça'},
        {'dia': 3, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Quarta'},
        {'dia': 4, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Quinta'},
        {'dia': 5, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Sexta'},
        {'dia': 6, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(12,0), 'nome': 'Sábado'},
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
            status = "aberto" if dia_data['aberto'] else "fechado"
            print(f"{dia_data['nome']}: {status}")
    
    # Configurações do sistema
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
            print(f"Configuração: {config_data['chave']} = {config_data['valor']}")
    
    db.session.commit()