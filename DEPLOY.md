# 🚀 Deploy Landing Page - Azure Static Web Apps (FREE)

## ⚡ Deploy Rápido (5 minutos)

### Opção 1: Via Portal Azure (Mais Fácil)

1. **Acesse:** https://portal.azure.com
2. **Crie recurso:** Procure "Static Web Apps" → Create
3. **Configuração:**
   - Subscription: Free tier
   - Resource Group: `projeto-acessi-rg` (cria novo)
   - Name: `ceci-landing`
   - Region: `East US 2` (free tier disponível)
   - Source: `GitHub` (conecta sua conta)
   - Repository: Selecione `mini_ceciV2_mcp`
   - Branch: `main`
   - Build Presets: `Custom`
   - App location: `/landing`
   - Api location: (deixe vazio)
   - Output location: (deixe vazio)

4. **Review + Create** → Aguarda 2-3min

5. **URL gerada:** `https://ceci-landing-XXXX.azurestaticapps.net`

---

### Opção 2: Via Azure CLI (Mais Rápido)

```bash
# Instala Azure CLI (se não tiver)
# https://aka.ms/installazurecliwindows

# Login
az login

# Cria resource group
az group create --name projeto-acessi-rg --location eastus2

# Deploy static web app
az staticwebapp create \
  --name ceci-landing \
  --resource-group projeto-acessi-rg \
  --source https://github.com/SEU_USUARIO/mini_ceciV2_mcp \
  --location eastus2 \
  --branch main \
  --app-location "/landing" \
  --login-with-github

# Aguarda deploy (~2min)
# URL será exibida no output
```

---

### Opção 3: Deploy Manual (Sem GitHub Actions)

```bash
# Instala SWA CLI
npm install -g @azure/static-web-apps-cli

# Deploy direto da pasta
cd landing
swa deploy --app-location . --env production
```

---

## 📱 Gerar QR Code

Depois que tiver a URL (ex: `https://ceci-landing-abc123.azurestaticapps.net`):

### Online (Rápido):
1. Acesse: https://www.qr-code-generator.com/
2. Cole a URL do seu site
3. Baixa PNG em alta resolução
4. **Imprime em A4** ou adiciona no cartaz

### Via Python (Profissa):
```bash
pip install qrcode[pil]

python -c "
import qrcode
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data('https://ceci-landing-abc123.azurestaticapps.net')
qr.make(fit=True)
img = qr.make_image(fill_color='black', back_color='white')
img.save('qr-code-ceci.png')
print('QR Code gerado: qr-code-ceci.png')
"
```

---

## ✏️ Personalizar Antes do Deploy

### **Edite `landing/index.html`:**

Procure e substitua:

```html
<!-- Linha ~86: Link do GitHub -->
<a href="https://github.com/SEU_USUARIO/mini_ceciV2_mcp" target="_blank" class="btn btn-secondary">Ver Código</a>

<!-- Linha ~213: Link do GitHub -->
<a href="https://github.com/SEU_USUARIO/mini_ceciV2_mcp" target="_blank" class="btn btn-primary">Saiba Mais</a>

<!-- Linha ~341: Link do GitHub -->
<a href="https://github.com/SEU_USUARIO/mini_ceciV2_mcp" target="_blank" class="btn">
  Ver Repositório no GitHub →
</a>

<!-- Linha ~353: Email de contato -->
<a href="mailto:seu.email@fiap.com.br">Contato</a>
```

**Substitua:**
- `SEU_USUARIO` → seu username do GitHub
- `seu.email@fiap.com.br` → seu email real

---

## 🎯 Checklist Pré-Deploy

- [ ] Editou links do GitHub com seu username
- [ ] Testou o `index.html` localmente (abre no navegador)
- [ ] Commitou as mudanças no Git
- [ ] Fez push pro GitHub
- [ ] Deploy no Azure (opção 1, 2 ou 3)
- [ ] Testou a URL gerada
- [ ] Gerou QR Code
- [ ] Imprimiu QR Code em alta qualidade

---

## 🧪 Testar Localmente

```bash
cd landing

# Opção 1: Python
python -m http.server 8000
# Acessa: http://localhost:8000

# Opção 2: npx
npx serve .
# Acessa: http://localhost:3000

# Opção 3: SWA CLI
npx @azure/static-web-apps-cli start
# Acessa: http://localhost:4280
```

---

## 🎨 Customizações Opcionais

### Adicionar Google Analytics
```html
<!-- Antes de </head> -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Adicionar Favicon
```html
<!-- Antes de </head> -->
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚇</text></svg>">
```

### Trocar Cores (edite `:root` no CSS)
```css
:root {
    --primary: #0066FF;    /* Azul principal */
    --secondary: #00C7B7;  /* Verde água */
    --accent: #FF6B35;     /* Laranja */
}
```

---

## 💰 Custo

**FREE TIER Azure Static Web Apps:**
- ✅ 100 GB bandwidth/mês
- ✅ SSL grátis
- ✅ Custom domain grátis
- ✅ CI/CD automático via GitHub Actions
- ✅ **US$ 0.00/mês**

---

## 🚨 Troubleshooting

### "Deploy falhou"
```bash
# Verifica logs
az staticwebapp show --name ceci-landing --resource-group projeto-acessi-rg
```

### "404 no site"
- Verifica se `app-location` está `/landing` no workflow
- Confirma que `index.html` está na raiz de `/landing`

### "QR Code não funciona"
- Testa URL diretamente no navegador
- Confirma que site está online (sem erros 404/500)

---

## 📞 Suporte Rápido

**Azure Static Web Apps Docs:**  
https://docs.microsoft.com/azure/static-web-apps/

**Gerador QR Code:**  
https://www.qr-code-generator.com/

---

## ✨ Resultado Final

Depois do deploy:
- ✅ Site profissional em `https://ceci-landing-XXX.azurestaticapps.net`
- ✅ QR Code impresso apontando pra landing
- ✅ Link "Ver Código" levando pro GitHub
- ✅ **Impressão de PROFISSIONALISMO** 🔥

**Tempo total:** 10-15 minutos  
**Custo:** US$ 0.00  
**Impacto:** 📈📈📈
