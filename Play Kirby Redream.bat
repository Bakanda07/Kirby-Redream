@echo off
rem Starts Kirby: Redream (the Desktop shortcut starts the game directly).
if exist "%~dp0deps\python\python.exe" (
  "%~dp0deps\python\python.exe" "%~dp0scripts\run.py" %*
) else (
  python "%~dp0scripts\run.py" %*
)
