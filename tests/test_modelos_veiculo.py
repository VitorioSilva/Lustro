import requests
import pytest

class TestModelosVeiculo:    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    def test_listar_modelos_veiculo(self, base_url):
        # Testa listagem de modelos de veículo (acesso público)
        response = requests.get(f"{base_url}/api/modelos-veiculo")
        
        assert response.status_code == 200
        result = response.json()
        assert 'modelos' in result
        assert len(result['modelos']) > 0
        
        print(f"✅ Listar Modelos Veículo - {len(result['modelos'])} modelos encontrados")
    
    def test_modelos_veiculo_estrutura(self, base_url):
        # Testa se os modelos possuem estrutura correta
        response = requests.get(f"{base_url}/api/modelos-veiculo")
        
        assert response.status_code == 200
        result = response.json()
        
        for modelo in result['modelos']:
            assert 'id' in modelo
            assert 'nome' in modelo
            assert isinstance(modelo['nome'], str)
            assert len(modelo['nome']) > 0
        
        print("✅ Estrutura Modelos - Todos têm ID e nome válidos")
    
    def test_modelos_veiculo_unicos(self, base_url):
        # Testa se os modelos são únicos
        response = requests.get(f"{base_url}/api/modelos-veiculo")
        
        assert response.status_code == 200
        result = response.json()
        
        nomes = [modelo['nome'] for modelo in result['modelos']]
        # Verifica se não há duplicatas
        assert len(nomes) == len(set(nomes))
        
        print("✅ Modelos Únicos - Não há modelos duplicados")
    
    def test_modelos_veiculo_esperados(self, base_url):
        # Testa se os modelos esperados estão presentes
        response = requests.get(f"{base_url}/api/modelos-veiculo")
        
        assert response.status_code == 200
        result = response.json()
        
        modelos_esperados = [
            'Sedan', 'Hatch', 'SUV', 'Pickup', 'Van', 
            'Coupé', 'Conversível', 'Station Wagon'
        ]
        
        nomes_encontrados = [modelo['nome'] for modelo in result['modelos']]
        
        for modelo_esperado in modelos_esperados:
            assert modelo_esperado in nomes_encontrados, f"Modelo {modelo_esperado} não encontrado"
        
        print("✅ Modelos Esperados - Todos os modelos padrão estão presentes")