@echo off
echo ========================================
echo  Sistema de Verificacion Arquitectonica
echo ========================================
echo.
echo Activando entorno virtual y ejecutando...
echo.

REM Activar entorno virtual
call .venv_clean\Scripts\activate.bat

REM Ejecutar script completo
python start_complete.py

pause
