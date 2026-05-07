@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_model_comparison.ps1"
