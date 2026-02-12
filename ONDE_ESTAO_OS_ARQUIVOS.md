# 📁 GUIA DE ACESSO AOS ARQUIVOS DO PROJETO

## 📍 **LOCALIZAÇÃO DOS ARQUIVOS**

**Diretório Principal:** `/home/user/webapp`

---

## 🗂️ **ESTRUTURA COMPLETA DE ARQUIVOS**

### **📋 Arquivos de Documentação (Principais)**

```
/home/user/webapp/
├── RESUMO_FINAL.txt              ⭐ RESUMO COMPLETO DE TUDO
├── GUIA_TESTES_E_DEPLOY.md       ⭐ COMO TESTAR E FAZER DEPLOY
├── README.md                     ⭐ DOCUMENTAÇÃO PRINCIPAL
├── MELHORIAS_IMPLEMENTADAS.md     📝 Detalhamento técnico
```

### **💻 Arquivos de Código (Principais)**

```
/home/user/webapp/
├── app.py                        ⭐ APLICAÇÃO PRINCIPAL (NOVA)
├── config.py                     ⚙️  Configurações do sistema
├── requirements.txt              📦 Dependências Python
├── .env                          🔒 Variáveis de ambiente (segredo)
├── .env.example                  📄 Exemplo de configuração
```

### **🎨 Templates Redesenhados**

```
/home/user/webapp/templates/
├── youtube.html                  ⭐ REDESENHADO
├── instagram.html                ⭐ REDESENHADO
├── tiktok.html                   ⭐ REDESENHADO
├── facebook.html
├── googledrive.html
├── kwai.html
├── mercadopago.html
├── noticia.html
└── ... (outros templates administrativos)
```

### **🔧 Arquivos de Utilitários**

```
/home/user/webapp/
├── gerar_chaves.py               🔑 Gera chaves secretas
├── push_github.sh                📤 Script auxiliar de push
├── install.sh                    🚀 Script de instalação
```

### **📂 Módulos do Sistema**

```
/home/user/webapp/app/
├── models.py                     💾 Modelos do banco com criptografia
├── services/
│   └── auth_service.py          🔐 Serviço de autenticação
├── utils/
│   ├── validators.py            ✅ Validações
│   └── logger.py                📊 Sistema de logs
```

### **📁 Diretórios de Dados**

```
/home/user/webapp/
├── static/
│   ├── upload/                  📸 Fotos capturadas (evidências)
│   └── previews/                🖼️  Imagens de preview
├── logs/                        📝 Logs da aplicação
├── instance/                    💾 Banco de dados SQLite
```

---

## 🔍 **COMO ACESSAR OS ARQUIVOS**

### **Opção 1: Via Terminal (Linux/Mac)**

```bash
# Navegar para o diretório
cd /home/user/webapp

# Listar arquivos
ls -lah

# Ver conteúdo de um arquivo
cat RESUMO_FINAL.txt

# Editar arquivo
nano app.py
# ou
vim app.py
```

### **Opção 2: Via Navegador de Arquivos (Linux/Mac)**

1. Abra o **Gerenciador de Arquivos**
2. Navegue para: `/home/user/webapp`
3. Clique duplo para abrir arquivos

### **Opção 3: Via VS Code / Editor**

```bash
# Abrir projeto no VS Code
cd /home/user/webapp
code .

# Ou abrir arquivo específico
code app.py
```

### **Opção 4: Via FTP/SFTP (Servidor Remoto)**

```
Host: seu_servidor.com
Porta: 22 (SSH/SFTP)
Usuário: seu_usuario
Caminho: /home/user/webapp
```

---

## 📖 **ARQUIVOS MAIS IMPORTANTES PARA LER**

### **1. RESUMO_FINAL.txt** 🌟
**O que é:** Resumo executivo completo de tudo
**Como ver:**
```bash
cat /home/user/webapp/RESUMO_FINAL.txt
```

### **2. GUIA_TESTES_E_DEPLOY.md** 🧪
**O que é:** Instruções completas de testes e deploy
**Como ver:**
```bash
cat /home/user/webapp/GUIA_TESTES_E_DEPLOY.md
```

### **3. README.md** 📚
**O que é:** Documentação principal do sistema
**Como ver:**
```bash
cat /home/user/webapp/README.md
```

### **4. app.py** 💻
**O que é:** Código principal da aplicação (NOVO e SEGURO)
**Como ver:**
```bash
# Ver primeiras 50 linhas
head -50 /home/user/webapp/app.py

# Ver arquivo completo
cat /home/user/webapp/app.py

# Editar
nano /home/user/webapp/app.py
```

### **5. config.py** ⚙️
**O que é:** Configurações do sistema por ambiente
**Como ver:**
```bash
cat /home/user/webapp/config.py
```

---

## 🎨 **VISUALIZAR TEMPLATES REDESENHADOS**

### **YouTube Template**
```bash
cat /home/user/webapp/templates/youtube.html
```

### **Instagram Template**
```bash
cat /home/user/webapp/templates/instagram.html
```

### **TikTok Template**
```bash
cat /home/user/webapp/templates/tiktok.html
```

---

## 📊 **VERIFICAR STATUS DO GIT**

```bash
cd /home/user/webapp

# Ver commits prontos para push
git log --oneline -6

# Ver status atual
git status

# Ver diferenças
git diff
```

---

## 📦 **COMANDOS ÚTEIS**

### **Ver Estrutura de Diretórios**
```bash
cd /home/user/webapp
tree -L 2
# ou
ls -R
```

### **Buscar Arquivo Específico**
```bash
cd /home/user/webapp
find . -name "*.py" -type f
```

### **Ver Tamanho dos Arquivos**
```bash
cd /home/user/webapp
du -sh *
```

### **Contar Linhas de Código**
```bash
cd /home/user/webapp
find . -name "*.py" -exec wc -l {} + | tail -1
```

---

## 🔒 **ARQUIVOS QUE NÃO DEVEM SER COMPARTILHADOS**

⚠️ **NUNCA compartilhe estes arquivos:**

- `.env` - Contém senhas e chaves secretas
- `instance/dados.db` - Banco de dados com informações sensíveis
- `static/upload/*.jpg` - Fotos capturadas (evidências)
- `logs/*.log` - Logs com IPs e dados

Estes arquivos já estão no `.gitignore` e não vão para o GitHub.

---

## 📤 **EXPORTAR ARQUIVOS**

### **Copiar para Área de Transferência**
```bash
# Linux (com xclip)
cat /home/user/webapp/RESUMO_FINAL.txt | xclip -selection clipboard

# Mac
cat /home/user/webapp/RESUMO_FINAL.txt | pbcopy
```

### **Criar Backup ZIP**
```bash
cd /home/user
tar -czf webapp_backup.tar.gz webapp/
# Arquivo criado: /home/user/webapp_backup.tar.gz
```

### **Copiar para Outro Local**
```bash
# Copiar diretório completo
cp -r /home/user/webapp /caminho/destino/

# Copiar apenas código (sem venv e cache)
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='.git' /home/user/webapp/ /destino/
```

---

## 🌐 **ACESSAR VIA NAVEGADOR (Quando o Servidor Estiver Rodando)**

### **Iniciar Servidor**
```bash
cd /home/user/webapp
python app.py
```

### **Acessar no Navegador**
- **Local:** http://localhost:5000
- **Rede Local:** http://SEU_IP:5000
- **Produção:** https://seu-dominio.com

---

## 📱 **ACESSAR VIA SSH (Servidor Remoto)**

```bash
# Conectar via SSH
ssh usuario@seu_servidor.com

# Navegar para o projeto
cd /home/user/webapp

# Ver arquivos
ls -lah

# Baixar arquivo específico para sua máquina
scp usuario@servidor:/home/user/webapp/RESUMO_FINAL.txt ~/Desktop/
```

---

## 🔍 **LOCALIZAR ARQUIVOS ESPECÍFICOS**

### **Onde está o código principal?**
```
/home/user/webapp/app.py
```

### **Onde estão os templates redesenhados?**
```
/home/user/webapp/templates/youtube.html
/home/user/webapp/templates/instagram.html
/home/user/webapp/templates/tiktok.html
```

### **Onde está a documentação?**
```
/home/user/webapp/README.md
/home/user/webapp/RESUMO_FINAL.txt
/home/user/webapp/GUIA_TESTES_E_DEPLOY.md
```

### **Onde estão as chaves e configurações?**
```
/home/user/webapp/.env
/home/user/webapp/config.py
```

### **Onde ficam os dados coletados?**
```
/home/user/webapp/instance/dados.db (banco de dados)
/home/user/webapp/static/upload/ (fotos)
/home/user/webapp/logs/ (logs)
```

---

## 🎯 **AÇÕES RÁPIDAS**

### **Ver Resumo Completo**
```bash
cat /home/user/webapp/RESUMO_FINAL.txt | less
```

### **Ver Últimas Mudanças**
```bash
cd /home/user/webapp
git log --stat -5
```

### **Ver Arquivo Específico do Último Commit**
```bash
cd /home/user/webapp
git show HEAD:app.py
```

### **Comparar Versão Nova vs Antiga do app.py**
```bash
cd /home/user/webapp
diff app_old.py app.py
```

---

## 📋 **CHECKLIST DE ACESSO**

- [ ] Localizar diretório: `/home/user/webapp`
- [ ] Ler RESUMO_FINAL.txt
- [ ] Verificar commits: `git log --oneline -6`
- [ ] Testar aplicação: `python app.py`
- [ ] Fazer push: `git push origin main`

---

## 🆘 **PROBLEMAS DE ACESSO?**

### **Não consigo acessar /home/user/webapp**
```bash
# Verificar se está no diretório certo
pwd

# Ir para o diretório
cd /home/user/webapp

# Se não existir, clonar do GitHub
git clone https://github.com/robson88ce2/link_spy_definitivo.git webapp
```

### **Não consigo ver arquivos ocultos (.env, .gitignore)**
```bash
# Listar TODOS os arquivos (incluindo ocultos)
ls -lah
```

### **Não tenho permissão para acessar**
```bash
# Verificar proprietário
ls -lah /home/user/webapp

# Ajustar permissões (se necessário)
sudo chown -R $USER:$USER /home/user/webapp
```

---

## 🎊 **ARQUIVOS CRIADOS/MODIFICADOS**

**Total:** 25+ arquivos

**Principais:**
1. ✅ app.py (completamente reescrito)
2. ✅ config.py (novo)
3. ✅ app/models.py (novo com criptografia)
4. ✅ app/services/auth_service.py (novo)
5. ✅ app/utils/validators.py (novo)
6. ✅ app/utils/logger.py (novo)
7. ✅ templates/youtube.html (redesenhado)
8. ✅ templates/instagram.html (redesenhado)
9. ✅ templates/tiktok.html (redesenhado)
10. ✅ README.md (atualizado)
11. ✅ RESUMO_FINAL.txt (novo)
12. ✅ GUIA_TESTES_E_DEPLOY.md (novo)

---

**📍 Todos os arquivos estão em:** `/home/user/webapp`

**🔗 Repositório GitHub:** https://github.com/robson88ce2/link_spy_definitivo

**✅ Pronto para usar!**
