import pytest
import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:5000')

@pytest.fixture
def base_url():
    return BASE_URL

@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def token(admin_credentials):
    # Fixture para obter token de admin para testes
    import requests
    response = requests.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        pytest.fail("Falha ao obter token de autenticação")

@pytest.fixture
def admin_credentials():
    return {
        "email": "admin@lustro.com",
        "senha": "Admin@007"
    }