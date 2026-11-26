@echo off
rem Arranca la cobaya desde el código (instala lo necesario la primera vez).
cd /d "%~dp0"
python -c "import PySide6, send2trash" 2>nul || python -m pip install -r requirements.txt
start "" pythonw tamacuychi.pyw
