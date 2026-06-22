@echo off
REM ============================================================
REM  Build dell'agente Lab Guardian in eseguibile autonomo.
REM  Da eseguire UNA VOLTA sul PC di sviluppo (richiede Python).
REM  Produce: dist\lab-agent.exe
REM ============================================================
cd /d "%~dp0"

echo [1/3] Creazione ambiente virtuale di build...
python -m venv .buildenv || goto :error
call .buildenv\Scripts\activate.bat

echo [2/3] Installazione dipendenze...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt || goto :error

echo [3/3] Compilazione eseguibile...
pyinstaller --onefile --name lab-agent --collect-all mitmproxy agent.py || goto :error

echo.
echo Build completata: dist\lab-agent.exe
echo Copia sulla chiavetta: lab-agent.exe, nssm.exe, install.bat, uninstall.bat, README.
goto :eof

:error
echo.
echo ERRORE durante la build.
exit /b 1
