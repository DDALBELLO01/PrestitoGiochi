@echo off
chcp 65001 >nul
echo ================================================================
echo Il Sentiero dei Draghi - Creazione Eseguibile
echo ================================================================
echo.

cd /d "%~dp0"

REM Termina processi Python in esecuzione
echo [1/5] Chiusura processi in esecuzione...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM SentieroDraghi.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

REM Pulizia vecchie build
echo [2/5] Pulizia cartelle precedenti...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "SentieroDraghi.spec" del /q "SentieroDraghi.spec"
if exist "Il Sentiero dei Draghi - Prestito Giochi" rmdir /s /q "Il Sentiero dei Draghi - Prestito Giochi"

REM Esecuzione PyInstaller
echo [3/5] Creazione eseguibile con PyInstaller...
echo      (Questo richiederà alcuni minuti...)
echo.

python -m PyInstaller ^
    --name=SentieroDraghi ^
    --onefile ^
    --console ^
    --icon=NONE ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "ISTRUZIONI.md;." ^
    --hidden-import=flask ^
    --hidden-import=flask.cli ^
    --hidden-import=flask.json ^
    --hidden-import=flask.json.tag ^
    --hidden-import=werkzeug ^
    --hidden-import=werkzeug.security ^
    --hidden-import=werkzeug.serving ^
    --hidden-import=click ^
    --hidden-import=itsdangerous ^
    --hidden-import=markupsafe ^
    --hidden-import=flask_sqlalchemy ^
    --hidden-import=flask_wtf ^
    --hidden-import=flask_wtf.csrf ^
    --hidden-import=sqlalchemy ^
    --hidden-import=sqlalchemy.ext.declarative ^
    --hidden-import=sqlalchemy.sql.default_comparator ^
    --hidden-import=sqlalchemy.orm ^
    --hidden-import=sqlalchemy.engine ^
    --hidden-import=wtforms ^
    --hidden-import=wtforms.validators ^
    --hidden-import=wtforms.fields ^
    --hidden-import=jinja2 ^
    --hidden-import=jinja2.ext ^
    --hidden-import=email_validator ^
    --hidden-import=dns ^
    --hidden-import=dns.resolver ^
    --collect-all=flask ^
    --collect-all=werkzeug ^
    app.py

if errorlevel 1 (
    echo.
    echo ================================================================
    echo ERRORE durante la creazione dell'eseguibile!
    echo ================================================================
    pause
    exit /b 1
)

REM Creazione struttura di distribuzione
echo.
echo [4/5] Creazione struttura di distribuzione...
mkdir "Il Sentiero dei Draghi - Prestito Giochi"
mkdir "Il Sentiero dei Draghi - Prestito Giochi\database"

REM Spostamento cartelle build e dist
echo [5/5] Organizzazione file...
move "build" "Il Sentiero dei Draghi - Prestito Giochi\build" >nul
move "dist" "Il Sentiero dei Draghi - Prestito Giochi\dist" >nul
if exist "SentieroDraghi.spec" move "SentieroDraghi.spec" "Il Sentiero dei Draghi - Prestito Giochi\" >nul

REM Copia file essenziali per la distribuzione
if exist "instance\prestiti.db" (
    copy "instance\prestiti.db" "Il Sentiero dei Draghi - Prestito Giochi\database\prestiti.db" >nul
)
if exist "ISTRUZIONI.md" (
    copy "ISTRUZIONI.md" "Il Sentiero dei Draghi - Prestito Giochi\ISTRUZIONI.md" >nul
)

REM Crea script di avvio
echo @echo off > "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo cd /d "%%~dp0" >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo =============================================== >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo Il Sentiero dei Draghi - Avvio Server >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo =============================================== >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo. >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo Avvio del server... >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo Il browser si aprira automaticamente. >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo. >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo Premi CTRL+C per fermare il server >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo =============================================== >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo echo. >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo start http://localhost:5000 >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo dist\SentieroDraghi.exe >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo pause >> "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"

REM Crea README
echo Il Sentiero dei Draghi - Sistema Gestione Prestiti > "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo ================================================== >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo. >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo ISTRUZIONI PER L'AVVIO: >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo. >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo 1. Fai doppio click su AVVIA.bat >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo 2. Il server si avviera automaticamente >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo 3. Il browser si aprira su http://localhost:5000 >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo. >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo NOTA: >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo - Il database si trova in: database\prestiti.db >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo - Le istruzioni sono in: ISTRUZIONI.md (modificabile) >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo - Eseguibile: dist\SentieroDraghi.exe >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo - File di build: build\ >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo. >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"
echo Per backup: copia la cartella 'database' >> "Il Sentiero dei Draghi - Prestito Giochi\README.txt"

echo.
echo ================================================================
echo BUILD COMPLETATA CON SUCCESSO!
echo ================================================================
echo.
echo Struttura creata in: "Il Sentiero dei Draghi - Prestito Giochi\"
echo.
echo Contenuto:
echo   - dist\SentieroDraghi.exe  (eseguibile)
echo   - build\                   (file di build PyInstaller)
echo   - database\prestiti.db     (database SQLite)
echo   - ISTRUZIONI.md            (guida utente - modificabile)
echo   - AVVIA.bat                (script di avvio rapido)
echo   - README.txt               (istruzioni)
echo.
echo Per distribuire: copia l'intera cartella "Il Sentiero dei Draghi - Prestito Giochi"
echo.
echo Per avviare: doppio click su "Il Sentiero dei Draghi - Prestito Giochi\AVVIA.bat"
echo.
echo ================================================================

pause
