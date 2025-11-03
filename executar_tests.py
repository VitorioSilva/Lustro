import subprocess
import sys

def executar_todos_testes():
    print("🚀 EXECUTANDO SUITE COMPLETA DE TESTES...")
    
    testes = [
        "test_health.py",
        "test_auth.py", 
        "test_servicos.py",
        "test_modelos_veiculo.py",
        "test_agendamentos.py",
        "test_admin_completo.py"
    ]
    
    total_passaram = 0
    total_testes = 0
    
    for teste in testes:
        resultado = subprocess.run(
            ["pytest", f"tests/{teste}", "-v"],
            capture_output=True,
            text=True
        )
        
        # Contar testes passados
        linhas = resultado.stdout.split('\n')
        passaram = len([l for l in linhas if 'PASSED' in l])
        total_passaram += passaram
        total_testes += passaram
        
        print(f"📋 {teste}: {passaram} testes passaram")
    
    print(f"\n🎉 RESULTADO FINAL: {total_passaram} testes PASSARAM!")

if __name__ == "__main__":
    executar_todos_testes()