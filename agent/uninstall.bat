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

REM Rete di sicurezza: ripristina firewall E proxy ANCHE se il cleanup sopra
REM fallisce. Senza questo, un PC potrebbe restare bloccato dopo aver cancellato
REM la cartella (niente piu' exe per rimediare).
echo Ripristino firewall di sicurezza...
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "Set-NetFirewallProfile -All -DefaultOutboundAction Allow; Remove-NetFirewallRule -DisplayName 'LabGuardian*' -ErrorAction SilentlyContinue" >nul 2>&1

echo Ripristino proxy di sistema di sicurezza...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyOverride /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxySettingsPerUser /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Internet Explorer\Control Panel" /v Proxy /f >nul 2>&1

echo Rimozione del servizio...
"%INSTALL%\nssm.exe" remove %SERVICE% confirm >nul 2>&1

echo Cancellazione file...
rmdir /s /q "%INSTALL%" 2>nul

echo.
echo Disinstallazione completata.
echo Se il proxy risultasse ancora attivo, vedere la sezione "Ripristino di
echo emergenza" nel manuale (README).
pause
