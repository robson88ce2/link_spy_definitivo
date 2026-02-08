"""
Configurações do Sistema de Rastreamento para Investigações
Arquivo de configuração centralizado e seguro
"""
import os
import secrets
from datetime import timedelta


class Config:
    """Configurações base para todas as ambientes"""
    
    # ===== SEGURANÇA =====
    # Secret key para sessões - NUNCA commitar valor real
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Proteção CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Token nunca expira (útil para investigações longas)
    
    # Sessão segura
    SESSION_COOKIE_SECURE = True  # Apenas HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Não acessível via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Proteção CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Sessão de 24h
    
    # ===== BANCO DE DADOS =====
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'instance', 'dados.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Não mostrar queries SQL (segurança)
    
    # ===== UPLOAD DE ARQUIVOS =====
    # Pasta para imagens de preview (Open Graph)
    PREVIEW_UPLOAD_FOLDER = 'static/previews'
    # Pasta para fotos capturadas (evidências)
    CAPTURE_UPLOAD_FOLDER = 'static/upload'
    # Extensões permitidas
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    # Limite de tamanho de upload (10MB)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    # ===== PROCESSAMENTO DE IMAGENS =====
    MAX_IMAGE_SIZE = (1200, 1200)  # Redimensionar para economizar espaço
    IMAGE_QUALITY = 85  # Qualidade JPEG (0-100)
    IMAGE_FORMAT = "JPEG"
    
    # ===== RASTREAMENTO =====
    # User agents de bots para detecção
    BOT_USER_AGENTS = [
        'facebookexternalhit',
        'twitterbot', 
        'linkedinbot',
        'whatsapp',
        'slackbot',
        'telegrambot',
        'discordbot',
        'instagram'
    ]
    
    # Timeout para requisições externas (em segundos)
    REQUEST_TIMEOUT = 10
    
    # Tamanho padrão do slug gerado
    DEFAULT_SLUG_LENGTH = 8
    
    # ===== AUTENTICAÇÃO =====
    # Número máximo de tentativas de login antes de bloquear temporariamente
    MAX_LOGIN_ATTEMPTS = 5
    # Tempo de bloqueio após muitas tentativas (em minutos)
    LOGIN_BLOCK_TIME = 15
    
    # ===== LOGS E AUDITORIA =====
    # Nível de log
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    # Arquivo de log
    LOG_FILE = 'logs/app.log'
    # Arquivo de log de auditoria (ações administrativas)
    AUDIT_LOG_FILE = 'logs/audit.log'
    # Tamanho máximo do arquivo de log (10MB)
    LOG_MAX_BYTES = 10 * 1024 * 1024
    # Número de backups de log
    LOG_BACKUP_COUNT = 5
    
    # ===== CRIPTOGRAFIA =====
    # Chave para criptografar dados sensíveis no banco
    # DEVE ser definida via variável de ambiente em produção
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    
    # ===== TIMEZONE =====
    TIMEZONE = 'America/Sao_Paulo'  # Fuso horário padrão (Brasília)


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento"""
    DEBUG = True
    TESTING = False
    
    # Em dev, permitir HTTP (não apenas HTTPS)
    SESSION_COOKIE_SECURE = False
    
    # Mostrar queries SQL em desenvolvimento
    SQLALCHEMY_ECHO = False  # Manter False para não poluir logs


class ProductionConfig(Config):
    """Configurações para ambiente de produção"""
    DEBUG = False
    TESTING = False
    
    # Em produção, forçar HTTPS
    SESSION_COOKIE_SECURE = True
    
    # Validações obrigatórias para produção
    @classmethod
    def init_app(cls, app):
        """Valida configurações críticas antes de iniciar"""
        # Validar SECRET_KEY
        if not os.environ.get('SECRET_KEY'):
            raise ValueError(
                "❌ ERRO CRÍTICO: SECRET_KEY não definida! "
                "Defina a variável de ambiente SECRET_KEY antes de executar em produção."
            )
        
        # Validar ENCRYPTION_KEY
        if not os.environ.get('ENCRYPTION_KEY'):
            raise ValueError(
                "❌ ERRO CRÍTICO: ENCRYPTION_KEY não definida! "
                "Defina a variável de ambiente ENCRYPTION_KEY antes de executar em produção."
            )
        
        # Avisar sobre banco de dados
        if 'sqlite' in cls.SQLALCHEMY_DATABASE_URI:
            app.logger.warning(
                "⚠️ AVISO: Usando SQLite em produção. "
                "Recomenda-se usar PostgreSQL ou MySQL para produção."
            )


class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    DEBUG = True
    
    # Banco em memória para testes
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Desabilitar CSRF em testes
    WTF_CSRF_ENABLED = False
    
    # Cookies não-secure para testes
    SESSION_COOKIE_SECURE = False


# Dicionário para facilitar seleção de config
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Retorna a configuração apropriada baseada no ambiente.
    
    Args:
        config_name: Nome da configuração ('development', 'production', 'testing')
                    Se None, usa a variável de ambiente FLASK_ENV
    
    Returns:
        Classe de configuração apropriada
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_by_name.get(config_name, DevelopmentConfig)
