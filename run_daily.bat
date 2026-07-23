@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================
REM  A股每日分析看板 - 自动运行脚本
REM  由 Windows 任务计划程序每天 9:00 触发
REM ============================================

set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe
set SCRIPT=C:\stock-dashboard\main.py
set LOG_DIR=C:\stock-dashboard\logs
set TODAY=%DATE:~0,4%-%DATE:~5,2%-%DATE:~8,2%

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOGFILE=%LOG_DIR%\daily_%TODAY%.log

echo ============================================ > "%LOGFILE%"
echo  A股每日分析看板 - 自动运行 >> "%LOGFILE%"
echo  日期: %TODAY% %TIME% >> "%LOGFILE%"
echo ============================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

REM ---- 运行看板生成 ----
echo [%TIME%] 开始生成看板... >> "%LOGFILE%"
"%PYTHON%" "%SCRIPT%" --real >> "%LOGFILE%" 2>&1
set EXIT_CODE=%ERRORLEVEL%

echo. >> "%LOGFILE%"
echo [%TIME%] 完成, 退出码: %EXIT_CODE% >> "%LOGFILE%"

REM ---- 检查结果 ----
if %EXIT_CODE% EQU 0 (
    echo [%TIME%] SUCCESS - 看板已生成到 C:\stock-dashboard\output\latest.html >> "%LOGFILE%"
) else (
    echo [%TIME%] FAILED - 请检查日志排查错误 >> "%LOGFILE%"
)

REM ---- 保留最近30天日志 ----
forfiles /p "%LOG_DIR%" /m "daily_*.log" /d -30 /c "cmd /c del @file" 2>nul

exit /b %EXIT_CODE%
