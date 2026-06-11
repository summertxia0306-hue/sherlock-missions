@echo off
cd /d "%~dp0"
echo ============================================
echo  Local preview: Sherlock Listening App
echo  Browser opens http://localhost:8501
echo  Parent view: add ?mode=parent  (local password: xlk2026)
echo  To stop: press Ctrl+C in this window
echo ============================================
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
%PY% -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo First run: installing streamlit, 1-2 minutes...
  %PY% -m pip install -q streamlit
)
if not exist "static\audio\listening\W01D01\q01.mp3" (
  echo.
  echo [!] Audio not generated yet.
  echo     Please double-click the bat file in tools folder first,
  echo     then run this file again.
  echo.
  pause
  exit /b 1
)
%PY% -m streamlit run app.py
pause
