@echo off
chcp 65001 > nul
setlocal

echo Verificando sistema operacional...
ver | find "Windows" >nul
if %errorlevel% neq 0 (
    echo ❌ Este script é otimizado para Windows.
    echo Para Linux/Mac, use: python3 -m venv .tapienv && source .tapienv/bin/activate
    exit /b 1
)

REM Converte para caminho absoluto do Windows
set "PYTHON_EXECUTABLE=C:\Local\Apps\Python\Python312\python.exe"
set "VENV_DIR=.tapienv"

if not defined VENV_PATH (
  for %%a in ("%CD%\%VENV_DIR%") do set "VENV_PATH=%%~fa"
)

REM Cria o ambiente virtual usando script Python inteligente
if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python create_venv.py
    if errorlevel 1 (
        echo ❌ Falha ao criar ambiente virtual
        exit /b 1
    )
)

REM Verifica se o ambiente virtual existe corretamente após criação
if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo ❌ Ambiente virtual não foi criado corretamente.
    echo Tentando criar manualmente...
    "%PYTHON_EXECUTABLE%" -m venv "%VENV_PATH%"
    if errorlevel 1 (
        echo ❌ Falha na criação manual do ambiente virtual
        exit /b 1
    )
)

echo Atualizando o Pip...
"%VENV_PATH%\Scripts\python.exe" -m pip install --upgrade pip

REM Instala/Atualiza dependencias
echo Verificando dependencias...
"%VENV_PATH%\Scripts\pip.exe" install --upgrade pip -r requirements.txt


REM Verifica se o .env existe antes de popular o banco
if not exist ".env" (
    echo.
    echo AVISO: Arquivo .env nao encontrado.
    echo Por favor, renomeie .env.example para .env e preencha com suas credenciais do Supabase.
    echo Os scripts de populacao do banco de dados serao ignorados.
    echo.
    goto start_app
)


goto start_app
:start_app
REM Forca o modo local ignorando o secrets.toml
set FORCE_LOCAL_MODE=1

REM Executa a aplicacao
echo.
echo Iniciando o Tríplice AI...
call "%VENV_DIR%\Scripts\streamlit.exe" run app.py
pause