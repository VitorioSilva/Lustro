from app import db
from datetime import datetime, time
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='cliente', lazy=True)
    veiculos = db.relationship('Veiculo', backref='dono', lazy=True)
    
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
            'created_at': self.created_at.isoformat()
        }

class Veiculo(db.Model):
    __tablename__ = 'veiculos'
    
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    cor = db.Column(db.String(30))
    tipo = db.Column(db.String(20), nullable=False)  # sedan, hatch, suv, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='veiculo', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'placa': self.placa,
            'marca': self.marca,
            'modelo': self.modelo,
            'cor': self.cor,
            'tipo': self.tipo,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat()
        }

class Servico(db.Model):
    __tablename__ = 'servicos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)  # Lavagem interna, externa, completa
    descricao = db.Column(db.Text)
    preco_base = db.Column(db.Float, nullable=False)
    duracao_minutos = db.Column(db.Integer, nullable=False)  # Duração em minutos
    ativo = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco_base': self.preco_base,
            'duracao_minutos': self.duracao_minutos,
            'ativo': self.ativo
        }

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    data_agendamento = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='confirmado')  # confirmado, cancelado, concluido
    valor_total = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_agendamento': self.data_agendamento.isoformat(),
            'status': self.status,
            'valor_total': self.valor_total,
            'observacoes': self.observacoes,
            'user_id': self.user_id,
            'veiculo_id': self.veiculo_id,
            'servico_id': self.servico_id,
            'created_at': self.created_at.isoformat()
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
    __tablename__ = 'horarios_funcionamento'
    
    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Dom, 1=Seg, ..., 6=Sab
    aberto = db.Column(db.Boolean, default=True)
    hora_abertura = db.Column(db.Time, default=time(8, 0))  # 08:00
    hora_fechamento = db.Column(db.Time, default=time(18, 0))  # 18:00
    
    def to_dict(self):
        return {
            'id': self.id,
            'dia_semana': self.dia_semana,
            'aberto': self.aberto,
            'hora_abertura': self.hora_abertura.strftime('%H:%M'),
            'hora_fechamento': self.hora_fechamento.strftime('%H:%M')
        }