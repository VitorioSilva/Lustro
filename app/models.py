from app import db
from datetime import datetime, time
import bcrypt

class User(db.Model):
    __tablename__ = 'clientes'  # Nome da tabela no MySQL
    
    id = db.Column('id_cliente', db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column('senha', db.String(255), nullable=False)
    telefone = db.Column(db.String(20))
    created_at = db.Column('data_cadastro', db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relacionamentos - ajustar para as novas tabelas
    agendamentos = db.relationship('Agendamento', backref='cliente', lazy=True, cascade='all, delete-orphan')
    veiculos = db.relationship('Veiculo', backref='dono', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.senha_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.senha_hash.encode('utf-8'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Veiculo(db.Model):
    __tablename__ = 'veiculos'
    
    id = db.Column('id_veiculo', db.Integer, primary_key=True)
    placa = db.Column(db.String(10), nullable=False)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    cor = db.Column(db.String(30))
    tipo = db.Column(db.String(50), nullable=False)  # Ajustado para VARCHAR(50)
    user_id = db.Column('id_cliente', db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='veiculo', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'placa': self.placa,
            'marca': self.marca,
            'modelo': self.modelo,
            'cor': self.cor,
            'tipo': self.tipo,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Servico(db.Model):
    __tablename__ = 'tipos_lavagem'
    
    id = db.Column('id_tipo', db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)
    preco_base = db.Column('preco_base', db.Float, nullable=False)
    duracao_minutos = db.Column(db.Integer, nullable=False, default=30)
    ativo = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco_base': float(self.preco_base),
            'duracao_minutos': self.duracao_minutos,
            'ativo': self.ativo
        }

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    
    id = db.Column('id_agendamento', db.Integer, primary_key=True)
    data_agendamento = db.Column('data_agendada', db.Date, nullable=False)
    horario = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='confirmado')
    valor_total = db.Column('valor', db.Float, nullable=False)
    observacoes = db.Column(db.Text)
    created_at = db.Column('data_criacao', db.DateTime, default=datetime.utcnow)
    
    # Chaves estrangeiras
    user_id = db.Column('id_cliente', db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    veiculo_id = db.Column('id_veiculo', db.Integer, db.ForeignKey('veiculos.id_veiculo'), nullable=False)
    servico_id = db.Column('id_tipo', db.Integer, db.ForeignKey('tipos_lavagem.id_tipo'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_agendamento': self.data_agendamento.isoformat() if self.data_agendamento else None,
            'horario': self.horario.strftime('%H:%M') if self.horario else None,
            'status': self.status,
            'valor_total': float(self.valor_total) if self.valor_total else 0.0,
            'observacoes': self.observacoes,
            'user_id': self.user_id,
            'veiculo_id': self.veiculo_id,
            'servico_id': self.servico_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'chave': self.chave,
            'valor': self.valor,
            'descricao': self.descricao
        }

class HorarioFuncionamento(db.Model):
    __tablename__ = 'horarios_disponiveis'
    
    id = db.Column('id_horario', db.Integer, primary_key=True)
    dia_semana = db.Column(db.Integer, nullable=False)  # MUDADO para Integer: 0=segunda, 1=terça, etc.
    aberto = db.Column(db.Boolean, default=True)
    hora_abertura = db.Column('hora_inicio', db.Time, default=time(8, 0))
    hora_fechamento = db.Column('hora_fim', db.Time, default=time(18, 0))
    
    def to_dict(self):
        # Mapear número para nome do dia
        dias = {
            0: 'segunda', 1: 'terça', 2: 'quarta', 3: 'quinta',
            4: 'sexta', 5: 'sábado', 6: 'domingo'
        }
        
        return {
            'id': self.id,
            'dia_semana': self.dia_semana,
            'dia_semana_nome': dias.get(self.dia_semana, ''),
            'aberto': self.aberto,
            'hora_abertura': self.hora_abertura.strftime('%H:%M') if self.hora_abertura else None,
            'hora_fechamento': self.hora_fechamento.strftime('%H:%M') if self.hora_fechamento else None
        }

class Administrador(db.Model):
    __tablename__ = 'administradores'
    
    id = db.Column('id_admin', db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column('senha', db.String(255), nullable=False)
    
    def set_password(self, password):
        self.senha_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.senha_hash.encode('utf-8'))