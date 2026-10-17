@echo off
setlocal
title Q3 Map Config Generator - instalador Windows
cd /d "%~dp0"
echo ============================================================
echo   Q3 MAP CONFIG GENERATOR - instalador Windows
echo ============================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
    echo No encontre Python. Instalalo desde https://www.python.org/downloads/
    echo ^(tilda "Add Python to PATH"^) o usa dist\Q3MapConfigGenerator.exe, que no lo necesita.
    pause
    exit /b 1
)
set "Q3=G:\Games\Quake3"
set /p "Q3=Carpeta de Quake 3 (la que tiene baseq3 y cpma) [%Q3%]: "
if not exist "%Q3%\baseq3" echo AVISO: no encuentro "%Q3%\baseq3" ^(lo podes cambiar despues desde la web, en Configuracion^)
set "HOST=127.0.0.1"
set /p "HOST=IP donde corren los servers Q3 (para aplicar next/prev en vivo) [%HOST%]: "
echo.
echo Creando entorno de Python ^(q3cg^) e instalando dependencias...
if not exist q3cg\Scripts\python.exe python -m venv q3cg
q3cg\Scripts\python.exe -m pip install --quiet --upgrade pip
q3cg\Scripts\python.exe -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo ERROR instalando dependencias.
    pause
    exit /b 1
)
q3cg\Scripts\python.exe -c "import json,sys; q=sys.argv[1].rstrip('\\'); json.dump({'baseq3_path': q+'\\baseq3', 'output_path': q+'\\cpma\\cfg-maps', 'ra3_path': q+'\\cpma\\cfg-ra3', 'q3_host': sys.argv[2]}, open('config.json','w'), indent=2)" "%Q3%" "%HOST%"
echo.
echo Listo. config.json creado:
type config.json
echo.
echo Para abrirlo: run.bat  ^(despues entra a http://localhost:5000^)
pause
