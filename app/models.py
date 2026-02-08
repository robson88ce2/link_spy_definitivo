"""
Modelos do Banco de Dados - Sistema de Rastreamento para Investigações
Centraliza todos os modelos SQLAlchemy com segurança aprimorada
"""
import pytz
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import os

db = SQLAlchemy()


def horario_brasilia() -> datetime:
    """Retorna o objeto datetime atual no fuso horário de Brasília."""
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_brasilia)


# --- Helper para Criptografia ---
class EncryptedField:
    """
    Helper para criptografar/descriptografar campos sensíveis.
    Usado para proteger dados como IPs e localização no banco.
    """
    
    @staticmethod
    def get_cipher():
        """Obtém instância do cipher Fernet"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Em desenvolvimento, usar chave temporária (NUNCA em produção)
            if os.environ.get('FLASK_ENV') == 'development':
                key = Fernet.generate_key()
            else:
                raise ValueError("ENCRYPTION_KEY não configurada!")
        
        if isinstance(key, str):
            key = key.encode()
        
        return Fernet(key)
    
    @staticmethod
    def encrypt(data: str) -> str:
        """Criptografa uma string"""
        if not data:
            return data
        cipher = EncryptedField.get_cipher()
        return cipher.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        """Descriptografa uma string"""
        if not encrypted_data:
            return encrypted_data
        try:
            cipher = EncryptedField.get_cipher()
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return encrypted_data  # Retorna original se falhar (dados não criptografados)


# --- Modelos do Banco de Dados ---

class Link(db.Model):
    """
    Representa um link de rastreamento criado para investigação.
    Cada link corresponde a uma operação/investigado específico.
    """
    __tablename__ = 'link'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    destino = db.Column(db.String(500), nullable=False)
    nome_investigado = db.Column(db.String(200), index=True)  # Nome/identificação do alvo
    plataforma = db.Column(db.String(50))  # Ex: youtube, instagram, noticia
    
    # Campos para pré-visualização personalizada (Open Graph/Twitter Card)
    preview_titulo = db.Column(db.String(255))
    preview_descricao = db.Column(db.String(500))
    preview_imagem = db.Column(db.String(255))  # URL da imagem de preview
    
    created_at = db.Column(db.DateTime, default=horario_brasilia, index=True)
    foi_testado = db.Column(db.Boolean, default=False)
    
    # Campos de auditoria
    criado_por = db.Column(db.String(100))  # Usuário que criou o link
    operacao = db.Column(db.String(200))  # Nome da operação/caso
    observacoes = db.Column(db.Text)  # Notas sobre a investigação
    
    # Relacionamentos com exclusão em cascata
    ips_iniciais = db.relationship('IPInicial', backref='link_rel', lazy='dynamic', 
                                   cascade="all, delete-orphan")
    registros_acesso = db.relationship('RegistroAcesso', backref='link_rel', lazy='dynamic',
                                       cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Link slug='{self.slug}' investigado='{self.nome_investigado}' operacao='{self.operacao}'>"
    
    def to_dict(self):
        """Serializa o link para dicionário"""
        return {
            'id': self.id,
            'slug': self.slug,
            'destino': self.destino,
            'nome_investigado': self.nome_investigado,
            'plataforma': self.plataforma,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'operacao': self.operacao,
            'total_acessos': self.registros_acesso.count()
        }


class IPInicial(db.Model):
    """
    Registra o primeiro acesso de IP a um link (antes do clique/interação).
    Útil para identificar reconhecimento ou múltiplas visitas.
    """
    __tablename__ = 'ip_inicial'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), db.ForeignKey('link.slug', ondelete='CASCADE'), index=True)
    
    # IPs criptografados por segurança
    ip_v4 = db.Column(db.String(500))  # Tamanho maior para acomodar dados criptografados
    ip_v6 = db.Column(db.String(500))
    porta = db.Column(db.Integer)
    
    data_hora = db.Column(db.DateTime, default=horario_brasilia, index=True)
    
    def set_ip_v4(self, ip: str):
        """Define IP v4 com criptografia"""
        self.ip_v4 = EncryptedField.encrypt(ip) if ip else None
    
    def get_ip_v4(self) -> str:
        """Obtém IP v4 descriptografado"""
        return EncryptedField.decrypt(self.ip_v4) if self.ip_v4 else None
    
    def set_ip_v6(self, ip: str):
        """Define IP v6 com criptografia"""
        self.ip_v6 = EncryptedField.encrypt(ip) if ip else None
    
    def get_ip_v6(self) -> str:
        """Obtém IP v6 descriptografado"""
        return EncryptedField.decrypt(self.ip_v6) if self.ip_v6 else None
    
    def __repr__(self):
        return f"<IPInicial slug='{self.slug}' data='{self.data_hora}'>"


class RegistroAcesso(db.Model):
    """
    Registra dados detalhados após interação do usuário (clique, foto, etc.).
    Contém as evidências coletadas durante a investigação.
    """
    __tablename__ = 'registro_acesso'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), db.ForeignKey('link.slug', ondelete='CASCADE'), index=True)
    
    # Dados de rede (criptografados)
    ip_v4 = db.Column(db.String(500))
    ip_v6 = db.Column(db.String(500))
    ip_servidor = db.Column(db.String(500))
    porta_servidor = db.Column(db.String(10))
    porta_r = db.Column(db.String(45))  # Porta remota
    
    # Dados de localização (criptografados - informação sensível)
    latitude = db.Column(db.String(500))
    longitude = db.Column(db.String(500))
    
    # Evidências
    foto_arquivo = db.Column(db.String(255))  # Nome do arquivo da foto capturada
    
    # Dados do dispositivo/navegador
    sistema = db.Column(db.String(100))
    navegador = db.Column(db.String(200))
    idioma = db.Column(db.String(50))
    fuso_horario = db.Column(db.String(100))
    conexao = db.Column(db.String(100))  # Tipo de conexão (wifi, cellular)
    largura_tela = db.Column(db.Integer)
    altura_tela = db.Column(db.Integer)
    
    # Métricas
    tempo_segundos = db.Column(db.Integer)  # Tempo na página antes da ação
    data_hora = db.Column(db.DateTime, default=horario_brasilia, index=True)
    
    # Métodos para criptografia de campos sensíveis
    def set_ip_v4(self, ip: str):
        self.ip_v4 = EncryptedField.encrypt(ip) if ip else None
    
    def get_ip_v4(self) -> str:
        return EncryptedField.decrypt(self.ip_v4) if self.ip_v4 else None
    
    def set_ip_v6(self, ip: str):
        self.ip_v6 = EncryptedField.encrypt(ip) if ip else None
    
    def get_ip_v6(self) -> str:
        return EncryptedField.decrypt(self.ip_v6) if self.ip_v6 else None
    
    def set_latitude(self, lat: str):
        self.latitude = EncryptedField.encrypt(lat) if lat else None
    
    def get_latitude(self) -> str:
        return EncryptedField.decrypt(self.latitude) if self.latitude else None
    
    def set_longitude(self, lon: str):
        self.longitude = EncryptedField.encrypt(lon) if lon else None
    
    def get_longitude(self) -> str:
        return EncryptedField.decrypt(self.longitude) if self.longitude else None
    
    def __repr__(self):
        return f"<RegistroAcesso slug='{self.slug}' data='{self.data_hora}'>"
    
    def to_dict(self):
        """Serializa registro para dicionário (para JSON/API)"""
        return {
            'id': self.id,
            'slug': self.slug,
            'ip_v4': self.get_ip_v4(),
            'ip_v6': self.get_ip_v6(),
            'latitude': self.get_latitude(),
            'longitude': self.get_longitude(),
            'foto_arquivo': self.foto_arquivo,
            'sistema': self.sistema,
            'navegador': self.navegador,
            'idioma': self.idioma,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None
        }


class RegistroBot(db.Model):
    """
    Registra acessos identificados como bots.
    Útil para diferenciar tentativas de reconhecimento automatizado.
    """
    __tablename__ = 'registro_bot'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), index=True)
    
    ip = db.Column(db.String(500))  # Criptografado
    user_agent = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=horario_brasilia, index=True)
    
    # Dados de geolocalização (se disponível)
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    pais = db.Column(db.String(100))
    
    def set_ip(self, ip: str):
        self.ip = EncryptedField.encrypt(ip) if ip else None
    
    def get_ip(self) -> str:
        return EncryptedField.decrypt(self.ip) if self.ip else None
    
    def __repr__(self):
        return f"<RegistroBot slug='{self.slug}' data='{self.timestamp}'>"


class AuditLog(db.Model):
    """
    Log de auditoria para rastrear ações administrativas.
    Fundamental para conformidade e rastreabilidade em investigações.
    """
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False, index=True)
    acao = db.Column(db.String(100), nullable=False, index=True)  # Ex: 'criar_link', 'excluir_link', 'login', 'exportar_dados'
    detalhes = db.Column(db.Text)  # JSON com detalhes da ação
    ip_origem = db.Column(db.String(500))  # IP de quem executou a ação (criptografado)
    timestamp = db.Column(db.DateTime, default=horario_brasilia, index=True)
    
    def set_ip_origem(self, ip: str):
        self.ip_origem = EncryptedField.encrypt(ip) if ip else None
    
    def get_ip_origem(self) -> str:
        return EncryptedField.decrypt(self.ip_origem) if self.ip_origem else None
    
    def __repr__(self):
        return f"<AuditLog usuario='{self.usuario}' acao='{self.acao}' data='{self.timestamp}'>"


class Usuario(db.Model):
    """
    Modelo para usuários do sistema (futura expansão para multi-usuário).
    Por enquanto suporta apenas um admin, mas preparado para expansão.
    """
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nome_completo = db.Column(db.String(200))
    email = db.Column(db.String(200))
    
    # Controle de acesso
    ativo = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Auditoria
    criado_em = db.Column(db.DateTime, default=horario_brasilia)
    ultimo_login = db.Column(db.DateTime)
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime)  # Bloqueio temporário após muitas tentativas
    
    def __repr__(self):
        return f"<Usuario username='{self.username}' admin={self.is_admin}>"
