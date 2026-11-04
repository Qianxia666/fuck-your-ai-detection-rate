@echo off
setlocal
cd /d "%~dp0"
python packaging\build_exe.py %*
if errorlevel 1 (
  echo.
  echo Build failed. Review the messages above.
  pause
  exit /b 1
)
echo.
pause
