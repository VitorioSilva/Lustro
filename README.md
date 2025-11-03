# 🚗 Lustro - Sistema de Agendamento para Lava Jato

Back-end completo para sistema de agendamento de serviços de lava jato, desenvolvido em **Python com Flask**.

---

## 🚀 Funcionalidades

### 👤 Área do Cliente
- ✅ Cadastro e autenticação de usuários  
- ✅ Agendamento de serviços (lavagem interna, externa, completa)  
- ✅ Seleção de data e horários disponíveis  
- ✅ Cadastro de veículos (placa, modelo, proprietário)  
- ✅ Visualização e cancelamento de agendamentos  
- ✅ Histórico de serviços  

### 🛠️ Área Administrativa
- ✅ Dashboard com estatísticas  
- ✅ Gestão completa de agendamentos  
- ✅ Busca de agendamentos por placa  
- ✅ Configuração de horários de funcionamento  
- ✅ Marcar serviços como concluídos  
- ✅ Visualização de agendamentos do dia  

---

## 🏗️ Tecnologias

| Categoria | Tecnologias |
|------------|-------------|
| **Back-end** | Python 3.12, Flask |
| **Banco de Dados** | MySQL (Aiven) / SQLite (dev) |
| **Autenticação** | JWT Tokens |
| **ORM** | SQLAlchemy |
| **Deploy** | Vercel |
| **Testes** | Pytest |

---

## 📋 Pré-requisitos

- Python 3.12+  
- MySQL ou SQLite  
- Conta no [Aiven](https://aiven.io/) (para produção)

---

## ⚙️ Instalação e Configuração

### 1. Clone o repositório
```bash
git clone https://github.com/VitorioSilva/Lustro.git
cd Lustro
```

### 2. Crie um ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:

```bash
# Banco de Dados (Produção - Aiven)
DB_HOST=seu-host-aiven
DB_PORT=3306
DB_USER=seu-usuario
DB_PASSWORD=sua-senha
DB_NAME=nome-do-banco

# JWT Secret Key
JWT_SECRET_KEY=sua-chave-secreta

# Admin padrão
ADMIN_EMAIL=adminemail@exemplo.com
ADMIN_PASSWORD=senha-admin-segura
```

### 5. Inicialize o banco de dados
```bash
curl -X POST http://localhost:5000/api/init-db
```

### 6. Execute a aplicação
```bash
python run.py
```

A API estará disponível em: **http://localhost:5000**

---

## 🗄️ Estrutura do Projeto

```bash
Lustro
├── app
│   ├── __init__.py
│   ├── models.py
│   ├── routes
│   │   ├── admin_dashboard.py
│   │   ├── admin.py
│   │   ├── agendamentos.py
│   │   ├── auth.py
│   │   ├── modelos_veiculo.py
│   │   ├── servicos.py
│   │   ├── users.py
│   │   └── veiculos.py
│   └── utils
│       ├── database_init.py
│       └── security.py
├── executar_tests.py
├── requirements.txt
├── run.py
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── test_admin_completo.py
│   ├── test_agendamentos.py
│   ├── test_auth.py
│   ├── test_health.py
│   ├── test_modelos_veiculo.py
│   └── test_servicos.py
└── vercel.json
```

---

## 📡 Endpoints da API

### 🔐 Autenticação
| Método | Endpoint | Descrição |
|--------|-----------|------------|
| `POST` | `/api/auth/register` | Cadastro de usuário |
| `POST` | `/api/auth/login` | Login |
| `POST` | `/api/auth/admin/login` | Login administrativo |

### 👤 Usuários
| Método | Endpoint | Descrição |
|--------|-----------|------------|
| `GET` | `/api/users/me` | Perfil do usuário logado |
| `PUT` | `/api/users/me` | Atualizar perfil |
| `PUT` | `/api/users/me/password` | Alterar senha |

### 🚗 Veículos
| Método | Endpoint | Descrição |
|--------|-----------|------------|
| `GET` | `/api/veiculos` | Listar veículos do usuário |
| `POST` | `/api/veiculos` | Cadastrar veículo |
| `PUT` | `/api/veiculos/{id}` | Atualizar veículo |
| `DELETE` | `/api/veiculos/{id}` | Excluir veículo |

### 🧼 Serviços
| Método | Endpoint | Descrição |
|--------|-----------|------------|
| `GET` | `/api/servicos` | Listar serviços (público) |
| `POST` | `/api/servicos` | Criar serviço (admin) |
| `PUT` | `/api/servicos/{id}` | Atualizar serviço (admin) |
| `DELETE` | `/api/servicos/{id}` | Excluir serviço (admin) |

### 📅 Agendamentos
| Método | Endpoint | Descrição |
|--------|-----------|------------|
| `GET` | `/api/agendamentos` | Listar agendamentos do usuário |
| `POST` | `/api/agendamentos` | Criar agendamento |
| `GET` | `/api/agendamentos/{id}` | Detalhes do agendamento |
| `DELETE` | `/api/agendamentos/{id}` | Cancelar agendamento |
| `GET` | `/api/agendamentos/horarios-disponiveis` | Horários disponíveis |

### ⚙️ Administração
| Método | Endpoint | Descrição |
|--------|-----------|------------|
| `GET` | `/api/admin/dashboard/agendamentos` | Todos os agendamentos |
| `GET` | `/api/admin/dashboard/agendamentos-hoje` | Agendamentos de hoje |
| `PUT` | `/api/admin/dashboard/agendamentos/{id}/concluir` | Marcar como concluído |
| `GET` | `/api/admin/agendamentos/buscar` | Buscar por placa |
| `GET/PUT` | `/api/admin/horarios-funcionamento` | Configurar horários |

---

## 🧪 Testes

### Executar todos os testes
```bash
pytest tests/ -v
```

### Executar testes específicos
```bash
pytest tests/test_auth.py -v
pytest tests/test_agendamentos.py -v
pytest tests/ -v -s  # Output detalhado
```

### Cobertura de Testes
- ✅ Health Check & Database  
- ✅ Autenticação (login/cadastro)  
- ✅ Serviços e Modelos de Veículo  
- ✅ Sistema de Agendamentos  
- ✅ Painel Administrativo  
- ✅ Fluxo Completo Ponta a Ponta  

---

## 📊 Exemplos de Uso

### Criar Agendamento
```bash
curl -X POST http://localhost:5000/api/agendamentos \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "data_agendamento": "2025-12-11",
    "horario_agendamento": "10:00",
    "servico_id": 1,
    "placa": "ABC1234",
    "nome_proprietario": "João Silva",
    "telefone": "(11) 99999-9999",
    "modelo_veiculo_id": 1
  }'
```

### Buscar Agendamentos por Placa (Admin)
```bash
curl -X GET "http://localhost:5000/api/admin/agendamentos/buscar?placa=ABC1234" \
  -H "Authorization: Bearer <admin-token>"
```

---

## 🐛 Solução de Problemas

### Erro de Conexão com Banco
- Verifique as credenciais do Aiven  
- Confirme se o banco está ativo  
- Teste a conexão manualmente  

### Problemas de Autenticação
- Verifique o `JWT_SECRET_KEY`  
- Confirme se o token não expirou  
- Valide as credenciais do usuário  

### Horários Não Disponíveis
- Verifique a configuração de horários de funcionamento  
- Confirme se a data não é passada  
- Verifique conflitos com outros agendamentos  

---

## 🤝 Contribuição

1. Faça um fork do projeto  
2. Crie uma branch para sua feature:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit suas mudanças:
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. Push para a branch:
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença **MIT**.

---

## 👨‍💻 Desenvolvedor

**Vitório Santos** — [GitHub](https://github.com/VitorioSilva)

---

## 📞 Suporte

Em caso de dúvidas:
- Verifique a documentação da API  
- Consulte os testes automatizados  
- Abra uma issue no repositório  

---

⭐️ **Desenvolvido com ❤️ para facilitar a gestão de lava jatos!**
