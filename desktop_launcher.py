import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt6.QtCore import QUrl
import subprocess
import threading
import time


class NgrokInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        # Adiciona header para pular aviso do ngrok free
        if "ngrok" in info.requestUrl().host():
            info.setHttpHeader(b"ngrok-skip-browser-warning", b"true")
            info.setHttpHeader(b"User-Agent", b"CustomUserAgent/1.0")


def get_tunnel_url_from_secrets():
    """Procura por TUNNEL_URL em .streamlit/secrets.toml"""
    try:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")
        if not os.path.isfile(secrets_path):
            return None

        with open(secrets_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("TUNNEL_URL"):
                    _, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    return value or None
    except Exception:
        return None


def run_streamlit():
    # Usa o Python atual para iniciar o Streamlit (mais robusto que caminho estático para streamlit.exe)
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "desktop/main.py",
        "--server.port", "8501",
        "--server.headless", "true",
        "--server.address", "0.0.0.0"
    ])


# Tenta usar TUNNEL_URL do secrets.toml (se existir).
tunnel_url = get_tunnel_url_from_secrets()
has_tunnel_url = bool(tunnel_url)

# Se o URL aprendido parece ser o endpoint /v1 do LM Studio, apenas avisamos.
lm_studio_url = tunnel_url if tunnel_url and "/v1" in tunnel_url else None

# Inicia o Streamlit em background (sempre).
thread = threading.Thread(target=run_streamlit, daemon=True)
thread.start()

if has_tunnel_url:
    base_url = tunnel_url.replace("/v1", "")
    print(f"✅ TUNNEL_URL detectado: {base_url}")
    print("Verificando se o túnel já está ativo localmente...")

    tunnel_is_active = False
    try:
        # Verifica se o agente ngrok local já está servindo este túnel
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            tunnels = response.json().get("tunnels", [])
            for t in tunnels:
                if t.get("public_url") == base_url:
                    print(f"✅ Túnel já está sendo gerenciado pelo agente local.")
                    tunnel_is_active = True
                    break
    except requests.exceptions.RequestException:
        print("ℹ️ Agente Ngrok não está rodando. Será iniciado.")

    if not tunnel_is_active:
        print("Iniciando novo processo ngrok para o domínio estático...")
        print("Se receber o erro 'ERR_NGROK_334', significa que o túnel já está online.")
        print("Nesse caso, pare qualquer outro processo 'ngrok.exe' e tente novamente em um minuto.")
        try:
            hostname = base_url.replace("https://", "").replace("http://", "")
            # O comando correto para domínios estáticos é --hostname
            ngrok_thread = threading.Thread(
                target=lambda: subprocess.Popen(["ngrok", "http", "8501", "--hostname", hostname]),
                daemon=True
            )
            ngrok_thread.start()
            time.sleep(3)  # Aguarda ngrok iniciar
        except Exception as e:
            print(f"❌ Falha ao iniciar ngrok: {e}")
            print("Certifique-se de que 'ngrok' está instalado e no PATH do sistema.")
            base_url = "http://localhost:8501" # Fallback para localhost
else:
    base_url = None

# Se não tem TUNNEL_URL, inicia ngrok para túnel aleatório
if not has_tunnel_url:
    # Sempre verifica e inicia ngrok se necessário (para túnel público do app)
    def is_ngrok_running() -> bool:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", 4040))
            sock.close()
            return result == 0
        except Exception:
            return False

    # Inicia o Ngrok apenas se não estiver rodando
    if not is_ngrok_running():
        print("ℹ️ TUNNEL_URL não encontrado. Iniciando ngrok com túnel aleatório...")
        try:
            ngrok_thread = threading.Thread(
                target=lambda: subprocess.Popen(["ngrok", "http", "8501"]),
                daemon=True
            )
            ngrok_thread.start()
            time.sleep(2)  # Aguarda ngrok iniciar
        except FileNotFoundError:
            print("❌ Erro: 'ngrok' não encontrado. Certifique-se de que está instalado e no PATH.")
            base_url = "http://localhost:8501"

    # Aguarda o servidor iniciar

    # Tenta detectar o túnel público do ngrok
    ngrok_public_url = None
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            import requests
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get("tunnels", [])
                app_tunnel = next((t for t in tunnels if '8501' in t.get('config', {}).get('addr', '')), None)
                if app_tunnel:
                    ngrok_public_url = app_tunnel['public_url']
                    print(f"Túnel ngrok detectado: {ngrok_public_url}")
                    break
                else:
                    print(f"Tentativa {attempt + 1}: Nenhum túnel encontrado para a porta 8501.")
            else:
                print(f"Tentativa {attempt + 1}: Erro ao consultar API do ngrok: {response.status_code}")
        except Exception as e:
            print(f"Tentativa {attempt + 1}: Falha ao detectar túnel ngrok: {e}")
        
        if attempt < max_attempts - 1:
            print("Aguardando mais tempo para ngrok iniciar...")
            time.sleep(3)

    if not ngrok_public_url:
        print("Não foi possível detectar o túnel ngrok. Abrindo em localhost.")
        base_url = "http://localhost:8501"
    else:
        base_url = ngrok_public_url
else:
    # Aguarda o servidor iniciar
    time.sleep(5)
    
    # Para domínio customizado, se base_url definido, usa ele; senão detecta
    print(f"Usando URL do túnel: {base_url}")

try:
    # Cria a aplicação Qt
    app = QApplication(sys.argv)
    view = QWebEngineView()

    # Adiciona interceptor para pular aviso do ngrok
    interceptor = NgrokInterceptor()
    view.page().profile().setUrlRequestInterceptor(interceptor)

    # Abre o URL determinado
    print(f"Abrindo aplicação em: {base_url}")
    view.load(QUrl(base_url))

    view.show()
    sys.exit(app.exec())
except Exception as e:
    print(f"Erro: {e}")
    input("Pressione Enter para sair")