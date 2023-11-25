@echo off
set PYTHONPATH=%~dp0/../..
set PITCHDATADEMOPATH=%~dp0
python -m mlb.scripts.pitch_data_harvester -c %~dp0demo_config.ini -g W