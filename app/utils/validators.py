"""
Utilitários de Validação e Helpers
Funções auxiliares para validação de dados e sanitização
"""
import re
import validators
from urllib.parse import urlparse
from typing import Optional, Tuple
import string
import random


def validar_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Valida se uma URL é válida e segura.
    
    Args:
        url: URL para validar
        
    Returns:
        Tupla (valido, mensagem_erro)
    """
    if not url:
        return False, "URL não pode ser vazia"
    
    # Valida formato básico
    if not validators.url(url):
        return False, "Formato de URL inválido"
    
    # Parse da URL
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Erro ao processar URL"
    
    # Bloquear URLs locais/privadas (segurança)
    hostnames_bloqueados = [
        'localhost', '127.0.0.1', '0.0.0.0', '::1',
        '10.', '172.16.', '172.17.', '172.18.', '172.19.',
        '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
        '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
        '172.30.', '172.31.', '192.168.'
    ]
    
    hostname = parsed.hostname or ''
    for bloqueado in hostnames_bloqueados:
        if hostname.startswith(bloqueado):
            return False, "URLs de rede local não são permitidas"
    
    # Deve ter esquema http ou https
    if parsed.scheme not in ['http', 'https']:
        return False, "URL deve usar protocolo HTTP ou HTTPS"
    
    return True, None


def validar_slug(slug: str) -> Tuple[bool, Optional[str]]:
    """
    Valida um slug personalizado.
    
    Args:
        slug: Slug para validar
        
    Returns:
        Tupla (valido, mensagem_erro)
    """
    if not slug:
        return False, "Slug não pode ser vazio"
    
    # Tamanho
    if len(slug) < 3:
        return False, "Slug deve ter no mínimo 3 caracteres"
    
    if len(slug) > 100:
        return False, "Slug deve ter no máximo 100 caracteres"
    
    # Apenas caracteres alfanuméricos, hífen e underscore
    if not re.match(r'^[a-zA-Z0-9_-]+$', slug):
        return False, "Slug deve conter apenas letras, números, hífen (-) e underscore (_)"
    
    # Não pode começar ou terminar com hífen ou underscore
    if slug.startswith(('-', '_')) or slug.endswith(('-', '_')):
        return False, "Slug não pode começar ou terminar com hífen ou underscore"
    
    # Slugs reservados (rotas do sistema)
    slugs_reservados = [
        'admin', 'api', 'static', 'login', 'logout', 'gerenciar',
        'painel', 'criar_link', 'excluir_link', 'upload_imagem',
        'coletar_ip_inicial', 'coletar_dados', 'redir', 'ping',
        'info_servidor', 'todos_links'
    ]
    
    if slug.lower() in slugs_reservados:
        return False, f"Slug '{slug}' é reservado pelo sistema"
    
    return True, None


def gerar_slug(tamanho: int = 8) -> str:
    """
    Gera um slug alfanumérico aleatório.
    
    Args:
        tamanho: Tamanho do slug (padrão: 8)
        
    Returns:
        Slug gerado
    """
    # Usa apenas letras maiúsculas, minúsculas e números
    # Evita caracteres ambíguos (0, O, l, I)
    caracteres = string.ascii_letters + string.digits
    caracteres = caracteres.replace('0', '').replace('O', '').replace('l', '').replace('I', '')
    
    return ''.join(random.choices(caracteres, k=tamanho))


def extensao_permitida(nome_arquivo: str, extensoes_permitidas: set = None) -> bool:
    """
    Verifica se a extensão do arquivo é permitida para upload.
    
    Args:
        nome_arquivo: Nome do arquivo
        extensoes_permitidas: Set de extensões permitidas (opcional)
        
    Returns:
        True se extensão permitida, False caso contrário
    """
    if extensoes_permitidas is None:
        extensoes_permitidas = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    return '.' in nome_arquivo and \
           nome_arquivo.rsplit('.', 1)[1].lower() in extensoes_permitidas


def sanitizar_filename(filename: str) -> str:
    """
    Sanitiza nome de arquivo removendo caracteres perigosos.
    
    Args:
        filename: Nome do arquivo original
        
    Returns:
        Nome do arquivo sanitizado
    """
    # Remove caracteres perigosos
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    # Remove múltiplos espaços
    filename = re.sub(r'\s+', '_', filename)
    # Remove pontos múltiplos (exceto extensão)
    partes = filename.rsplit('.', 1)
    if len(partes) == 2:
        nome, ext = partes
        nome = nome.replace('.', '_')
        filename = f"{nome}.{ext}"
    
    return filename[:255]  # Limita tamanho


def analisar_user_agent(user_agent: str) -> dict:
    """
    Analisa o User-Agent e extrai informações sobre o dispositivo.
    Versão simplificada - para produção, considere usar biblioteca especializada.
    
    Args:
        user_agent: String do User-Agent
        
    Returns:
        Dicionário com informações do dispositivo
    """
    if not user_agent:
        return {
            "sistema": "Desconhecido",
            "dispositivo": "Desconhecido",
            "navegador": "Desconhecido"
        }
    
    ua_lower = user_agent.lower()
    sistema = "Desconhecido"
    dispositivo = "Desconhecido"
    navegador = "Desconhecido"
    
    # Detectar Sistema Operacional e Dispositivo
    if "android" in ua_lower:
        sistema_match = re.search(r"android[\s/][\d\.]+", ua_lower)
        sistema = sistema_match.group(0).replace("android", "Android") if sistema_match else "Android"
        dispositivo_match = re.search(r";\s?([^;]*)\sbuild", ua_lower)
        dispositivo = dispositivo_match.group(1).strip() if dispositivo_match else "Android genérico"
    elif "iphone" in ua_lower:
        sistema = "iOS"
        dispositivo = "iPhone"
    elif "ipad" in ua_lower:
        sistema = "iOS"
        dispositivo = "iPad"
    elif "windows" in ua_lower:
        sistema_match = re.search(r"windows nt [\d\.]+", ua_lower)
        sistema = sistema_match.group(0).replace("windows nt", "Windows") if sistema_match else "Windows"
        dispositivo = "PC"
    elif "macintosh" in ua_lower or "mac os x" in ua_lower:
        sistema = "macOS"
        dispositivo = "Mac"
    elif "linux" in ua_lower:
        sistema = "Linux"
        dispositivo = "PC/Dispositivo"
    elif "x11" in ua_lower:
        dispositivo = "Unix/Linux"
    
    # Detectar Navegador (ordem importa)
    if "edg" in ua_lower:
        navegador_match = re.search(r"edg\/[\d\.]+", ua_lower)
        navegador = navegador_match.group(0).replace("edg", "Edge") if navegador_match else "Edge"
    elif "chrome" in ua_lower and "safari" in ua_lower:
        navegador_match = re.search(r"chrome\/[\d\.]+", ua_lower)
        navegador = navegador_match.group(0).replace("chrome", "Chrome") if navegador_match else "Chrome"
    elif "firefox" in ua_lower:
        navegador_match = re.search(r"firefox\/[\d\.]+", ua_lower)
        navegador = navegador_match.group(0).replace("firefox", "Firefox") if navegador_match else "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        navegador_match = re.search(r"version\/[\d\.]+ safari", ua_lower)
        navegador = navegador_match.group(0).replace("version", "Safari").replace("safari", "").strip() if navegador_match else "Safari"
    elif "opr" in ua_lower or "opera" in ua_lower:
        navegador_match = re.search(r"opr\/[\d\.]+", ua_lower) or re.search(r"opera\/[\d\.]+", ua_lower)
        navegador = navegador_match.group(0).replace("opr", "Opera").replace("opera", "Opera") if navegador_match else "Opera"
    elif "msie" in ua_lower or "trident" in ua_lower:
        navegador = "Internet Explorer"
    
    return {
        "sistema": sistema,
        "dispositivo": dispositivo,
        "navegador": navegador
    }


def detectar_bot(user_agent: str, bots_lista: list = None) -> bool:
    """
    Detecta se o User-Agent é de um bot.
    
    Args:
        user_agent: String do User-Agent
        bots_lista: Lista personalizada de bots (opcional)
        
    Returns:
        True se for bot, False caso contrário
    """
    if not user_agent:
        return False
    
    if bots_lista is None:
        bots_lista = [
            'facebookexternalhit', 'twitterbot', 'linkedinbot',
            'whatsapp', 'slackbot', 'telegrambot', 'discordbot',
            'instagram', 'pinterestbot', 'redditbot'
        ]
    
    ua_lower = user_agent.lower()
    return any(bot in ua_lower for bot in bots_lista)


def formatar_coordenadas(latitude: str, longitude: str) -> str:
    """
    Formata coordenadas geográficas para exibição.
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        String formatada com link para Google Maps
    """
    if not latitude or not longitude:
        return "Coordenadas não disponíveis"
    
    try:
        lat = float(latitude)
        lon = float(longitude)
        return f"{lat:.6f}, {lon:.6f}"
    except (ValueError, TypeError):
        return f"{latitude}, {longitude}"


def gerar_link_google_maps(latitude: str, longitude: str) -> Optional[str]:
    """
    Gera link do Google Maps para coordenadas.
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        URL do Google Maps ou None se inválido
    """
    if not latitude or not longitude:
        return None
    
    try:
        lat = float(latitude)
        lon = float(longitude)
        return f"https://www.google.com/maps?q={lat},{lon}"
    except (ValueError, TypeError):
        return None
