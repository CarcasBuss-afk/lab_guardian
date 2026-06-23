@echo off
setlocal
REM ============================================================
REM  Installazione agente Lab Guardian (eseguire come ADMIN).
REM  Da lanciare dalla chiavetta USB su ogni PC del laboratorio.
REM ============================================================

REM --- Costanti: COMPILARE UNA VOLTA prima di copiare su USB ---
set "APIKEY=LA_TUA_NEXT_PUBLIC_FIREBASE_API_KEY"
set "DBURL=https://lab-guardian-default-rtdb.europe-west1.firebasedatabase.app"
set "AGENTEMAIL=agent@lab-guardian.example"
set "AGENTPASS=PASSWORD_ACCOUNT_AGENTE"
set "PROXYADDR=127.0.0.1:8080"
REM -------------------------------------------------------------

set "INSTALL=%ProgramFiles%\LabGuardian"
set "SRC=%~dp0"
set "SERVICE=LabGuardianAgent"

REM Verifica privilegi amministratore
net session >nul 2>&1
if %errorLevel% neq 0 (
  echo Questo installer va eseguito come AMMINISTRATORE.
  pause
  exit /b 1
)

REM Chiede il nome dell'aula
set "ROOM="
set /p "ROOM=Nome aula per questo PC (es. aula3): "
if "%ROOM%"=="" (
  echo Nome aula obbligatorio.
  pause
  exit /b 1
)

echo Installazione in "%INSTALL%"...
mkdir "%INSTALL%" 2>nul
copy /Y "%SRC%lab-agent.exe" "%INSTALL%\" >nul || goto :error
copy /Y "%SRC%nssm.exe" "%INSTALL%\" >nul || goto :error

REM Genera config.json
> "%INSTALL%\config.json" echo {
>> "%INSTALL%\config.json" echo   "apiKey": "%APIKEY%",
>> "%INSTALL%\config.json" echo   "databaseURL": "%DBURL%",
>> "%INSTALL%\config.json" echo   "room": "%ROOM%",
>> "%INSTALL%\config.json" echo   "agentEmail": "%AGENTEMAIL%",
>> "%INSTALL%\config.json" echo   "agentPassword": "%AGENTPASS%",
>> "%INSTALL%\config.json" echo   "proxyAddress": "%PROXYADDR%",
>> "%INSTALL%\config.json" echo   "heartbeatSeconds": 30
>> "%INSTALL%\config.json" echo }

REM Limita l'accesso all'INTERA cartella (solo SYSTEM e Amministratori):
REM gli studenti non potranno leggere config, log, backup ne' i binari.
REM I file creati dopo (agent.log, proxy_backup.json) ereditano questi permessi.
icacls "%INSTALL%" /inheritance:r /grant:r "SYSTEM:F" "Administrators:F" /T >nul

REM Registra ed avvia il servizio come SYSTEM
"%INSTALL%\nssm.exe" install %SERVICE% "%INSTALL%\lab-agent.exe" || goto :error
"%INSTALL%\nssm.exe" set %SERVICE% AppDirectory "%INSTALL%" >nul
"%INSTALL%\nssm.exe" set %SERVICE% Start SERVICE_AUTO_START >nul
"%INSTALL%\nssm.exe" set %SERVICE% ObjectName LocalSystem >nul
"%INSTALL%\nssm.exe" start %SERVICE% >nul

echo.
echo Agente installato e avviato per l'aula "%ROOM%".
echo NB: se un antivirus segnala lab-agent.exe, aggiungere un'eccezione per "%INSTALL%".
pause
goto :eof

:error
echo.
echo ERRORE durante l'installazione.
pause
exit /b 1
