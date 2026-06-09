@echo off
title WorkHunter

echo ========================================
echo  WorkHunter - Iniciando servicos
echo ========================================
echo.

set "VENV_DIR=D:\Work\backend\venv"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"

:: Verificar venv
if not exist "%PYTHON%" (
    echo [ERRO] Venv nao encontrado em %VENV_DIR%
    echo        Execute: python -m venv %VENV_DIR%
    pause
    exit /b 1
)
echo [OK] Python: %PYTHON%
%PYTHON% --version

:: Verificar e instalar dependencias do backend
echo [Backend] Verificando dependencias...
%PYTHON% -m pip install -r D:\Work\backend\requirements.txt --quiet --disable-pip-version-check
echo [Backend] Instalando Playwright browsers...
%PYTHON% -m playwright install chromium

:: Iniciar Backend (com terminal visivel + log)
echo [Backend] Iniciando FastAPI na porta 8070...
start "WorkHunter-Backend" cmd /c "cd /d D:\Work\backend && %PYTHON% -m uvicorn main:app --reload --port 8070 --log-level debug"

:: Esperar 3s e verificar se backend subiu
timeout /t 3 /nobreak >nul
powershell -Command "if (-not (Get-CimInstance Win32_Process -Filter \"Name='python.exe' AND CommandLine LIKE '%%uvicorn%%'\" -ErrorAction SilentlyContinue)) { Write-Host '[AVISO] Backend pode nao ter iniciado. Verifique backend\backend.log' -ForegroundColor Yellow } else { Write-Host '[OK] Backend rodando' -ForegroundColor Green }"

:: Instalar dependencias do frontend se necessario
if not exist "D:\Work\frontend\node_modules" (
    echo [Frontend] node_modules nao encontrado. Instalando dependencias...
    cd /d D:\Work\frontend
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo [ERRO] npm install falhou. Verifique o erro acima.
        pause
        exit /b 1
    )
    cd /d D:\Work
)

:: Iniciar Frontend
echo [Frontend] Iniciando Next.js na porta 3000...
start "WorkHunter-Frontend" cmd /c "cd /d D:\Work\frontend && npm run dev"

echo.
echo ========================================
echo  Backend:  http://localhost:8070
echo  Frontend: http://localhost:3000
echo  Health:   http://localhost:8070/api/v1/sistema/health
echo ========================================
echo.
echo  Pressione qualquer tecla para parar tudo...
echo  (ou feche esta janela)
pause >nul

echo.
echo Parando servicos...
taskkill /f /fi "WindowTitle eq WorkHunter-Backend" >nul 2>&1
taskkill /f /fi "WindowTitle eq WorkHunter-Frontend" >nul 2>&1
echo Servicos parados.
