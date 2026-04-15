@echo off
REM ── Stock Dashboard — Arranque Windows ───────────────────────────────────

cd /d "%~dp0"

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   📈  Stock Dashboard — Value Investing  
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Comprobar Python
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no encontrado. Instala Python 3 desde https://python.org
    pause
    exit /b 1
)

echo [INFO] Verificando dependencias...
python -m pip install --quiet flask flask-cors yfinance pandas gunicorn

echo.
echo [INFO] Arrancando servidor en http://localhost:5000 ...
echo        Pulsa Ctrl+C en esta ventana para detener.
echo.

REM Abrir navegador tras 3 segundos
start /b cmd /c "timeout /t 3 >nul && start http://localhost:5000"

REM Lanzar Flask
set FLASK_ENV=development
python app.py

pause
