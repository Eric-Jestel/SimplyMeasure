@echo off
cd /d "C:\Users\Agilent Cary 60\Documents\SoftwareDev - dont delete\COS-397-Black-2025"
call .venv\Scripts\activate.bat
python ".\components\User_Interface\main.py"
echo.
echo Run Complete
pause >nul