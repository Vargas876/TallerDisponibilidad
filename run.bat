@echo off
setlocal
set "ROOT=%~dp0"
set "PY="

if exist "%LocalAppData%\Python\bin\python.exe" set "PY=%LocalAppData%\Python\bin\python.exe"
if not defined PY if exist "%LocalAppData%\Python\bin\python3.exe" set "PY=%LocalAppData%\Python\bin\python3.exe"
if not defined PY if exist "C:\Python312\python.exe" set "PY=C:\Python312\python.exe"
if not defined PY (
    echo [ERROR] No se encontro Python.
    echo Instalalo desde https://www.python.org/downloads/ o agrega su ruta al PATH.
    pause
    exit /b 1
)

echo Usando Python: %PY%
pushd "%ROOT%"
"%PY%" run.py
popd
endlocal