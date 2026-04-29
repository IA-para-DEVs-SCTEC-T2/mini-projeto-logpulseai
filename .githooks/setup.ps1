# Script para configurar os Git Hooks locais no Windows
# Execute este script uma vez para ativar as validações locais

Write-Host "🔧 Configurando Git Hooks locais..." -ForegroundColor Cyan
Write-Host ""

# Configura o diretório de hooks do Git para usar .githooks
git config core.hooksPath .githooks

Write-Host "✅ Git Hooks configurados com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "📋 HOOKS ATIVADOS:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "  ✅ commit-msg  → Valida mensagens de commit" -ForegroundColor Green
Write-Host "  ✅ pre-push    → Valida nome da branch antes do push" -ForegroundColor Green
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 Agora as validações acontecerão LOCALMENTE:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  • Commits inválidos serão bloqueados"
Write-Host "  • Push de branches inválidas será bloqueado"
Write-Host "  • Você verá mensagens de erro antes de enviar ao GitHub"
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
