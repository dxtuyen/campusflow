@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Chua co moi truong Python .venv cho Windows.
    echo Mo vault CampusFlow-Vault, muc Chay tren Windows de cai dat.
    exit /b 1
)

if not "%~1"=="" goto run_python

if not exist "app.py" (
    echo Chua co app.py. Can hoan tat source theo task trong Obsidian.
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1
exit /b %errorlevel%

:run_python
".venv\Scripts\python.exe" %*
exit /b %errorlevel%