@echo off
chcp 65001 >nul
echo ========================================
echo  安装 A股看板定时任务
echo  每天工作日 09:00 自动运行
echo ========================================
echo.

REM 删除旧任务
schtasks /delete /tn "A-Stock-Dashboard" /f 2>nul

REM 创建新任务
schtasks /create /tn "A-Stock-Dashboard" /tr "C:\stock-dashboard\run_daily.bat" /sc WEEKLY /d MON,TUE,WED,THU,FRI /st 09:00 /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 定时任务已创建！
    echo   任务名: A-Stock-Dashboard
    echo   时间: 周一至周五 09:00
    echo   脚本: C:\stock-dashboard\run_daily.bat
    echo   日志: C:\stock-dashboard\logs\
    echo.
    echo 管理命令:
    echo   查看: schtasks /query /tn "A-Stock-Dashboard" /v
    echo   手动跑: schtasks /run /tn "A-Stock-Dashboard"
    echo   删除: schtasks /delete /tn "A-Stock-Dashboard" /f
) else (
    echo.
    echo [失败] 请右键此文件 → 以管理员身份运行
)

pause
