@echo off
setlocal
cd /d "%~dp0..\.."
set CONFIG_PATH=%~dp0unified_model_eval_config.json
if exist "%~dp0unified_model_eval_config.local.json" set CONFIG_PATH=%~dp0unified_model_eval_config.local.json
call "%CD%\python.cmd" -B "%CD%\scripts\run_unified_model_eval.py" --config-file "%CONFIG_PATH%" --report-dir "%~dp0reports"
