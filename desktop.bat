@echo off
chcp 65001 > nul
setlocal


REM Converte para caminho absoluto do Windows
REM set "PYTHON_EXECUTABLE=C:\Local\Apps\Python\Python312\python.exe"
set "VENV_DIR=.tapienv"


if not defined VENV_PATH (
  for %%a in ("%CD%\%VENV_DIR%") do set "VENV_PATH=%%~fa"
)

REM Cria o ambiente virtual usando script Python
if not exist "%VENV_PATH%\Scripts\python.exe" (
    python create_venv.py
)

REM Verifica se o ambiente virtual existe corretamente
if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo Criando ambiente virtual...
    "%PYTHON_EXECUTABLE%" -m venv "%VENV_PATH%"
)

echo Atualizando o Pip...
"%VENV_PATH%\Scripts\python.exe" -m pip install --upgrade pip

REM Instala/Atualiza dependencias
echo Verificando dependencias...
"%VENV_PATH%\Scripts\pip.exe" install --upgrade pip -r requirements.txt

goto start_app
:start_app
REM Forca o modo local ignorando o secrets.toml
set FORCE_LOCAL_MODE=1

REM Executa a aplicacao
echo.
echo Iniciando o Tríplice AI...
"%VENV_DIR%\Scripts\python.exe" desktop_launcher.py
pause