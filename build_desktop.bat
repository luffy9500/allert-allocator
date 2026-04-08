@echo off
setlocal EnableDelayedExpansion
title Allert Allocator — Build Desktop

echo.
echo  =====================================================
echo   Allert Allocator — Build eseguibile Windows (.exe)
echo  =====================================================
echo.

:: ── Verifica Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato nel PATH.
    echo         Installa Python 3.11+ e aggiungilo al PATH di sistema.
    pause & exit /b 1
)

:: ── Verifica Node.js ─────────────────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Node.js non trovato nel PATH.
    echo         Installa Node.js 18+ da https://nodejs.org/
    pause & exit /b 1
)

echo [1/5] Installazione dipendenze Python...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRORE] pip install fallito.
    pause & exit /b 1
)
echo       OK

echo.
echo [2/5] Build frontend React...
cd frontend
call npm install --silent
if errorlevel 1 ( echo [ERRORE] npm install fallito. & cd .. & pause & exit /b 1 )
call npm run build
if errorlevel 1 ( echo [ERRORE] npm run build fallito. & cd .. & pause & exit /b 1 )
cd ..
echo       OK — frontend/dist/ aggiornato

echo.
echo [3/5] Verifica build frontend...
if not exist "frontend\dist\index.html" (
    echo [ERRORE] frontend\dist\index.html non trovato dopo il build.
    pause & exit /b 1
)
echo       OK

echo.
echo [4/5] Build exe con PyInstaller...
pyinstaller desktop\desktop.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERRORE] PyInstaller fallito. Controlla l'output sopra.
    pause & exit /b 1
)
echo       OK

echo.
echo [5/5] Verifica output...
if not exist "dist\AllertAllocator.exe" (
    echo [ERRORE] dist\AllertAllocator.exe non trovato.
    pause & exit /b 1
)

:: Dimensione file
for %%F in ("dist\AllertAllocator.exe") do set SIZE=%%~zF
set /a SIZE_MB=!SIZE! / 1048576

echo       OK
echo.
echo  =====================================================
echo   BUILD COMPLETATO CON SUCCESSO
echo   File: dist\AllertAllocator.exe  (!SIZE_MB! MB)
echo  =====================================================
echo.
echo  Per testare: doppio clic su dist\AllertAllocator.exe
echo  Nota: WebView2 Runtime richiesto (pre-installato su Win10/11)
echo.
pause
