from app import db
from app.models import Administrador, Servico, ModeloVeiculo, HorarioFuncionamento
from datetime import time
import os

def init_database():
    try:
        print("Inicializando banco de dados com estrutura Aiven...")

        # Administrador
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        admin = Administrador.query.filter_by(email=admin_email).first()
        if not admin:
            admin = Administrador(
                email=admin_email,
                nome='Administrador Lustro'
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            print(f"Administrador criado: {admin_email}")
        else:
            print(f"Administrador já existe: {admin_email}")

        # Serviços
        servicos_data = [
            {'nome': 'Lavagem Interna', 'descricao': 'Interior limpo e higienizado', 'preco': 50.00, 'duracao_minutos': 60},
            {'nome': 'Lavagem Externa', 'descricao': 'Remova a sujeira e recupere o brilho', 'preco': 40.00, 'duracao_minutos': 45},
            {'nome': 'Lavagem Completa', 'descricao': 'Cuidado total por dentro e por fora', 'preco': 80.00, 'duracao_minutos': 90}
        ]

        for servico_data in servicos_data:
            servico = Servico.query.filter_by(nome=servico_data['nome']).first()
            if not servico:
                servico = Servico(**servico_data)
                db.session.add(servico)
                print(f"Serviço criado: {servico_data['nome']}")

        # Modelos de veículo
        modelos_data = ['Sedan', 'Hatch', 'SUV', 'Pickup', 'Van', 'Coupé', 'Conversível', 'Station Wagon']
        for modelo_nome in modelos_data:
            modelo = ModeloVeiculo.query.filter_by(nome=modelo_nome).first()
            if not modelo:
                modelo = ModeloVeiculo(nome=modelo_nome)
                db.session.add(modelo)
                print(f"Modelo criado: {modelo_nome}")

        # Horários de funcionamento
        horarios_data = [
            (1, True, time(8, 0), time(18, 0)),  # Segunda
            (2, True, time(8, 0), time(18, 0)),  # Terça
            (3, True, time(8, 0), time(18, 0)),  # Quarta
            (4, True, time(8, 0), time(18, 0)),  # Quinta
            (5, True, time(8, 0), time(18, 0)),  # Sexta
            (6, True, time(8, 0), time(16, 0)),  # Sábado
            (0, False, None, None)               # Domingo
        ]

        for dia_semana, aberto, abertura, fechamento in horarios_data:
            horario = HorarioFuncionamento.query.filter_by(dia_semana=dia_semana).first()
            if not horario:
                horario = HorarioFuncionamento(
                    dia_semana=dia_semana,
                    aberto=aberto,
                    hora_abertura=abertura,
                    hora_fechamento=fechamento
                )
                db.session.add(horario)
                print(f"Horário configurado: {dia_semana}")

        db.session.commit()
        print("Banco de dados inicializado com sucesso!")

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inicializar banco: {str(e)}")
        raise e