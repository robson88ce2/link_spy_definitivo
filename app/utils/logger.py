"""
Configuração de Logging Avançado
Sistema de logs com rotação e separação de logs de auditoria
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def configurar_logging(app):
    """
    Configura o sistema de logging da aplicação.
    
    Args:
        app: Instância do Flask app
    """
    # Criar diretório de logs se não existir
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Nível de log
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # Formato dos logs
    log_format = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # --- Log principal da aplicação ---
    app_log_file = app.config.get('LOG_FILE', 'logs/app.log')
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),  # 10MB
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
    )
    app_handler.setFormatter(log_format)
    app_handler.setLevel(log_level)
    
    # --- Log de auditoria (separado) ---
    audit_log_file = app.config.get('AUDIT_LOG_FILE', 'logs/audit.log')
    audit_handler = logging.handlers.RotatingFileHandler(
        audit_log_file,
        maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
    )
    audit_format = logging.Formatter(
        '[%(asctime)s] AUDIT - %(message)s'
    )
    audit_handler.setFormatter(audit_format)
    audit_handler.setLevel(logging.INFO)
    
    # --- Console handler (para desenvolvimento) ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(log_level)
    
    # Configurar logger do Flask
    app.logger.setLevel(log_level)
    app.logger.addHandler(app_handler)
    app.logger.addHandler(console_handler)
    
    # Logger específico para auditoria
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_handler)
    audit_logger.addHandler(console_handler)
    
    # Evitar propagação para o root logger
    audit_logger.propagate = False
    
    # Log de inicialização
    app.logger.info("=" * 80)
    app.logger.info("🚀 Sistema de Rastreamento para Investigações - Iniciado")
    app.logger.info(f"Ambiente: {app.config.get('ENV', 'production')}")
    app.logger.info(f"Debug: {app.debug}")
    app.logger.info(f"Nível de Log: {logging.getLevelName(log_level)}")
    app.logger.info("=" * 80)


def log_auditoria(usuario: str, acao: str, detalhes: str = "", ip: str = ""):
    """
    Registra uma ação no log de auditoria.
    
    Args:
        usuario: Username do usuário
        acao: Ação executada
        detalhes: Detalhes adicionais
        ip: IP de origem
    """
    audit_logger = logging.getLogger('audit')
    
    mensagem_partes = [f"Usuario: {usuario}", f"Acao: {acao}"]
    
    if ip:
        mensagem_partes.append(f"IP: {ip}")
    
    if detalhes:
        mensagem_partes.append(f"Detalhes: {detalhes}")
    
    mensagem = " | ".join(mensagem_partes)
    audit_logger.info(mensagem)


def log_acesso_rastreamento(slug: str, ip: str, tipo: str, detalhes: str = ""):
    """
    Registra acesso a um link de rastreamento.
    
    Args:
        slug: Slug do link acessado
        ip: IP do visitante
        tipo: Tipo de acesso (bot, usuario, ip_inicial)
        detalhes: Informações adicionais
    """
    app_logger = logging.getLogger('flask.app')
    
    mensagem = f"RASTREAMENTO | Slug: {slug} | IP: {ip} | Tipo: {tipo}"
    if detalhes:
        mensagem += f" | {detalhes}"
    
    app_logger.info(mensagem)


def log_erro_seguranca(mensagem: str, detalhes: dict = None):
    """
    Registra um evento de segurança (tentativa de ataque, etc).
    
    Args:
        mensagem: Mensagem descritiva
        detalhes: Dicionário com detalhes do evento
    """
    app_logger = logging.getLogger('flask.app')
    
    log_msg = f"⚠️ SEGURANÇA: {mensagem}"
    if detalhes:
        log_msg += f" | Detalhes: {detalhes}"
    
    app_logger.warning(log_msg)
