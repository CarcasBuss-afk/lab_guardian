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

echo [3/4] Compilazione eseguibile...
pyinstaller --onefile --name lab-agent --collect-all mitmproxy agent.py || goto :error

echo [4/4] Aggiornamento staging USB...
REM  Mantiene usb\ SEMPRE allineato all'ultima build: "build = chiavetta pronta".
REM  Copia l'eseguibile e tutti i .bat/.md, con DUE eccezioni:
REM   - install.bat: nella USB contiene le credenziali reali (API key + password
REM     agente); il template del repo le azzererebbe, quindi NON va sovrascritto.
REM   - build.bat: e' lo script di build, non un file di deploy.
set "USBDIR=%~dp0..\usb"
if not exist "%USBDIR%" mkdir "%USBDIR%"
copy /Y "%~dp0dist\lab-agent.exe" "%USBDIR%\" >nul || goto :error
for %%F in ("%~dp0*.bat") do if /I not "%%~nxF"=="install.bat" if /I not "%%~nxF"=="build.bat" copy /Y "%%F" "%USBDIR%\" >nul
for %%F in ("%~dp0*.md") do copy /Y "%%F" "%USBDIR%\" >nul

echo.
echo Build completata: dist\lab-agent.exe  (copiato anche in usb\)
echo NB: install.bat nella USB NON viene toccato (conserva le credenziali reali).
goto :eof

:error
echo.
echo ERRORE durante la build.
exit /b 1
