from app import db
from app.models import User, Servico, HorarioFuncionamento, Configuracao
from datetime import time
import os

def init_database():
    try:
        print("Inicializando banco de dados...")
        
        # Criar administrador padrão
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                nome='Administrador Sistema',
                email=admin_email,
                telefone='(11) 99999-9999',
                is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            print("Administrador criado")
        
        # Serviços disponíveis
        servicos = [
            {
                'nome': 'Lavagem Externa',
                'descricao': 'Remova a sujeira e recupere o brilho',
                'preco_base': 40.00,
                'duracao_minutos': 30
            },
            {
                'nome': 'Lavagem Interna', 
                'descricao': 'Interior limpo e higienizado',
                'preco_base': 50.00,
                'duracao_minutos': 45
            },
            {
                'nome': 'Lavagem Completa',
                'descricao': 'Cuidado total por dentro e por fora', 
                'preco_base': 80.00,
                'duracao_minutos': 75
            }
        ]
        
        for servico_data in servicos:
            servico = Servico.query.filter_by(nome=servico_data['nome']).first()
            if not servico:
                servico = Servico(**servico_data)
                db.session.add(servico)
                print(f"Serviço criado: {servico_data['nome']} - R$ {servico_data['preco_base']}")
        
        # CORREÇÃO: Horários alinhados com Python (Segunda=0, Domingo=6)
        dias_semana = [
            {'dia': 0, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Segunda-feira'},
            {'dia': 1, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Terça-feira'},
            {'dia': 2, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Quarta-feira'},
            {'dia': 3, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Quinta-feira'},
            {'dia': 4, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(18,0), 'nome': 'Sexta-feira'},
            {'dia': 5, 'aberto': True, 'abertura': time(8,0), 'fechamento': time(16,0), 'nome': 'Sábado'},
            {'dia': 6, 'aberto': False, 'abertura': time(0,0), 'fechamento': time(0,0), 'nome': 'Domingo'},
        ]
        
        for dia_data in dias_semana:
            horario = HorarioFuncionamento.query.filter_by(dia_semana=dia_data['dia']).first()
            if not horario:
                horario = HorarioFuncionamento(
                    dia_semana=dia_data['dia'],
                    aberto=dia_data['aberto'],
                    hora_abertura=dia_data['abertura'],
                    hora_fechamento=dia_data['fechamento']
                )
                db.session.add(horario)
                print(f"Horário configurado: {dia_data['nome']}")
        
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
                print(f"Configuração criada: {config_data['chave']}")
        
        db.session.commit()
        print("Banco de dados inicializado com sucesso!")
        
        # Log das credenciais do admin (apenas em desenvolvimento)
        if os.getenv('FLASK_ENV') == 'development':
            print(f"Admin: {admin_email} | Senha: {admin_password}")
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inicializar banco: {str(e)}")
        raise e