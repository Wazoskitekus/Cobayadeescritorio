@echo off
rem Crea dist\Tamacuychi\Tamacuychi.exe (carpeta que usa instalador.iss).
rem Necesita Python 3.9 o posterior instalado.
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller || goto error
python herramientas\exportar_sprites.py || goto error
python -m PyInstaller --noconfirm --clean --onedir --windowed --name Tamacuychi ^
  --icon icono.ico --add-data "sprites;sprites" ^
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtPdf ^
  tamacuychi.pyw || goto error
echo.
echo Listo: dist\Tamacuychi\Tamacuychi.exe
echo Para el instalador: iscc instalador.iss
pause
exit /b 0
:error
echo.
echo Algo ha fallado. Revisa los mensajes de arriba.
pause
exit /b 1
