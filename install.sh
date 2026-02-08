#!/bin/bash
# Script de instalação rápida - Sistema de Rastreamento para Investigações

echo "=========================================="
echo "🔍 Sistema de Rastreamento - Instalação"
echo "=========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado! Instale Python 3.8+ e tente novamente."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"
echo ""

# Criar ambiente virtual
echo "📦 Criando ambiente virtual..."
python3 -m venv venv

# Ativar ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Gerar chaves
echo ""
echo "🔑 Gerando chaves secretas..."
python gerar_chaves.py

# Criar .env
echo ""
echo "📝 Criando arquivo .env..."
if [ -f .env ]; then
    echo "⚠️  Arquivo .env já existe. Pulando..."
else
    cp .env.example .env
    echo "✅ Arquivo .env criado! EDITE-O com as chaves geradas acima."
fi

# Criar diretórios necessários
echo ""
echo "📁 Criando diretórios..."
mkdir -p logs
mkdir -p instance
mkdir -p static/upload
mkdir -p static/previews

echo ""
echo "=========================================="
echo "✅ Instalação concluída!"
echo "=========================================="
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Edite o arquivo .env e configure:"
echo "   - SECRET_KEY (cole a chave gerada acima)"
echo "   - ENCRYPTION_KEY (cole a chave gerada acima)"
echo "   - ADMIN_PASSWORD (defina uma senha forte)"
echo ""
echo "2. Inicialize o banco de dados:"
echo "   flask db init"
echo "   flask db migrate -m 'Initial migration'"
echo "   flask db upgrade"
echo ""
echo "3. Execute o sistema:"
echo "   python app.py"
echo ""
echo "=========================================="
