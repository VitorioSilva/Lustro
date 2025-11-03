import requests
import pytest
import random

class TestAuthentication:
    """Testes de autenticação - Login e Cadastro"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    @pytest.fixture
    def unique_email(self):
        """Gera um email único para cada teste"""
        return f"teste_{random.randint(10000, 99999)}@email.com"
    
    def test_login_admin(self, base_url):
        """Testa login do administrador"""
        data = {
            "email": "admin@lustro.com",
            "senha": "Admin@007"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert 'access_token' in result
        assert result['tipo'] == 'admin'
        print("✅ Login Admin - Administrador autenticado com sucesso")
    
    def test_cadastro_usuario(self, base_url, unique_email):
        """Testa cadastro de novo usuário"""
        data = {
            "nome": "Usuário Teste",
            "email": unique_email,
            "senha": "Senha@123",
            "confirmar_senha": "Senha@123",
            "telefone": "(11) 99999-9999"
        }
        response = requests.post(f"{base_url}/api/auth/register", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert 'access_token' in result
        assert result['user']['email'] == unique_email
        print("✅ Cadastro Usuário - Usuário criado com sucesso")
    
    def test_login_usuario(self, base_url, unique_email):
        """Testa login de usuário comum"""
        # Primeiro cadastra o usuário
        cadastro_data = {
            "nome": "Usuário Login Teste",
            "email": unique_email,
            "senha": "Senha@123",
            "confirmar_senha": "Senha@123"
        }
        requests.post(f"{base_url}/api/auth/register", json=cadastro_data)
        
        # Agora testa o login
        login_data = {
            "email": unique_email,
            "senha": "Senha@123"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        result = response.json()
        assert 'access_token' in result
        assert result['tipo'] == 'cliente'
        print("✅ Login Usuário - Usuário autenticado com sucesso")
    
    def test_login_credenciais_invalidas(self, base_url):
        """Testa login com credenciais inválidas"""
        data = {
            "email": "email_inexistente@teste.com",
            "senha": "senha_errada"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=data)
        
        assert response.status_code == 401
        result = response.json()
        assert 'error' in result
        print("✅ Login Credenciais Inválidas - Rejeitou credenciais erradas")