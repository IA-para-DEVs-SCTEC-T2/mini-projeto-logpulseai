#!/bin/bash

# Script para configurar os Git Hooks locais
# Execute este script uma vez para ativar as validações locais

echo "🔧 Configurando Git Hooks locais..."
echo ""

# Configura o diretório de hooks do Git para usar .githooks
git config core.hooksPath .githooks

# Torna os hooks executáveis (necessário no Linux/macOS)
chmod +x .githooks/commit-msg
chmod +x .githooks/pre-push

echo "✅ Git Hooks configurados com sucesso!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 HOOKS ATIVADOS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✅ commit-msg  → Valida mensagens de commit"
echo "  ✅ pre-push    → Valida nome da branch antes do push"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 Agora as validações acontecerão LOCALMENTE:"
echo ""
echo "  • Commits inválidos serão bloqueados"
echo "  • Push de branches inválidas será bloqueado"
echo "  • Você verá mensagens de erro antes de enviar ao GitHub"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
