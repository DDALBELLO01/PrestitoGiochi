@echo off
echo ===============================================
echo Il Sentiero dei Draghi - Avvio Server
echo ===============================================
echo.
echo Avvio del server Flask...
echo Il browser si aprirà automaticamente su http://localhost:5000
echo.
echo Premi CTRL+C per fermare il server
echo ===============================================
echo.

cd /d "%~dp0"
start http://localhost:5000
python app.py

pause
