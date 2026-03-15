import json
import os
import qrcode
import requests
import socket
import streamlit as st
from openai import OpenAI
from io import BytesIO

# --- 1. CONFIGURAÇÃO E AMBIENTE ---
IS_CLOUD = "STREAMLIT_RUNTIME_EXECUTABLE" in os.environ

st.set_page_config(
    page_title="Dev Assistant Pro",
    page_icon="🤖",
    layout="wide"
)

# Inicializa estados essenciais
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_path" not in st.session_state:
    st.session_state.current_path = "B:/" if os.path.exists("B:/") else os.getcwd()
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
    st.session_state.ngrok_url = ""
if "use_ngrok_for_ai" not in st.session_state:
    st.session_state.use_ngrok_for_ai = False

# --- 2. BARRA LATERAL (CONEXÃO E NAVEGAÇÃO) ---
st.sidebar.header("🔌 Conexão & Acesso")

# DEBUG: mostrar se estamos no modo Cloud (influencia se o QR aparece)
st.sidebar.caption(f"IS_CLOUD = {IS_CLOUD}")
st.sidebar.caption(f"STREAMLIT_RUNTIME_EXECUTABLE = {os.environ.get('STREAMLIT_RUNTIME_EXECUTABLE')}")

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
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
        conversations_dir = os.path.join(os.getcwd(), "conversations")
        os.makedirs(conversations_dir, exist_ok=True)

        # Salvar conversa atual
        save_name = st.text_input("Nome para salvar conversa:", key="save_conv")
        if st.button("💾 Salvar Conversa") and save_name:
            conv_data = {
                "messages": st.session_state.messages,
                "expert_type": st.session_state.expert_type,
                "opinionated": st.session_state.opinionated,
                "include_media": st.session_state.include_media,
                "english_mode": st.session_state.english_mode,
                "current_path": st.session_state.current_path,
                "play_media": st.session_state.get("play_media"),
                "play_media_type": st.session_state.get("play_media_type")
            }
            save_path = os.path.join(conversations_dir, f"{save_name}.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(conv_data, f, ensure_ascii=False, indent=2)
            st.success(f"Conversa salva em: {save_path}")

        # Carregar conversa
        conv_files = [f for f in os.listdir(conversations_dir) if f.endswith(".json")]
        if conv_files:
            selected_conv = st.selectbox("Carregar conversa:", [""] + conv_files, key="load_conv")
            if st.button("📂 Carregar Conversa") and selected_conv:
                load_path = os.path.join(conversations_dir, selected_conv)
                with open(load_path, "r", encoding="utf-8") as f:
                    conv_data = json.load(f)
                st.session_state.messages = conv_data.get("messages", [])
                st.session_state.expert_type = conv_data.get("expert_type", "Dev Sênior")
                st.session_state.opinionated = conv_data.get("opinionated", False)
                st.session_state.include_media = conv_data.get("include_media", False)
                st.session_state.english_mode = conv_data.get("english_mode", False)
                st.session_state.current_path = conv_data.get("current_path", st.session_state.current_path)
                if "play_media" in conv_data:
                    st.session_state.play_media = conv_data["play_media"]
                    st.session_state.play_media_type = conv_data.get("play_media_type", "audio")
                st.rerun()
                st.success(f"Conversa carregada de: {load_path}")
        else:
            st.write("Nenhuma conversa salva ainda.")

api_key_groq = st.sidebar.text_input("Groq API Key (Backup):", type="password")

# --- 3. EXPLORADOR DE PASTAS (LOCAL) ---
if not IS_CLOUD:
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Projetos no B:")

    col_back, col_clear = st.sidebar.columns(2)
    if col_back.button("⬅️ Voltar"):
        st.session_state.current_path = os.path.dirname(st.session_state.current_path)
        st.rerun()
    if col_clear.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

    st.sidebar.caption(f"📍 {st.session_state.current_path}")

    try:
        items = os.listdir(st.session_state.current_path)
        folders = sorted([f for f in items if
                          os.path.isdir(os.path.join(st.session_state.current_path, f)) and not f.startswith('.')])
        files = sorted([f for f in items if
                        os.path.isfile(os.path.join(st.session_state.current_path, f)) and not f.startswith('.')])

        for folder in folders:
            if st.sidebar.button(f"📁 {folder}", key=f"dir_{folder}"):
                st.session_state.current_path = os.path.join(st.session_state.current_path, folder)
                st.rerun()

        for file in files:
            col_f, col_play, col_btn = st.sidebar.columns([0.6, 0.2, 0.2])
            col_f.caption(f"📄 {file}")

            ext = os.path.splitext(file)[1].lower()
            if ext in (".mp3", ".mp4"):
                if col_play.button("▶️", key=f"play_{file}"):
                    st.session_state.play_media = os.path.join(st.session_state.current_path, file)
                    st.session_state.play_media_type = "audio" if ext == ".mp3" else "video"
                    st.rerun()

            if col_btn.button("➕", key=f"file_{file}"):
                full_path = os.path.join(st.session_state.current_path, file)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                st.session_state.messages.append(
                    {"role": "user", "content": f"Analise o código de `{file}`:\n\n```\n{content}\n```"})
                st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro: {e}")


# --- 4. LÓGICA DE IA ---
def get_ai_client():
    if st.session_state.get("use_ngrok_for_ai") and st.session_state.ngrok_url:
        base_url = st.session_state.ngrok_url.rstrip('/')
        if not base_url.endswith('/v1'): base_url += '/v1'
    else:
        base_url = tunel_url.rstrip('/')
        if not base_url.endswith('/v1'): base_url += '/v1'
    try:
        check = requests.get(f"{base_url}/models", timeout=1)
        if check.status_code == 200:
            models_data = check.json()
            model_id = models_data.get('data', [{}])[0].get('id', 'gemma-3n-e4b-it-text')
            return OpenAI(base_url=base_url, api_key="lm-studio"), model_id
    except:
        pass
    if api_key_groq:
        return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_groq), "llama-3.1-8b-instant"
    return None, None


client, model_name = get_ai_client()

# --- 5. CHAT E SALVAMENTO ---
st.title(f"🚀 {st.session_state.expert_type} AI Assistant")

# Mostra player de mídia se selecionado
if st.session_state.get("play_media"):
    media_path = st.session_state.play_media
    media_type = st.session_state.get("play_media_type", "audio")
    col_title, col_stop = st.columns([0.8, 0.2])
    col_title.write(f"**Reproduzindo:** {os.path.basename(media_path)}")
    if col_stop.button("⏹️ Parar", key="stop_media"):
        del st.session_state.play_media
        del st.session_state.play_media_type
        st.rerun()
    try:
        if media_type == "audio":
            st.audio(media_path)
        else:
            st.video(media_path)
    except Exception as e:
        st.error(f"Erro ao reproduzir mídia: {e}")

# Exibe histórico (Usando containers para garantir a ordem)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input de Chat
if prompt := st.chat_input("Diga algo..."):
    if client:
        # 1. Adiciona e mostra a mensagem do usuário imediatamente
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Gera a resposta da IA
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""

            try:
                # Construir prompt do sistema dinamicamente
                system_prompt = f"Você é um {st.session_state.expert_type} focado em automação."
                if st.session_state.english_mode:
                    system_prompt += " Responda sempre em inglês, pois o usuário quer praticar conversação."
                if st.session_state.opinionated:
                    system_prompt += " Seja opinativo e dê sugestões diretas."
                if st.session_state.include_media and st.session_state.get("play_media"):
                    media_name = os.path.basename(st.session_state.play_media)
                    system_prompt += f" Considere que o usuário está reproduzindo '{media_name}' e incorpore isso no contexto se relevante."

                # Limita o histórico para evitar exceder o contexto do modelo (n_ctx).
                # Isso previne erros como "n_keep >= n_ctx" em modelos com limite de ~4k tokens.
                MAX_HISTORY = 14
                history_truncated = False
                if len(st.session_state.messages) > MAX_HISTORY:
                    st.session_state.messages = st.session_state.messages[-MAX_HISTORY:]
                    history_truncated = True

                msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages

                if history_truncated:
                    st.warning(
                        "🔔 Histórico truncado para evitar ultrapassar o limite de contexto (n_ctx). "
                        "Considere usar um modelo com maior contexto (ex.: Gemma 3n 8k/32k ou outro modelo de 16k/32k tokens) "
                        "ou limpar o chat antes de enviar prompts muito longos."
                    )

                stream = client.chat.completions.create(
                    model=model_name,
                    messages=msgs,
                    stream=True
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        placeholder.markdown(full_res + "▌")

                # Finaliza a exibição
                placeholder.markdown(full_res)

                # 3. SÓ AGORA salva no estado e atualiza o histórico
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.session_state.last_ai_response = full_res

                # Removido o st.rerun() daqui para evitar o loop de reset antes da leitura

            except Exception as e:
                st.error(f"Erro na geração: {e}")
    else:
        st.error("Sem conexão ativa com o LM Studio ou Groq.")

# --- 6. FUNÇÃO DE SALVAR ---
# Só aparece se houver uma resposta para salvar e se estivermos localmente
if not IS_CLOUD and st.session_state.get("last_ai_response"):
    st.write("---")
    with st.expander("💾 Salvar última resposta da IA no Drive B:"):
        # Sugere um nome baseado no arquivo analisado ou um padrão
        file_name = st.text_input("Nome do arquivo:", "refatorado.py")
        if st.button("Confirmar Salvamento"):
            try:
                save_path = os.path.join(st.session_state.current_path, file_name)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(st.session_state.last_ai_response)
                st.success(f"✅ Arquivo salvo com sucesso em: {save_path}")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
