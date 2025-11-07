#!/bin/bash

# 🚀 Script de Deploy Rápido - Ceci VM
# Execute na VM após clonar o repo

set -e  # Para se houver erro

echo "🚀 Iniciando deploy do Ceci..."

# 1. Atualiza repo
echo "📦 Atualizando código..."
git pull origin main

# 2. Ativa venv
echo "🐍 Ativando ambiente Python..."
source venv/bin/activate

# 3. Atualiza dependências
echo "📚 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements-lock.txt

# 4. Garante diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p reports
mkdir -p .cache
chmod 755 reports

# 5. Verifica .env
if [ ! -f .env ]; then
    echo "⚠️  ATENÇÃO: Arquivo .env não encontrado!"
    echo "Crie um arquivo .env com:"
    echo "OPENAI_API_KEY=sk-proj-..."
    exit 1
fi

# 6. Reinicia serviço
echo "🔄 Reiniciando serviço..."
sudo supervisorctl restart ceci

# 7. Aguarda 2s
sleep 2

# 8. Verifica status
echo "✅ Verificando status..."
sudo supervisorctl status ceci

# 9. Testa health
echo "🏥 Testando /health..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Health check falhou"

echo ""
echo "🎉 Deploy concluído!"
echo ""
echo "📊 Comandos úteis:"
echo "  - Logs: sudo tail -f /var/log/ceci/error.log"
echo "  - Status: sudo supervisorctl status ceci"
echo "  - Restart: sudo supervisorctl restart ceci"
