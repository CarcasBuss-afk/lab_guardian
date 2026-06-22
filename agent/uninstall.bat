@echo off
setlocal
REM ============================================================
REM  Disinstallazione agente Lab Guardian (eseguire come ADMIN).
REM  Ferma il servizio, RIPRISTINA il proxy originale, rimuove
REM  firewall/policy e cancella i file.
REM ============================================================

set "INSTALL=%ProgramFiles%\LabGuardian"
set "SERVICE=LabGuardianAgent"

net session >nul 2>&1
if %errorLevel% neq 0 (
  echo Questo script va eseguito come AMMINISTRATORE.
  pause
  exit /b 1
)

echo Arresto del servizio...
"%INSTALL%\nssm.exe" stop %SERVICE% >nul 2>&1

echo Ripristino impostazioni di sistema (proxy, firewall, policy)...
"%INSTALL%\lab-agent.exe" --cleanup

echo Rimozione del servizio...
"%INSTALL%\nssm.exe" remove %SERVICE% confirm >nul 2>&1

echo Cancellazione file...
rmdir /s /q "%INSTALL%" 2>nul

echo.
echo Disinstallazione completata.
echo Se il proxy risultasse ancora attivo, vedere la sezione "Ripristino di
echo emergenza" nel manuale (README).
pause
