#!/bin/bash
# Script para adicionar issues existentes ao GitHub Project automaticamente

set -e

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🤖 Adicionando Issues ao GitHub Project Automaticamente"
echo ""

# Verificar se gh está instalado
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) não encontrado.${NC}"
    echo "Instale em: https://cli.github.com/"
    exit 1
fi

# Detectar repositório
REPO=$(git remote get-url origin 2>/dev/null | sed -E 's/.*github\.com[:/](.+)\.git/\1/' || echo "")

if [ -z "$REPO" ]; then
    echo -e "${YELLOW}⚠️  Não foi possível detectar o repositório.${NC}"
    read -p "Digite o repositório (formato: usuario/repo): " REPO
else
    echo -e "📦 Repositório: ${GREEN}$REPO${NC}"
fi

# Listar projetos
echo ""
echo "📊 Projetos disponíveis:"
gh project list --owner $(echo $REPO | cut -d'/' -f1) --format json | \
    jq -r '.projects[] | "\(.number). \(.title)"'

echo ""
read -p "Digite o NÚMERO do projeto: " PROJECT_NUMBER

# Confirmar
echo ""
echo -e "${YELLOW}⚠️  Isso adicionará TODAS as issues com label 'logpulse-ia' ao projeto #$PROJECT_NUMBER${NC}"
read -p "Deseja continuar? (s/n): " confirm

if [ "$confirm" != "s" ]; then
    echo -e "${RED}❌ Operação cancelada.${NC}"
    exit 0
fi

echo ""
echo "======================================================================"
echo "ADICIONANDO ISSUES AO PROJETO"
echo "======================================================================"
echo ""

# Obter owner do repositório
OWNER=$(echo $REPO | cut -d'/' -f1)

# Listar issues com label logpulse-ia
ISSUES=$(gh issue list --repo $REPO --label "logpulse-ia" --state open --json number --jq '.[].number')

count=0
for issue_number in $ISSUES; do
    echo -e "Adicionando issue #$issue_number..."
    
    # Adicionar issue ao projeto
    gh project item-add $PROJECT_NUMBER \
        --owner $OWNER \
        --url "https://github.com/$REPO/issues/$issue_number" 2>&1 | \
        grep -v "GraphQL" || echo "  ✅ Adicionada"
    
    count=$((count + 1))
    sleep 0.3  # Pequeno delay para não sobrecarregar API
done

echo ""
echo "======================================================================"
echo -e "${GREEN}✅ $count issues adicionadas ao projeto!${NC}"
echo ""
echo "🔗 Visualize em: https://github.com/$OWNER/projects/$PROJECT_NUMBER"
