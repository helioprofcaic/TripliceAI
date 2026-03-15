# 🚀 Guia de Deploy - TripliceAI

Este guia explica como fazer o deploy do TripliceAI no **Streamlit Cloud** para acesso público online.

## 📋 Pré-requisitos

- Conta no [GitHub](https://github.com)
- Conta no [Streamlit Cloud](https://share.streamlit.io/)
- Conta no [Ngrok](https://ngrok.com/) (para túnel LM Studio)
- Conta no [Groq](https://console.groq.com/) (API backup)

## 📝 Passo 1: Preparar o Repositório

### 1.1 Criar repositório no GitHub
1. Acesse [GitHub](https://github.com) e clique em "New repository"
2. Nome: `TripliceAI`
3. Descrição: "Hybrid AI Assistant with Local + Cloud Fallback"
4. Deixe público
5. Não inicialize com README

### 1.2 Fazer upload do código
```bash
# No terminal, navegue até a pasta do projeto
cd /caminho/para/TripliceAI

# Inicializar git (se não fez ainda)
git init
git add .
git commit -m "Initial commit"

# Conectar ao GitHub
git remote add origin https://github.com/SEU_USERNAME/TripliceAI.git
git push -u origin main
```

**Arquivos necessários para o deploy:**
- `app.py` (arquivo principal)
- `requirements.txt`
- `.streamlit/secrets.toml` (será configurado no Streamlit Cloud)
- `README.md`

**Arquivos opcionais (não subir para cloud):**
- `desktop/` (versão desktop)
- `desktop_launcher.py`
- `desktop.bat`
- `create_venv.py`

## 🔧 Passo 2: Configurar Secrets

### 2.1 Obter API Keys

#### Ngrok
1. Acesse [Ngrok Dashboard](https://dashboard.ngrok.com/)
2. Vá em "Your Authtoken"
3. Copie o token

#### Groq
1. Acesse [Groq Console](https://console.groq.com/)
2. Crie uma API Key
3. Copie a key

### 2.2 Configurar Túnel Ngrok
```bash
# Instale ngrok se não tiver
# Configure authtoken
ngrok config add-authtoken SEU_TOKEN

# Inicie túnel para LM Studio (porta 1234)
ngrok http 1234 --url https://seu-dominio.ngrok-free.app
```

Copie a URL gerada (ex: `https://abc123.ngrok-free.app`) e adicione `/v1` no final para `TUNNEL_URL`.

## 🌐 Passo 3: Deploy no Streamlit Cloud

### 3.1 Conectar o Repositório
1. Acesse [Streamlit Cloud](https://share.streamlit.io/)
2. Clique em "New app"
3. Selecione "Deploy a public app from GitHub"
4. Conecte sua conta GitHub
5. Selecione o repositório `TripliceAI`
6. Branch: `main`
7. Arquivo principal: `app.py`

### 3.2 Configurar Secrets
No painel do app, vá em "Advanced settings" > "Secrets":

```toml
GROQ_API_KEY = "gsk_..."
TUNNEL_URL = "https://seu-dominio.ngrok-free.app/v1"

# Opcional: Supabase para salvar conversas na nuvem
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Nota:** Para configurar o Supabase:
1. Crie um projeto gratuito em [supabase.com](https://supabase.com)
2. Execute o script `supabase_setup.sql` no SQL Editor
3. Copie a URL do projeto e a chave anônima para os secrets acima

### 3.3 Deploy
1. Clique em "Deploy!"
2. Aguarde o build (pode levar alguns minutos)
3. O app estará online em `https://SEU_USERNAME-TripliceAI.streamlit.app`

## 🔍 Passo 4: Verificar Funcionamento

### 4.1 Testar Conexões
- **LM Studio Local:** Deve conectar via túnel ngrok
- **Groq Fallback:** Deve funcionar quando LM Studio estiver offline
- **Interface:** Deve carregar corretamente

### 4.2 Monitorar Logs
No Streamlit Cloud, vá em "Manage app" > "Logs" para ver erros.

## 🛠️ Troubleshooting

### Erro: "Connection failed"
- Verifique se o túnel ngrok está ativo
- Confirme se LM Studio está rodando na porta 1234

### Erro: "Secrets not found"
- Verifique se os secrets estão configurados corretamente no painel

### App lento
- Considere usar modelo menor no LM Studio
- Verifique conexão com Groq

## 📱 Acesso Mobile

O app gera QR codes automaticamente para acesso mobile. Para compartilhar:
1. Abra o app online
2. Vá no sidebar > "Acesso Mobile"
3. Escaneie o QR code

## 🔄 Atualizações

Para atualizar o app:
1. Faça commits no GitHub
2. No Streamlit Cloud, clique em "Reboot app" ou aguarde auto-deploy

## 💡 Dicas para Produção

- **Monitoramento:** Configure alertas no Streamlit Cloud
- **Backup:** Mantenha LM Studio rodando 24/7 para melhor experiência
- **Segurança:** Não exponha chaves API desnecessariamente
- **Performance:** Use modelos otimizados no LM Studio

---

**Deploy concluído!** O TripliceAI agora está online e acessível globalmente. 🎉