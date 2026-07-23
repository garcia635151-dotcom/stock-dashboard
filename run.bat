@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python" "C:\stock-dashboard\main.py" %*
pause
