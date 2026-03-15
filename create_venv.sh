#!/bin/bash
# create_venv.sh - Script para criar ambiente virtual em Linux/Mac
# Uso: ./create_venv.sh

VENV_DIR=".tapienv"

echo "Verificando sistema operacional..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "❌ Este script é para Linux/Mac. Para Windows, use: python create_venv.py"
    exit 1
fi

echo "Sistema operacional: $OSTYPE"
echo "Usando Python: $(which python3)"
python3 --version

# Verificar se já existe ambiente virtual
if [ -f "$VENV_DIR/bin/python" ]; then
    echo "Ambiente virtual '$VENV_DIR' já existe e está válido."
    exit 0
fi

echo "Criando ambiente virtual..."
python3 -m venv "$VENV_DIR"

if [ $? -eq 0 ]; then
    echo "✅ Ambiente virtual criado com sucesso."

    # Verificar se foi criado corretamente
    if [ -f "$VENV_DIR/bin/python" ]; then
        echo "✅ Ambiente virtual validado com sucesso."
        echo ""
        echo "Para ativar o ambiente virtual, execute:"
        echo "  source $VENV_DIR/bin/activate"
    else
        echo "❌ Erro: Ambiente virtual não foi criado corretamente."
        exit 1
    fi
else
    echo "❌ Erro ao criar ambiente virtual."
    exit 1
fi