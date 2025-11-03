import requests
import pytest

class TestServicos:    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    @pytest.fixture
    def admin_token(self, base_url):
        # Obtém token de administrador
        data = {
            "email": "admin@lustro.com",
            "senha": "admin123"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=data)
        return response.json()['access_token']
    
    def test_listar_servicos_publico(self, base_url):
        # Testa listagem de serviços (acesso público)
        response = requests.get(f"{base_url}/api/servicos")
        
        assert response.status_code == 200
        result = response.json()
        assert 'servicos' in result
        assert len(result['servicos']) > 0
        
        # Verifica se os serviços esperados existem
        servicos_nomes = [s['nome'] for s in result['servicos']]
        assert 'Lavagem Interna' in servicos_nomes
        assert 'Lavagem Externa' in servicos_nomes
        assert 'Lavagem Completa' in servicos_nomes
        
        print("✅ Listar Serviços Público - Serviços listados com sucesso")
    
    def test_servicos_possuem_precos(self, base_url):
        # Testa se os serviços possuem preços definidos
        response = requests.get(f"{base_url}/api/servicos")
        
        assert response.status_code == 200
        result = response.json()
        
        for servico in result['servicos']:
            assert 'preco' in servico
            assert servico['preco'] > 0
            assert 'duracao_minutos' in servico
            assert servico['duracao_minutos'] > 0
        
        print("✅ Serviços com Preços - Todos têm preço e duração definidos")
    
    def test_detalhes_servicos(self, base_url):
        # Testa se os serviços possuem descrições
        response = requests.get(f"{base_url}/api/servicos")
        
        assert response.status_code == 200
        result = response.json()
        
        for servico in result['servicos']:
            assert 'nome' in servico
            assert 'descricao' in servico
            assert servico['descricao'] is not None
            assert len(servico['descricao']) > 0
        
        print("✅ Detalhes Serviços - Todos têm descrição completa")
    
    def test_servicos_ativos(self, base_url):
        # Testa se apenas serviços ativos são listados
        response = requests.get(f"{base_url}/api/servicos")
        
        assert response.status_code == 200
        result = response.json()
        
        for servico in result['servicos']:
            assert servico['ativo'] == True
        
        print("✅ Serviços Ativos - Apenas serviços ativos são listados")