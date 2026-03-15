# create_venv.py
import os
import platform
import subprocess
import sys

venv_dir = ".tapienv"

def check_virtualenv_exists():
    """Verifica se o ambiente virtual já existe e é válido"""
    if platform.system() == "Windows":
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        return os.path.exists(python_exe)
    else:
        # Para Linux/Mac, verificar se existe bin/python
        python_exe = os.path.join(venv_dir, "bin", "python")
        return os.path.exists(python_exe)

def create_virtualenv():
    """Cria ambiente virtual apenas se necessário"""
    system = platform.system()

    print(f"Sistema operacional: {system}")
    print(f"Usando Python: {sys.executable}")
    print(f"Versão do Python: {sys.version}")

    # Verificar se já existe ambiente virtual válido
    if check_virtualenv_exists():
        print(f"Ambiente virtual '{venv_dir}' já existe e está válido.")
        return

    # Só criar venv no Windows
    if system == "Windows":
        print("Criando ambiente virtual para Windows...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
            print("✅ Ambiente virtual criado com sucesso.")

            # Verificar se foi criado corretamente
            if check_virtualenv_exists():
                print("✅ Ambiente virtual validado com sucesso.")
            else:
                print("❌ Erro: Ambiente virtual não foi criado corretamente.")
                sys.exit(1)

        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao criar ambiente virtual: {e}")
            sys.exit(1)
    else:
        print(f"ℹ️  Este script é otimizado para Windows. Para {system}, considere usar:")
        print("   python3 -m venv .tapienv")
        print("   source .tapienv/bin/activate  # Linux/Mac")
        sys.exit(0)

if __name__ == "__main__":
    create_virtualenv()
