# 🤖 Hybrid Intelligence: Gemma 3n + Cloud Backup

Este projeto implementa uma **Arquitetura de Contingência Tripla** para assistentes de IA. O sistema prioriza o processamento local (preservando privacidade e custo zero), utilizando modelos hospedados em hardware próprio, com fallback automático para APIs de nuvem de alta performance.

## 🏗️ A Arquitetura (O "Frankenstein")

O fluxo de decisão do assistente segue esta hierarquia:
1. **Local (Offline/Túnel):** Tenta conectar ao **LM Studio** rodando no PC local (Modelos no Drive B:).
2. **Túnel Ngrok:** Utiliza um túnel seguro para expor o servidor local ao Streamlit Cloud.
3. **Nuvem (Fallback):** Caso o PC local esteja desligado ou o túnel caia, o sistema alterna automaticamente para a **API da Groq (Llama 3)**.

## 🚀 Tecnologias Utilizadas

* **Frontend:** [Streamlit](https://streamlit.io/)
* **Local LLM Engine:** [LM Studio](https://lmstudio.ai/)
* **Modelo Local:** Google Gemma 3n (Experimental 4B) - *Armazenado no Drive B:*
* **Túnel:** [Ngrok](https://ngrok.com/)
* **API de Backup:** [Groq Cloud](https://console.groq.com/) (Llama 3 8B)
* **Linguagem:** Python 3.10+

## 📂 Estrutura de Pastas

```text
├── .streamlit/
│   └── secrets.toml      # Configurações sensíveis (URL Ngrok, API Keys)
├── app.py                # Lógica principal do Streamlit e gestão de conexão
├── desktop/              # Versão desktop com launcher Qt
│   └── main.py           # App Streamlit para desktop
├── desktop_launcher.py   # Launcher Qt para versão desktop
├── desktop.bat           # Script para iniciar versão desktop
├── requirements.txt      # Dependências do Python
└── README.md             # Documentação do projeto
```

## 🛠️ Instalação e Configuração

### Pré-requisitos
- **Python 3.10+** instalado
- **LM Studio** instalado e configurado com modelo Gemma 3n
- **Ngrok** instalado e configurado com authtoken
- Conta no **Groq Cloud** (para fallback)

### 1. Clone o Repositório
```bash
git clone <url-do-repositorio>
cd TripliceAI
```

### 2. Configure o Ambiente Virtual
O projeto inclui scripts inteligentes para criar ambientes virtuais:

**Windows:**
```bash
# O script detecta automaticamente se o venv já existe
python create_venv.py
# ou simplesmente execute: run.bat
```

**Linux/Mac:**
```bash
# Torne o script executável e execute
chmod +x create_venv.sh
./create_venv.sh
# ou manualmente: python3 -m venv .tapienv && source .tapienv/bin/activate
```

**Nota:** Os scripts só criam o ambiente virtual se ele não existir. Se já houver um venv válido, eles informam e saem.

### 3. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 4. Configure os Secrets
Crie o arquivo `.streamlit/secrets.toml` baseado no exemplo `secrets.example.toml`:
```toml
GROQ_API_KEY = "sua-chave-groq-aqui"
TUNNEL_URL = "https://seu-dominio-ngrok.ngrok-free.app/v1"

# Opcional: Supabase para salvar conversas na nuvem
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-chave-anonima-supabase"
```

### 3.1 Configure o Supabase (Opcional - Para salvar conversas na nuvem)
1. Acesse [supabase.com](https://supabase.com) e crie um projeto gratuito.
2. Vá para **SQL Editor** no painel do Supabase.
3. Execute o script `supabase_setup.sql` para criar a tabela de conversas.
4. Copie a **Project URL** e **anon public key** para `secrets.toml`.

### 5. Configure o LM Studio
- Baixe o modelo **Google Gemma 3n 4B** no LM Studio.
- Inicie o servidor local na porta **1234** com API habilitada.

### 6. Configure o Ngrok
```bash
ngrok config add-authtoken SEU_TOKEN_AQUI
ngrok http 1234 --url https://seu-dominio.ngrok-free.app
```
Copie o `TUNNEL_URL` gerado para `secrets.toml`.

## 🚀 Como Usar

### Versão Desktop (Recomendada)
1. Execute `desktop.bat`.
2. O launcher Qt abrirá automaticamente o app.
3. Use o QR code no sidebar para acesso mobile.

### Versão Web (Streamlit Run)
```bash
streamlit run app.py
```

### Deploy no Streamlit Cloud
1. Suba o código para um repositório GitHub público.
2. Acesse [Streamlit Cloud](https://share.streamlit.io/) e conecte o repo.
3. Configure os secrets no painel do Streamlit Cloud.
4. Deploy automático!

## 🔧 Configurações Avançadas

### Modos do Assistente
- **Dev Sênior:** Foco em código e arquitetura.
- **Designer:** Criação de interfaces e UX.
- **Analista de Dados:** Análises e visualizações.

### Opções de IA
- **Modo Opinativo:** Respostas mais diretas.
- **Incluir Mídia:** Contexto de mídia reproduzindo.
- **Modo Inglês:** Respostas em inglês.

### Monitor de Conexão
O sidebar inclui monitores para:
- Status do Ngrok
- Status do LM Studio
- Histórico de conversas

## 📊 Funcionalidades

- ✅ Processamento local prioritário (privacidade)
- ✅ Fallback automático para nuvem
- ✅ Interface responsiva com QR codes
- ✅ Suporte a múltiplos modelos de IA
- ✅ Histórico de conversas persistente
- ✅ Modos especializados por tipo de assistente

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para dúvidas ou issues, abra uma issue no GitHub ou entre em contato com o maintainer.

---

**Desenvolvido com ❤️ para demonstrar arquiteturas híbridas de IA.**