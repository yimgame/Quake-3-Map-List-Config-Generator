@echo off
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"
set "EXIT_CODE=0"

echo [1/6] Estado actual...
git status
if errorlevel 1 goto :error

echo.
echo [2/6] Agregando cambios (git add .)...
git add .
if errorlevel 1 goto :error

echo.
echo [3/6] Detectando rama actual...
for /f "tokens=*" %%i in ('git branch --show-current') do set "CURRENT_BRANCH=%%i"

if "%CURRENT_BRANCH%"=="" (
    echo No se pudo detectar la rama actual. Usando 'main' por defecto...
    set "CURRENT_BRANCH=main"
    git branch -M main
    if errorlevel 1 goto :error
) else (
    echo Rama detectada: %CURRENT_BRANCH%
)

echo.
set "COMMIT_MSG="
set /p "COMMIT_MSG=[4/6] Mensaje del commit: "
if not defined COMMIT_MSG (
    echo ERROR: Debes ingresar un mensaje de commit.
    set "EXIT_CODE=1"
    goto :end
)

echo.
echo [5/6] Creando commit...
git commit -m "%COMMIT_MSG%"
if errorlevel 1 goto :error

echo.
echo [6/6] Enviando a origin/%CURRENT_BRANCH%...
git push -u origin %CURRENT_BRANCH%
if errorlevel 1 goto :error

goto :summary

:error
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo ERROR: Fallo un comando git. Codigo !EXIT_CODE!.
echo Revisa los mensajes de arriba.
goto :summary

:summary
echo.
echo ===== RESUMEN =====
git status -sb
echo.
git log -1 --oneline
echo ===================

:end
echo.
pause
exit /b %EXIT_CODE%