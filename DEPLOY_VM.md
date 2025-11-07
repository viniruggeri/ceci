# 🚀 Deploy Ceci na VM Azure

## 📋 Pré-requisitos

- VM Ubuntu 20.04+ rodando
- Acesso SSH à VM
- Domínio/IP público configurado
- Porta 80/443 liberada no firewall

---

## ⚡ Deploy Rápido (Copy-Paste)

### **1. Conecta na VM**

```bash
ssh seu-usuario@IP_DA_VM
```

### **2. Instala dependências do sistema**

```bash
# Atualiza sistema
sudo apt update && sudo apt upgrade -y

# Instala Python 3.12+ e ferramentas
sudo apt install -y python3.12 python3.12-venv python3-pip nginx supervisor git

# Instala certbot (SSL grátis)
sudo apt install -y certbot python3-certbot-nginx
```

### **3. Clona o repositório**

```bash
# Cria diretório de apps
sudo mkdir -p /var/www
cd /var/www

# Clona repo
sudo git clone https://github.com/viniruggeri/mini_ceciV2_mcp.git ceci
cd ceci

# Ajusta permissões
sudo chown -R $USER:$USER /var/www/ceci
```

### **4. Configura ambiente Python**

```bash
# Cria venv
python3.12 -m venv venv
source venv/bin/activate

# Instala dependências (usa lock file)
pip install --upgrade pip
pip install -r requirements-lock.txt

# Se não tiver gunicorn no requirements:
pip install gunicorn
```

### **5. Configura variáveis de ambiente**

```bash
# Cria arquivo .env
nano .env
```

**Cole isso:**
```env
OPENAI_API_KEY=sk-proj-SEU_TOKEN_AQUI
```

Salva: `Ctrl+O` → `Enter` → `Ctrl+X`

### **6. Testa localmente**

```bash
# Ativa venv (se não estiver ativo)
source venv/bin/activate

# Roda backend
uvicorn app:app --host 0.0.0.0 --port 8000

# Abre outro terminal/SSH e testa:
curl http://localhost:8000/health
# Esperado: {"status":"healthy",...}
```

Se funcionou, `Ctrl+C` e continua.

---

## 🔧 Configuração Nginx (Reverse Proxy)

### **7. Cria config Nginx**

```bash
sudo nano /etc/nginx/sites-available/ceci
```

**Cole isso:**
```nginx
server {
    listen 80;
    server_name SEU_DOMINIO_OU_IP;

    # Headers de segurança
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logs
    access_log /var/log/nginx/ceci_access.log;
    error_log /var/log/nginx/ceci_error.log;

    # Timeout para WebSocket
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;

    # Proxy para FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Cache de assets estáticos (se tiver)
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Ajusta:** `SEU_DOMINIO_OU_IP` → seu IP ou domínio real

Salva: `Ctrl+O` → `Enter` → `Ctrl+X`

### **8. Ativa o site**

```bash
# Cria symlink
sudo ln -s /etc/nginx/sites-available/ceci /etc/nginx/sites-enabled/

# Remove default (opcional)
sudo rm /etc/nginx/sites-enabled/default

# Testa config
sudo nginx -t

# Reinicia Nginx
sudo systemctl restart nginx
```

---

## 🔄 Supervisor (Mantém API Rodando)

### **9. Cria config do Supervisor**

```bash
sudo nano /etc/supervisor/conf.d/ceci.conf
```

**Cole isso:**
```ini
[program:ceci]
command=/var/www/ceci/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 127.0.0.1:8000 --timeout 120
directory=/var/www/ceci
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/ceci/error.log
stdout_logfile=/var/log/ceci/access.log
environment=PATH="/var/www/ceci/venv/bin"
```

Salva: `Ctrl+O` → `Enter` → `Ctrl+X`

### **10. Cria diretórios de log**

```bash
sudo mkdir -p /var/log/ceci
sudo chown -R www-data:www-data /var/log/ceci
sudo chown -R www-data:www-data /var/www/ceci
```

### **11. Inicia o Supervisor**

```bash
# Recarrega configs
sudo supervisorctl reread
sudo supervisorctl update

# Inicia Ceci
sudo supervisorctl start ceci

# Verifica status
sudo supervisorctl status ceci
# Esperado: ceci RUNNING pid XXXXX, uptime 0:00:XX
```

---

## 🔒 SSL com Certbot (HTTPS grátis)

### **12. Configura SSL**

```bash
# Se tiver domínio (ex: ceci.seudominio.com):
sudo certbot --nginx -d ceci.seudominio.com

# Siga o wizard:
# - Email: seu@email.com
# - Agree: Yes
# - Share email: No
# - Redirect HTTP to HTTPS: Yes (opção 2)

# Certbot já configura tudo automaticamente!
```

**Renovação automática:**
```bash
# Testa renovação
sudo certbot renew --dry-run

# Já vem com cron configurado, sem precisar fazer nada
```

---

## ✅ Verificação Final

### **13. Testa tudo**

```bash
# Health check
curl http://SEU_IP_OU_DOMINIO/health

# WebSocket (instala wscat se precisar)
npm install -g wscat
wscat -c ws://SEU_IP_OU_DOMINIO/ws/ceci

# Envia mensagem:
{"usuario":"Passageiro","texto":"Oi Ceci!"}
```

---

## 🔄 Atualizações Futuras

### **Deploy de nova versão:**

```bash
# Conecta na VM
ssh seu-usuario@IP_DA_VM

# Vai pro diretório
cd /var/www/ceci

# Puxa mudanças
git pull origin main

# Ativa venv
source venv/bin/activate

# Atualiza dependências (se mudaram)
pip install -r requirements-lock.txt

# Reinicia app
sudo supervisorctl restart ceci

# Verifica
sudo supervisorctl status ceci
curl http://localhost:8000/health
```

---

## 🛠️ Troubleshooting

### **API não responde:**
```bash
# Verifica logs
sudo tail -f /var/log/ceci/error.log
sudo tail -f /var/log/nginx/ceci_error.log

# Status do supervisor
sudo supervisorctl status ceci

# Reinicia tudo
sudo supervisorctl restart ceci
sudo systemctl restart nginx
```

### **WebSocket não conecta:**
```bash
# Verifica se Nginx tá passando Upgrade headers
sudo nginx -t
sudo tail -f /var/log/nginx/ceci_access.log

# Testa direto no backend
curl http://127.0.0.1:8000/health
```

### **Permissões de reports/:**
```bash
# Garante que www-data consegue escrever
sudo chown -R www-data:www-data /var/www/ceci/reports
sudo chmod 755 /var/www/ceci/reports
```

### **RAM/CPU alto:**
```bash
# Monitora recursos
htop

# Reduz workers do gunicorn (edita supervisor config):
sudo nano /etc/supervisor/conf.d/ceci.conf
# Muda: -w 4 para -w 2
sudo supervisorctl restart ceci
```

---

## 📊 Monitoramento

### **Logs em tempo real:**
```bash
# Backend
sudo tail -f /var/log/ceci/access.log

# Nginx
sudo tail -f /var/log/nginx/ceci_access.log

# Erros
sudo tail -f /var/log/ceci/error.log
```

### **Status dos serviços:**
```bash
# Supervisor
sudo supervisorctl status

# Nginx
sudo systemctl status nginx

# Uso de disco
df -h

# Uso de RAM
free -h
```

---

## 🎯 Checklist Pós-Deploy

- [ ] `/health` responde com status healthy
- [ ] WebSocket `/ws/ceci` aceita conexões
- [ ] Relatórios PDF são gerados em `reports/`
- [ ] HTTPS funcionando (se configurou SSL)
- [ ] Logs sendo escritos corretamente
- [ ] Supervisor reinicia app automaticamente após crash
- [ ] `.env` com `OPENAI_API_KEY` válida
- [ ] Firewall liberou portas 80 e 443

---

## 💰 Custo Estimado

**VM Azure B1s (1 vCPU, 1GB RAM):**
- ~US$ 7.60/mês (Linux)
- Suficiente para MVP/apresentação
- Upgrade para B2s (~US$ 30/mês) se precisar mais performance

**SSL:** Grátis (Let's Encrypt via Certbot)  
**Domínio:** ~US$ 12/ano (opcional)

---

## 🚀 Deploy Completo em ~15min

Se seguir todos os passos acima, você terá:
- ✅ Backend rodando 24/7
- ✅ Nginx como reverse proxy
- ✅ HTTPS configurado (se tiver domínio)
- ✅ Auto-restart em caso de crash
- ✅ Logs organizados
- ✅ WebSocket funcionando
- ✅ Production-ready!

**Boa sorte no deploy! 🔥**
