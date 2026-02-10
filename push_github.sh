#!/bin/bash
# Script para fazer push das mudanças para o GitHub

echo "=========================================="
echo "🚀 Push para GitHub - Sistema de Rastreamento"
echo "=========================================="
echo ""

cd /home/user/webapp

echo "📊 Verificando commits a serem enviados..."
git log origin/main..HEAD --oneline
echo ""

echo "📦 Total de commits novos:"
git rev-list --count origin/main..HEAD
echo ""

echo "=========================================="
echo "Para fazer o push, execute:"
echo "=========================================="
echo ""
echo "cd /home/user/webapp"
echo "git push origin main"
echo ""
echo "Se pedir autenticação:"
echo "- Username: seu_usuario_github"
echo "- Password: seu_token_pessoal_github"
echo ""
echo "Como gerar token:"
echo "1. Acesse: https://github.com/settings/tokens"
echo "2. Clique em 'Generate new token (classic)'"
echo "3. Dê um nome (ex: 'Link Spy')"
echo "4. Marque: 'repo' (todos os subitens)"
echo "5. Clique em 'Generate token'"
echo "6. Copie o token (ghp_...)"
echo "7. Use como senha no git push"
echo ""
echo "=========================================="
