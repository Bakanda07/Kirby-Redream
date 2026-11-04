@echo off
rem Installs Kirby: Redream from your own game files: a private Python, the installer window, then the build.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap.ps1" %*
