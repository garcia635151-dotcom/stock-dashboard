@echo off
schtasks /delete /tn "A-Stock-Dashboard" /f
if %ERRORLEVEL% EQU 0 (
    echo 定时任务已删除
) else (
    echo 未找到定时任务，或已删除
)
pause
