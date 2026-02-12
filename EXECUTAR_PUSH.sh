#!/bin/bash

# ==============================================
# 🚀 SCRIPT DE PUSH AUTOMÁTICO PARA GITHUB
# ==============================================
# Repositório: link_spy_definitivo
# Autor: Sistema de Investigação
# Data: 2026-02-12
# ==============================================

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     🚀 PUSH PARA GITHUB - Sistema de Investigação   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Verificar se estamos no diretório correto
if [ ! -d ".git" ]; then
    echo "❌ ERRO: Este não é um repositório Git!"
    echo "   Execute este script em: /home/user/webapp"
    exit 1
fi

# Mostrar commits pendentes
echo "📦 COMMITS PRONTOS PARA ENVIAR:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git log --oneline origin/main..HEAD 2>/dev/null || git log --oneline -8
echo ""

# Verificar branch
BRANCH=$(git branch --show-current)
echo "📍 Branch atual: $BRANCH"
echo ""

# Perguntar confirmação
echo "❓ Deseja continuar com o push?"
echo "   [S] Sim, fazer push agora"
echo "   [N] Não, cancelar"
echo ""
read -p "   Escolha (S/N): " CONFIRM

if [ "$CONFIRM" != "S" ] && [ "$CONFIRM" != "s" ]; then
    echo ""
    echo "❌ Push cancelado pelo usuário."
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 AUTENTICAÇÃO GITHUB"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "ℹ️  Você precisará fornecer suas credenciais do GitHub:"
echo ""
echo "   👤 Username: robson88ce2"
echo "   🔑 Password: Seu Personal Access Token (ghp_...)"
echo ""
echo "📝 Como gerar o token:"
echo "   1. Acesse: https://github.com/settings/tokens"
echo "   2. Clique em 'Generate new token (classic)'"
echo "   3. Marque a opção: ✓ repo"
echo "   4. Copie o token gerado (ghp_...)"
echo ""
read -p "   Pressione ENTER quando estiver pronto..."

echo ""
echo "🚀 Iniciando push para origin/$BRANCH..."
echo ""

# Fazer o push
git push origin "$BRANCH"

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ PUSH REALIZADO COM SUCESSO!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📍 Acesse seu repositório:"
    echo "   👉 https://github.com/robson88ce2/link_spy_definitivo"
    echo ""
    echo "✅ Arquivos enviados:"
    echo "   • Código completo com segurança integrada"
    echo "   • Templates redesenhados (YouTube, Instagram, TikTok)"
    echo "   • Documentação completa"
    echo "   • Scripts de instalação e deploy"
    echo "   • Guias de testes e configuração"
    echo ""
    echo "🎯 Próximos passos:"
    echo "   1. Verificar commits no GitHub"
    echo "   2. Testar o sistema localmente"
    echo "   3. Configurar variáveis de ambiente"
    echo "   4. Fazer deploy em produção"
    echo ""
    echo "🎊 Sistema 100% pronto para investigações!"
    echo ""
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ ERRO NO PUSH"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "💡 Possíveis soluções:"
    echo ""
    echo "1️⃣  Verificar autenticação:"
    echo "   • Token correto (começa com ghp_)?"
    echo "   • Token não expirado?"
    echo "   • Permissões 'repo' marcadas?"
    echo ""
    echo "2️⃣  Gerar novo token:"
    echo "   • https://github.com/settings/tokens"
    echo "   • Generate new token (classic)"
    echo "   • Marcar: ✓ repo"
    echo ""
    echo "3️⃣  Sincronizar com remote:"
    echo "   git pull origin main --rebase"
    echo "   git push origin main"
    echo ""
    echo "4️⃣  Push com força (cuidado!):"
    echo "   git push -f origin main"
    echo ""
    echo "📖 Leia o guia completo:"
    echo "   cat PUSH_GITHUB_MANUAL.md"
    echo ""
    exit 1
fi
