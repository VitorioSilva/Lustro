import requests
import pytest
import random
from datetime import datetime, timedelta

class TestAgendamentos:
    """Testes do sistema de agendamentos"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    @pytest.fixture
    def user_token(self, base_url):
        """Cria um usuário e retorna o token"""
        email = f"user_agendamento_{random.randint(10000, 99999)}@teste.com"
        
        # Cadastra usuário
        cadastro_data = {
            "nome": "Usuário Agendamento Teste",
            "email": email,
            "senha": "Senha@123",
            "confirmar_senha": "Senha@123",
            "telefone": "(11) 99999-9999"
        }
        response = requests.post(f"{base_url}/api/auth/register", json=cadastro_data)
        return response.json()['access_token']
    
    @pytest.fixture
    def admin_token(self, base_url):
        """Obtém token de administrador"""
        data = {
            "email": "admin@lustro.com",
            "senha": "Admin@007"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=data)
        return response.json()['access_token']
    
    @pytest.fixture
    def servico_id(self, base_url):
        """Obtém o ID do primeiro serviço disponível"""
        response = requests.get(f"{base_url}/api/servicos")
        return response.json()['servicos'][0]['id']
    
    @pytest.fixture
    def modelo_veiculo_id(self, base_url):
        """Obtém o ID do primeiro modelo de veículo"""
        response = requests.get(f"{base_url}/api/modelos-veiculo")
        return response.json()['modelos'][0]['id']
    
    def test_horarios_disponiveis(self, base_url, user_token, servico_id):
        """Testa consulta de horários disponíveis"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Data futura para teste
        data_futura = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        params = {
            "data": data_futura,
            "servico_id": servico_id
        }
        
        response = requests.get(
            f"{base_url}/api/agendamentos/horarios-disponiveis",
            params=params,
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert 'horarios_disponiveis' in result
        assert isinstance(result['horarios_disponiveis'], list)
        
        print(f"✅ Horários Disponíveis - {len(result['horarios_disponiveis'])} horários encontrados")
    
    def test_criar_agendamento(self, base_url, user_token, servico_id, modelo_veiculo_id):
        """Testa criação de agendamento"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Data futura para teste
        data_futura = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Obter um horário realmente disponível antes de agendar
        params = {"data": data_futura, "servico_id": servico_id}
        response_horarios = requests.get(f"{base_url}/api/agendamentos/horarios-disponiveis", params=params, headers=headers)
        horarios_disponiveis = response_horarios.json().get("horarios_disponiveis", [])

        if not horarios_disponiveis:
            pytest.skip("Nenhum horário disponível para o serviço nesta data")

        agendamento_data = {
            "data_agendamento": data_futura,
            "horario_agendamento": horarios_disponiveis[0],  # ✅ usa um horário real
            "servico_id": servico_id,
            "placa": f"ABC{random.randint(1000, 9999)}",
            "nome_proprietario": "Proprietário Teste",
            "telefone": "(11) 98888-7777",
            "modelo_veiculo_id": modelo_veiculo_id
        }

        response = requests.post(
            f"{base_url}/api/agendamentos",
            json=agendamento_data,
            headers=headers
        )
        print(response.status_code, response.json())

        assert response.status_code == 201
        result = response.json()
        assert 'agendamento' in result
        assert 'id' in result['agendamento']
        assert result['agendamento']['status'] == 'confirmado'
        
        print(f"✅ Criar Agendamento - Agendamento {result['agendamento']['id']} criado com sucesso")
        return result['agendamento']['id']
    
    def test_listar_agendamentos_usuario(self, base_url, user_token):
        """Testa listagem de agendamentos do usuário"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = requests.get(f"{base_url}/api/agendamentos", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert 'agendamentos' in result
        assert isinstance(result['agendamentos'], list)
        
        print(f"✅ Listar Agendamentos Usuário - {len(result['agendamentos'])} agendamentos encontrados")
    
    def test_listar_agendamentos_admin(self, base_url, admin_token):
        """Testa listagem de todos os agendamentos (admin)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{base_url}/api/admin/dashboard/agendamentos", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert 'agendamentos' in result
        assert isinstance(result['agendamentos'], list)
        
        print(f"✅ Listar Agendamentos Admin - {len(result['agendamentos'])} agendamentos encontrados")
    
    def test_agendamentos_estrutura(self, base_url, user_token):
        """Testa se os agendamentos possuem estrutura completa"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = requests.get(f"{base_url}/api/agendamentos", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        if result['agendamentos']:
            agendamento = result['agendamentos'][0]
            campos_obrigatorios = [
                'id', 'data_agendamento', 'horario_agendamento', 
                'valor_total', 'status', 'servico_nome', 'veiculo_placa'
            ]
            
            for campo in campos_obrigatorios:
                assert campo in agendamento, f"Campo {campo} não encontrado no agendamento"
        
        print("✅ Estrutura Agendamentos - Campos obrigatórios presentes")