@echo off
setlocal

rem ============================================================
rem  Academic-Slides-Agent one-click dev launcher
rem  Backend  : .venv python -m asa_api      (http://127.0.0.1:8000)
rem  Frontend : vite dev server in apps/web  (http://localhost:5173)
rem  Each runs in its own window; close the window to stop it.
rem ============================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "WEB_DIR=%ROOT%\apps\web"
set "PY=%ROOT%\.venv\Scripts\python.exe"
if not defined ASA_PORT set "ASA_PORT=8000"
set "FRONTEND_URL=http://localhost:5173"
set "BACKEND_URL=http://127.0.0.1:%ASA_PORT%"

rem ---- preflight checks --------------------------------------
if not exist "%PY%" (
  echo [x] .venv not found at %PY%
  echo     Create it first:  uv sync --all-packages
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [x] npm was not found on PATH. Install Node.js, then run start-dev.bat again.
  pause
  exit /b 1
)

if not exist "%ROOT%\.env" (
  echo [!] .env not found in project root - LLM provider keys may be missing.
  echo     Expected keys: ASA_LLM_PROVIDER / ASA_DEEPSEEK_API_KEY / MINERU_API_KEY ...
)

if not exist "%WEB_DIR%\node_modules" (
  echo ==^> Installing frontend dependencies ^(first run only^)
  pushd "%WEB_DIR%"
  call npm install
  if errorlevel 1 (
    popd
    pause
    exit /b 1
  )
  popd
)

rem ---- backend (skip when the port is already serving) -------
rem findstr note: /c: keeps the spaced pattern literal (a bare space means OR in findstr).
netstat -ano | findstr /r /c:":%ASA_PORT% .*LISTENING" >nul 2>nul
if not errorlevel 1 (
  echo ==^> Backend port %ASA_PORT% already in use - reusing the running server.
) else (
  echo ==^> Starting backend on %BACKEND_URL%
  start "ASA Backend" cmd /k "cd /d "%ROOT%" && set PYTHONUNBUFFERED=1 && "%PY%" -m asa_api"
)

rem ---- wait for the backend to answer ------------------------
set /a TRIES=0
:wait_backend
set /a TRIES+=1
curl -s -o nul "%BACKEND_URL%/jobs"
if not errorlevel 1 goto backend_up
if %TRIES% geq 30 (
  echo [!] Backend did not answer within 30s - check the "ASA Backend" window.
  goto frontend
)
ping -n 2 127.0.0.1 >nul
goto wait_backend
:backend_up
echo ==^> Backend is up.

:frontend
netstat -ano | findstr /r /c:":5173 .*LISTENING" >nul 2>nul
if not errorlevel 1 (
  echo ==^> Frontend port 5173 already in use - reusing the running dev server.
) else (
  echo ==^> Starting frontend on %FRONTEND_URL%
  start "ASA Frontend" cmd /k "cd /d "%WEB_DIR%" && npm run dev"
  ping -n 4 127.0.0.1 >nul
)

echo ==^> Opening %FRONTEND_URL%
start "" "%FRONTEND_URL%"

echo.
echo ============================================================
echo   Academic-Slides-Agent is running
echo     Frontend : %FRONTEND_URL%
echo     Backend  : %BACKEND_URL%  ^(docs: %BACKEND_URL%/docs^)
echo   Close the "ASA Backend" / "ASA Frontend" windows to stop.
echo ============================================================
endlocal
