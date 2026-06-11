@echo off
cd /d "%~dp0.."
echo ============================================
echo  Generate listening audio: JSON to MP3
echo  (Sheng Cheng Yin Pin - needs internet)
echo ============================================
where py >nul 2>nul
if %errorlevel%==0 (
  py tools\make_audio_v2.py %1
) else (
  python tools\make_audio_v2.py %1
)
echo.
pause
