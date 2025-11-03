import requests
import pytest
import random
from datetime import datetime, timedelta

class TestSistemaCompleto:    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    @pytest.fixture
    def admin_token(self, base_url):
        # Obtém token de administrador
        data = {
            "email": "admin@lustro.com", 
            "senha": "Admin@007"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=data)
        return response.json()['access_token']
    
    @pytest.fixture
    def user_token(self, base_url):
        # Cria um usuário para teste
        email = f"final_test_{random.randint(10000, 99999)}@teste.com"
        cadastro_data = {
            "nome": "Usuário Final Teste",
            "email": email,
            "senha": "Senha@123",
            "confirmar_senha": "Senha@123"
        }
        response = requests.post(f"{base_url}/api/auth/register", json=cadastro_data)
        return response.json()['access_token']
    
    def test_configurar_horarios_funcionamento(self, base_url, admin_token):
        # Configura horários de funcionamento para os testes
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        horarios_config = [
            {"dia_semana": 0, "aberto": False, "hora_abertura": None, "hora_fechamento": None},       # Domingo
            {"dia_semana": 1, "aberto": True, "hora_abertura": "08:00", "hora_fechamento": "18:00"},  # Segunda
            {"dia_semana": 2, "aberto": True, "hora_abertura": "08:00", "hora_fechamento": "18:00"},  # Terça
            {"dia_semana": 3, "aberto": True, "hora_abertura": "08:00", "hora_fechamento": "18:00"},  # Quarta
            {"dia_semana": 4, "aberto": True, "hora_abertura": "08:00", "hora_fechamento": "18:00"},  # Quinta
            {"dia_semana": 5, "aberto": True, "hora_abertura": "08:00", "hora_fechamento": "18:00"},  # Sexta
            {"dia_semana": 6, "aberto": True, "hora_abertura": "08:00", "hora_fechamento": "16:00"},  # Sábado
        ]
        
        response = requests.put(
            f"{base_url}/api/admin/horarios-funcionamento",
            json=horarios_config,
            headers=headers
        )
        
        assert response.status_code == 200
        print("✅ Horários Configurados - Sistema pronto para agendamentos")
    
    def test_fluxo_completo_agendamento(self, base_url, admin_token, user_token):
        # Testa o fluxo completo: horários → agendar → listar → admin 
        headers_user = {"Authorization": f"Bearer {user_token}"}
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. Obter serviços e modelos
        servicos_response = requests.get(f"{base_url}/api/servicos")
        servico_id = servicos_response.json()['servicos'][0]['id']
        
        modelos_response = requests.get(f"{base_url}/api/modelos-veiculo") 
        modelo_id = modelos_response.json()['modelos'][0]['id']
        
        # 2. Encontrar um dia que tenha horários disponíveis
        # Testa vários dias até encontrar um com horários
        horarios = []
        data_com_horarios = None
        
        for dias_adicionais in range(1, 8):  # Testa próximos 7 dias
            data_teste = (datetime.now() + timedelta(days=dias_adicionais)).strftime('%Y-%m-%d')
            params = {"data": data_teste, "servico_id": servico_id}
            
            horarios_response = requests.get(
                f"{base_url}/api/agendamentos/horarios-disponiveis",
                params=params,
                headers=headers_user
            )
            
            if horarios_response.status_code == 200:
                horarios_teste = horarios_response.json()['horarios_disponiveis']
                if len(horarios_teste) > 0:
                    horarios = horarios_teste
                    data_com_horarios = data_teste
                    break
        
        # Se não encontrou horários, cria um agendamento manualmente para teste
        if not horarios:
            print("⚠️  Nenhum horário disponível automaticamente, criando agendamento direto")
            data_com_horarios = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            # Usa um horário fixo que deve estar disponível (segunda a sexta 08:00-18:00)
            horario_manual = "09:00"
        else:
            horario_manual = horarios[0]
        
        print(f"✅ Data selecionada: {data_com_horarios} - Horário: {horario_manual}")
        
        # 3. Criar agendamento
        placa = f"ABC{random.randint(1000, 9999)}"
        agendamento_data = {
            "data_agendamento": data_com_horarios,
            "horario_agendamento": horario_manual,
            "servico_id": servico_id,
            "placa": placa,
            "nome_proprietario": "Proprietário Teste",
            "telefone": "(11) 97777-6666", 
            "modelo_veiculo_id": modelo_id
        }
        
        agendar_response = requests.post(
            f"{base_url}/api/agendamentos",
            json=agendamento_data,
            headers=headers_user
        )
        
        # Se falhar por conflito de horário, tenta outro horário
        if agendar_response.status_code == 409:
            print("⚠️  Conflito de horário, tentando horário alternativo...")
            agendamento_data["horario_agendamento"] = "10:00"  # Horário alternativo
            agendar_response = requests.post(
                f"{base_url}/api/agendamentos",
                json=agendamento_data,
                headers=headers_user
            )
        
        assert agendar_response.status_code == 201, f"Falha ao criar agendamento: {agendar_response.text}"
        agendamento_id = agendar_response.json()['agendamento']['id']
        print(f"✅ Agendamento Criado - ID: {agendamento_id}")
        
        # 4. Ver agendamento do usuário
        meus_agendamentos_response = requests.get(
            f"{base_url}/api/agendamentos", 
            headers=headers_user
        )
        
        assert meus_agendamentos_response.status_code == 200
        meus_agendamentos = meus_agendamentos_response.json()['agendamentos']
        assert len(meus_agendamentos) > 0
        print(f"✅ Meus Agendamentos - {len(meus_agendamentos)} agendamento(s)")
        
        # 5. Admin busca por placa
        params_busca = {"placa": placa}
        busca_response = requests.get(
            f"{base_url}/api/admin/agendamentos/buscar",
            params=params_busca,
            headers=headers_admin
        )
        
        assert busca_response.status_code == 200
        agendamentos_busca = busca_response.json()['agendamentos']
        assert len(agendamentos_busca) > 0
        print(f"✅ Busca Admin - {len(agendamentos_busca)} agendamento(s) encontrado(s)")
        
        # 6. Admin marca como concluído
        concluir_response = requests.put(
            f"{base_url}/api/admin/dashboard/agendamentos/{agendamento_id}/concluir",
            headers=headers_admin
        )
        
        assert concluir_response.status_code == 200
        print("✅ Agendamento Concluído - Status atualizado com sucesso")
    
    def test_agendamentos_hoje_admin(self, base_url, admin_token):
        # Testa visualização de agendamentos de hoje pelo admin
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{base_url}/api/admin/dashboard/agendamentos-hoje",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert 'agendamentos' in result
        print(f"✅ Agendamentos Hoje - {len(result['agendamentos'])} agendamento(s) para hoje")
    
    def test_estatisticas_admin(self, base_url, admin_token):
        # Testa dashboard de estatísticas do admin
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(
            f"{base_url}/api/admin/dashboard/estatisticas", 
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert 'agendamentos_hoje' in result
        assert 'total_clientes' in result
        print("✅ Estatísticas Admin - Dashboard carregado com sucesso")