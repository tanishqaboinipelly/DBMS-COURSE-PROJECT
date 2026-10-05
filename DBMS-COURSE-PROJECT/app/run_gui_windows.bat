@echo off
REM HIPCMS - Windows launcher. Edit db_config.ini first (MySQL user/password).
cd /d "%~dp0"
python -m pip install -q -r requirements.txt
python -c "import db,sys; ok,msg=db.test_connection(); print(msg); sys.exit(0 if ok else 1)"
if errorlevel 1 (
  echo.
  echo Database not ready. Creating it now with setup_database.py ...
  python setup_database.py
)
python gui_app.py
pause
