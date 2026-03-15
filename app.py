import json
import os
import qrcode
import requests
import socket
import streamlit as st
from openai import OpenAI
from io import BytesIO
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO E AMBIENTE ---
# Detecção robusta: Verifica override nos secrets, usuário padrão 'appuser' ou hostname típico do Cloud
IS_CLOUD = st.secrets.get("IS_CLOUD", False) or os.environ.get("USER") in ["appuser", "adminuser"] or os.environ.get("HOSTNAME", "").startswith("streamlit")

# Inicializar Supabase
supabase: Client = None
try:
    supabase_url = st.secrets.get("SUPABASE_URL")
    supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
    if supabase_url and supabase_key:
        supabase = create_client(supabase_url, supabase_key)
        st.sidebar.caption("🗄️ Supabase: Conectado")
    else:
        st.sidebar.caption("🗄️ Supabase: Não configurado")
except Exception as e:
    st.sidebar.caption(f"🗄️ Supabase: Erro - {str(e)[:20]}...")

st.set_page_config(
    page_title="Dev Assistant Pro",
    page_icon="🤖",
    layout="wide"
)

# Inicializa estados essenciais
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_path" not in st.session_state:
    st.session_state.current_path = os.getcwd() if not IS_CLOUD else "/"
if "last_ai_response" not in st.session_state:
    st.session_state.last_ai_response = ""
if "expert_type" not in st.session_state:
    st.session_state.expert_type = "Dev Sênior"
if "opinionated" not in st.session_state:
    st.session_state.opinionated = False
if "include_media" not in st.session_state:
    st.session_state.include_media = False
if "english_mode" not in st.session_state:
    st.session_state.english_mode = False
if "ngrok_url" not in st.session_state:
    st.session_state.ngrok_url = st.secrets.get("TUNNEL_URL", "").replace("/v1", "") if IS_CLOUD else ""
if "use_ngrok_for_ai" not in st.session_state:
    st.session_state.use_ngrok_for_ai = False
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""

# --- FUNÇÕES SUPABASE ---
def save_conversation_to_supabase(name: str, conversation_data: dict) -> bool:
    """Salva uma conversa no Supabase"""
    if not supabase:
        return False
    
    try:
        # Cria um ID único baseado no nome e timestamp
        import hashlib
        import time
        conversation_id = hashlib.md5(f"{name}_{int(time.time())}".encode()).hexdigest()[:16]
        
        data = {
            "id": conversation_id,
            "name": name,
            "messages": conversation_data.get("messages", []),
            "expert_type": conversation_data.get("expert_type", "Dev Sênior"),
            "opinionated": conversation_data.get("opinionated", False),
            "include_media": conversation_data.get("include_media", False),
            "english_mode": conversation_data.get("english_mode", False),
            "created_at": "now()",
            "updated_at": "now()"
        }
        
        result = supabase.table("conversations").insert(data).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Erro ao salvar no Supabase: {e}")
        return False

def load_conversations_from_supabase() -> list:
    """Carrega lista de conversas do Supabase"""
    if not supabase:
        return []
    
    try:
        result = supabase.table("conversations").select("id,name,created_at").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"Erro ao carregar conversas: {e}")
        return []

def load_conversation_from_supabase(conversation_id: str) -> dict:
    """Carrega uma conversa específica do Supabase"""
    if not supabase:
        return {}
    
    try:
        result = supabase.table("conversations").select("*").eq("id", conversation_id).execute()
        if result.data:
            return result.data[0]
        return {}
    except Exception as e:
        st.error(f"Erro ao carregar conversa: {e}")
        return {}

# --- 2. BARRA LATERAL (CONEXÃO E NAVEGAÇÃO) ---
st.sidebar.header("🔌 Conexão & Acesso")

# Indicador de modo
modo = "☁️ Cloud" if IS_CLOUD else "💻 Local"
st.sidebar.caption(f"Modo: {modo}")

if not IS_CLOUD:
    tunel_url = st.sidebar.text_input("Endereço LM Studio:", "http://localhost:1234/v1")
    ngrok_url = st.sidebar.text_input("URL Pública Ngrok (Opcional):", value=st.session_state.ngrok_url, key="ngrok_url")
    if ngrok_url:
        qr = qrcode.make(ngrok_url)
        buf = BytesIO()
        qr.save(buf)
        st.sidebar.image(buf, caption="Acesso Mobile", width=260)
else:
    tunel_url = st.sidebar.text_input("URL do Ngrok:", st.secrets.get("TUNNEL_URL", ""))

# --- QR Codes para Acesso Mobile ---
if not IS_CLOUD:
    with st.sidebar.expander("📱 Acesso Mobile"):
        # Função para obter todos os IPs locais (incluindo possíveis 192.168.0.x)
        def get_local_ips():
            ips = set()

            # IP padrão via rota padrão
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("8.8.8.8", 80))
                ips.add(s.getsockname()[0])
            except Exception:
                pass
            finally:
                try:
                    s.close()
                except Exception:
                    pass

            # Hostname
            try:
                hostname = socket.gethostname()
                for ip in socket.gethostbyname_ex(hostname)[2]:
                    ips.add(ip)
            except Exception:
                pass

            # localhost
            ips.add("127.0.0.1")

            return sorted(ips)

        local_ips = get_local_ips()
        st.write("**IPs locais detectados:**")
        for ip in local_ips:
            st.write(f"- {ip}")

        # Preferir 192.168.0.x se existir
        preferred_ip = next((ip for ip in local_ips if ip.startswith("192.168.0.")), local_ips[0])
        local_url = f"http://{preferred_ip}:8501"
        st.write("**URL local (preferido):**")
        st.write(local_url)

        try:
            qr_local = qrcode.make(local_url)
            buf = BytesIO()
            qr_local.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Acesso Local: {local_url}", width=260)
        except Exception as e:
            st.error(f"Erro gerando QR local: {e}")

        if ngrok_url:
            st.write("**URL pública (Ngrok):**")
            st.write(ngrok_url)
            try:
                qr = qrcode.make(ngrok_url)
                st.image(qr, caption="Acesso Público", width=260)
            except Exception as e:
                st.error(f"Erro gerando QR público: {e}")

    # --- Configurações de IA ---
    with st.sidebar.expander("⚙️ Configurações de IA"):
        expert_options = [
            "Dev Sênior", "Dev Junior", "Designer", "Analista de Dados", "Especialista em Automação",
            "Senior Developer", "Junior Developer", "Data Analyst", "Automation Specialist"
        ]
        st.session_state.expert_type = st.selectbox(
            "Tipo de Especialista:",
            expert_options,
            index=expert_options.index(st.session_state.expert_type) if st.session_state.expert_type in expert_options else 0
        )
        st.session_state.opinionated = st.checkbox("Modo Opinativo", value=st.session_state.opinionated)
        st.session_state.include_media = st.checkbox("Incluir mídia reproduzindo no contexto", value=st.session_state.include_media)
        st.session_state.english_mode = st.checkbox("Modo Inglês (responder em inglês)", value=st.session_state.get("english_mode", False))
        st.session_state.use_ngrok_for_ai = st.checkbox("Usar Ngrok para IA", value=st.session_state.get("use_ngrok_for_ai", False))
        
        st.markdown("---")
        # Feedback visual sobre a chave no Secrets
        has_secret = "GROQ_API_KEY" in st.secrets
        st.caption(f"Chave no Secrets: {'✅ Detectada' if has_secret else '❌ Não detectada'}")
        
        # Permite corrigir a chave API diretamente pela interface se o Secrets estiver errado
        st.session_state.groq_key = st.text_input("Groq API Key (Override):", value=st.session_state.groq_key, type="password", help="Use caso a chave nos secrets esteja inválida")

    # --- Ngrok Monitor ---
    with st.sidebar.expander("🌐 Ngrok Monitor"):
        if st.button("🔄 Atualizar Túneis"):
            try:
                response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    tunnels = data.get("tunnels", [])
                    if tunnels:
                        st.write("**Túneis Ativos:**")
                        for tunnel in tunnels:
                            st.write(f"**Nome:** {tunnel.get('name', 'N/A')}")
                            st.write(f"**URL Pública:** {tunnel.get('public_url', 'N/A')}")
                            st.write(f"**Protocolo:** {tunnel.get('proto', 'N/A')}")
                            st.write(f"**URL Local:** {tunnel.get('config', {}).get('addr', 'N/A')}")
                            
                            # Metrics
                            metrics = tunnel.get('metrics', {})
                            conns = metrics.get('conns', {})
                            http = metrics.get('http', {})
                            
                            st.write("**Métricas de Conexões:**")
                            st.write(f"- Total: {conns.get('count', 0)} | Abertas: {conns.get('gauge', 0)}")
                            st.write(f"- Taxa (/s): 1m: {conns.get('rate1', 0):.2f} | 5m: {conns.get('rate5', 0):.2f} | 15m: {conns.get('rate15', 0):.2f}")
                            st.write(f"- Durações (s) - 50%: {conns.get('p50', 0):.2f} | 90%: {conns.get('p90', 0):.2f} | 95%: {conns.get('p95', 0):.2f} | 99%: {conns.get('p99', 0):.2f}")
                            
                            st.write("**Métricas HTTP:**")
                            st.write(f"- Total de Requisições: {http.get('count', 0)}")
                            st.write(f"- Taxa (/s): 1m: {http.get('rate1', 0):.2f} | 5m: {http.get('rate5', 0):.2f} | 15m: {http.get('rate15', 0):.2f}")
                            st.write(f"- Durações (s) - 50%: {http.get('p50', 0):.2f} | 90%: {http.get('p90', 0):.2f} | 95%: {http.get('p95', 0):.2f} | 99%: {http.get('p99', 0):.2f}")
                            
                            st.write("---")
                        # Auto-detect tunnel for the app (port 8501)
                        app_tunnel = next((t for t in tunnels if '8501' in t.get('config', {}).get('addr', '')), None)
                        if app_tunnel:
                            st.session_state.ngrok_url = app_tunnel['public_url']
                            st.success(f"Ngrok detectado para o app: {app_tunnel['public_url']}")
                        else:
                            st.info("Nenhum túnel encontrado para o app (porta 8501).")
                    else:
                        st.write("Nenhum túnel ativo encontrado.")
                else:
                    st.error(f"Erro na API do Ngrok: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.warning(
                    "Ngrok não está acessível localmente. "
                    "Verifique se o processo ngrok está rodando (porta 4040). "
                    "Tente recarregar a página ou reiniciar o app."
                )
            except Exception as e:
                st.error(f"Erro inesperado: {e}")

    # --- LM Studio Monitor ---
    with st.sidebar.expander("🤖 LM Studio Monitor"):
        if st.button("🔍 Verificar API"):
            try:
                base_url = tunel_url.rstrip('/')
                if not base_url.endswith('/v1'): base_url += '/v1'
                response = requests.get(f"{base_url}/models", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    if models:
                        st.write("**Modelos Carregados:**")
                        for model in models:
                            st.write(f"- **ID:** {model.get('id', 'N/A')}")
                            st.write(f"  **Proprietário:** {model.get('owned_by', 'N/A')}")
                        # Check for ngrok tunnel for LM Studio (port 1234)
                        try:
                            ngrok_resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
                            if ngrok_resp.status_code == 200:
                                ngrok_data = ngrok_resp.json()
                                lm_tunnel = next((t for t in ngrok_data.get("tunnels", []) if '1234' in t.get('config', {}).get('addr', '')), None)
                                if lm_tunnel:
                                    st.success(f"Ngrok ativo para LM Studio: {lm_tunnel['public_url']}/v1/...")
                                else:
                                    st.info("Nenhum túnel ngrok encontrado para LM Studio (porta 1234).")
                        except:
                            st.info("Ngrok não detectado ou inacessível.")
                    else:
                        st.warning("Nenhum modelo carregado no LM Studio.")
                else:
                    st.error(f"Erro na API do LM Studio: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"LM Studio não está rodando ou inacessível: {e}")
            except Exception as e:
                st.error(f"Erro inesperado: {e}")

    # --- Histórico de Conversas ---
    with st.sidebar.expander("💬 Histórico de Conversas"):
        if supabase:
            # Salvar conversa atual no Supabase
            save_name = st.text_input("Nome para salvar conversa:", key="save_conv")
            if st.button("💾 Salvar no Supabase") and save_name:
                conv_data = {
                    "messages": st.session_state.messages,
                    "expert_type": st.session_state.expert_type,
                    "opinionated": st.session_state.opinionated,
                    "include_media": st.session_state.include_media,
                    "english_mode": st.session_state.english_mode
                }
                if save_conversation_to_supabase(save_name, conv_data):
                    st.success(f"✅ Conversa '{save_name}' salva no Supabase!")
                    st.rerun()

            # Carregar conversa do Supabase
            conversations = load_conversations_from_supabase()
            if conversations:
                conv_options = [""] + [f"{c['name']} ({c['created_at'][:10]})" for c in conversations]
                selected_conv_display = st.selectbox("Carregar conversa:", conv_options, key="load_conv")
                
                if selected_conv_display and st.button("📂 Carregar do Supabase"):
                    # Encontrar o ID da conversa selecionada
                    selected_name = selected_conv_display.split(" (")[0]
                    selected_conv = next((c for c in conversations if c['name'] == selected_name), None)
                    
                    if selected_conv:
                        conv_data = load_conversation_from_supabase(selected_conv['id'])
                        if conv_data:
                            st.session_state.messages = conv_data.get("messages", [])
                            st.session_state.expert_type = conv_data.get("expert_type", "Dev Sênior")
                            st.session_state.opinionated = conv_data.get("opinionated", False)
                            st.session_state.include_media = conv_data.get("include_media", False)
                            st.session_state.english_mode = conv_data.get("english_mode", False)
                            st.success(f"✅ Conversa '{selected_name}' carregada!")
                            st.rerun()
            else:
                st.info("Nenhuma conversa salva ainda.")
        else:
            # Fallback para arquivos locais se Supabase não estiver disponível
            conversations_dir = os.path.join(os.getcwd(), "conversations")
            os.makedirs(conversations_dir, exist_ok=True)

            # Salvar conversa atual localmente
            save_name = st.text_input("Nome para salvar conversa:", key="save_conv_local")
            if st.button("💾 Salvar Local") and save_name:
                conv_data = {
                    "messages": st.session_state.messages,
                    "expert_type": st.session_state.expert_type,
                    "opinionated": st.session_state.opinionated,
                    "include_media": st.session_state.include_media,
                    "english_mode": st.session_state.english_mode
                }
                filename = f"{save_name.replace(' ', '_')}.json"
                filepath = os.path.join(conversations_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(conv_data, f, ensure_ascii=False, indent=2)
                st.success(f"💾 Conversa salva localmente em: {filepath}")

            # Carregar conversa local
            if os.path.exists(conversations_dir):
                conv_files = [f for f in os.listdir(conversations_dir) if f.endswith('.json')]
                if conv_files:
                    selected_conv = st.selectbox("Carregar conversa local:", [""] + conv_files, key="load_conv_local")
                    if selected_conv and st.button("📂 Carregar Local"):
                        filepath = os.path.join(conversations_dir, selected_conv)
                        with open(filepath, "r", encoding="utf-8") as f:
                            conv_data = json.load(f)
                        st.session_state.messages = conv_data.get("messages", [])
                        st.session_state.expert_type = conv_data.get("expert_type", "Dev Sênior")
                        st.session_state.opinionated = conv_data.get("opinionated", False)
                        st.session_state.include_media = conv_data.get("include_media", False)
                        st.session_state.english_mode = conv_data.get("english_mode", False)
                        st.success(f"📂 Conversa '{selected_conv}' carregada!")
                        st.rerun()

# --- 3. INTERFACE PRINCIPAL ---
st.title("🤖 Dev Assistant Pro")
st.markdown("---")

# Área de chat
chat_container = st.container()

with chat_container:
    # Exibir mensagens anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("Digite sua pergunta..."):
    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

    # Preparar contexto para IA
    context = ""
    if st.session_state.include_media:
        # Simulação - em produção, detectar mídia reproduzindo
        context += "\nContexto adicional: Música/áudio reproduzindo (simulado)"

    # Tentar LM Studio primeiro
    ai_response = None
    try:
        client = OpenAI(base_url=tunel_url, api_key="lm-studio")
        
        messages = [{"role": "system", "content": f"Você é um {st.session_state.expert_type}. {'Seja opinativo e direto.' if st.session_state.opinionated else 'Seja prestativo e informativo.'} {'Responda em inglês.' if st.session_state.english_mode else 'Responda em português brasileiro.'}"}]
        messages.extend(st.session_state.messages[-10:])  # Últimas 10 mensagens
        
        if context:
            messages.insert(1, {"role": "system", "content": context})

        response = client.chat.completions.create(
            model="local-model",
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if "No models loaded" in error_msg:
            st.warning("⚠️ LM Studio conectado, mas NENHUM modelo carregado. Carregue um modelo na barra verde do LM Studio no seu PC.")
        else:
            st.warning(f"LM Studio indisponível ({error_msg[:100]}...). Usando Groq como fallback.")

    # Fallback para Groq
    if not ai_response:
        try:
            # Prioridade: Input da Sidebar > Secrets (para permitir correção rápida)
            # Removemos espaços em branco que costumam causar erro 401 ao copiar/colar
            user_key = st.session_state.get("groq_key", "").strip()
            secret_key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
            
            groq_key = user_key if user_key else secret_key
            key_source = "Sidebar (Override)" if user_key else "Secrets"
            
            if not groq_key:
                st.error("Configure GROQ_API_KEY nos secrets (.streamlit/secrets.toml) ou na barra lateral.")
                st.stop()
            
            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            
            messages = [{"role": "system", "content": f"Você é um {st.session_state.expert_type}. {'Seja opinativo e direto.' if st.session_state.opinionated else 'Seja prestativo e informativo.'} {'Responda em inglês.' if st.session_state.english_mode else 'Responda em português brasileiro.'}"}]
            messages.extend(st.session_state.messages[-10:])
            
            if context:
                messages.insert(1, {"role": "system", "content": context})

            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            ai_response = response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg:
                masked_key = f"{groq_key[:4]}...{groq_key[-4:]}" if len(groq_key) > 8 else "Inválida"
                ai_response = f"❌ **Erro 401: Chave Inválida**\n\nO sistema tentou usar a chave vinda de: **{key_source}**.\nChave detectada: `{masked_key}`\n\n👉 Se a origem for 'Sidebar', apague o campo na barra lateral.\n👉 Se for 'Secrets', verifique o painel do Streamlit Cloud."
            else:
                ai_response = f"❌ Erro no fallback Groq: {error_msg}"

    # Adicionar resposta da IA
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    st.session_state.last_ai_response = ai_response
    
    with chat_container:
        with st.chat_message("assistant"):
            st.markdown(ai_response)

# --- 4. RODAPÉ ---
st.markdown("---")
st.caption("Desenvolvido com ❤️ | Arquitetura Híbrida: Local + Cloud Fallback")
