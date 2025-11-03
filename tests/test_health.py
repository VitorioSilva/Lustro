import requests
import pytest

class TestHealthCheck:    
    def test_health_check(self):
        # Testa se a API está respondendo
        BASE_URL = "http://localhost:5000"
        response = requests.get(f"{BASE_URL}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'OK'
        assert 'Lustro API running' in data['message']
        print("✅ Health Check - API respondendo corretamente")
    
    def test_database_status(self):
        # Testa se o banco de dados está conectado
        BASE_URL = "http://localhost:5000"
        response = requests.get(f"{BASE_URL}/api/check-db")
        
        assert response.status_code == 200
        data = response.json()
        assert data['database_status'] == 'OK'
        print("✅ Database Status - Banco conectado corretamente")