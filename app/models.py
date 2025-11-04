from app import db
import bcrypt

class Administrador(db.Model):
    __tablename__ = 'administradores'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def set_password(self, password):
        self.senha_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.senha_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nome': self.nome,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

class User(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20))
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    atualizado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

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
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

class Servico(db.Model):
    __tablename__ = 'servicos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    duracao_minutos = db.Column(db.Integer, default=60)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': float(self.preco) if self.preco else 0.0,
            'duracao_minutos': self.duracao_minutos,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

class ModeloVeiculo(db.Model):
    __tablename__ = 'modelos_veiculo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

class Veiculo(db.Model):
    __tablename__ = 'veiculos'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    nome_proprietario = db.Column(db.String(100), nullable=False)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    modelo_veiculo_id = db.Column(db.Integer, db.ForeignKey('modelos_veiculo.id'), nullable=True)
    telefone = db.Column(db.String(20), nullable=False)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    atualizado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    modelo = db.relationship('ModeloVeiculo', backref='veiculos', lazy='joined')


    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nome_proprietario': self.nome_proprietario,
            'placa': self.placa,
            'modelo_veiculo_id': self.modelo_veiculo_id,
            'telefone': self.telefone,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

class HorarioFuncionamento(db.Model):
    __tablename__ = 'horarios_funcionamento'

    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.Integer, nullable=False)
    aberto = db.Column(db.Boolean, default=False)
    hora_abertura = db.Column(db.Time)
    hora_fechamento = db.Column(db.Time)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    atualizado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        dias = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        return {
            'id': self.id,
            'dia_semana': self.dia_semana,
            'dia_nome': dias[self.dia_semana] if 0 <= self.dia_semana < 7 else 'Desconhecido',
            'aberto': self.aberto,
            'hora_abertura': self.hora_abertura.strftime('%H:%M') if self.hora_abertura else None,
            'hora_fechamento': self.hora_fechamento.strftime('%H:%M') if self.hora_fechamento else None
        }

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'

    id = db.Column(db.Integer, primary_key=True)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_agendamento = db.Column(db.Date, nullable=False)
    horario_agendamento = db.Column(db.Time, nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pendente', 'confirmado', 'concluido', 'cancelado', 'expirado'), default='pendente')
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    atualizado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'veiculo_id': self.veiculo_id,
            'servico_id': self.servico_id,
            'user_id': self.user_id,
            'data_agendamento': self.data_agendamento.isoformat() if self.data_agendamento else None,
            'horario_agendamento': self.horario_agendamento.strftime('%H:%M') if self.horario_agendamento else None,
            'valor_total': float(self.valor_total) if self.valor_total else 0.0,
            'status': self.status,
            'observacoes': self.observacoes,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }