# ============================================
#  A股每日分析看板 - 创建 Windows 定时任务
#  每天 9:00 AM 自动生成看板（仅工作日）
#  右键 → "使用 PowerShell 运行" 或管理员终端执行:
#    powershell -ExecutionPolicy Bypass -File setup_schedule.ps1
# ============================================

$TaskName = "A股每日分析看板"
$ScriptPath = "C:\stock-dashboard\run_daily.bat"
$WorkingDir = "C:\stock-dashboard"
$LogDir = "C:\stock-dashboard\logs"

# 确保日志目录存在
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# 删除旧任务（如果存在）
$existing = schtasks /query /tn "$TaskName" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "删除已有定时任务: $TaskName"
    schtasks /delete /tn "$TaskName" /f 2>$null
}

# 创建新任务
# /sc WEEKLY /d MON,TUE,WED,THU,FRI  = 每周一到周五
# /st 09:00 = 每天9:00 AM
Write-Host "正在创建定时任务: $TaskName"
Write-Host "  脚本: $ScriptPath"
Write-Host "  时间: 每个工作日 09:00 AM"

schtasks /create `
    /tn "$TaskName" `
    /tr "cmd /c `"$ScriptPath`"" `
    /sc WEEKLY `
    /d MON,TUE,WED,THU,FRI `
    /st 09:00 `
    /ru SYSTEM `
    /f

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  定时任务创建成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "任务名称: $TaskName"
    Write-Host "运行时间: 每个工作日 09:00 AM"
    Write-Host "运行脚本: $ScriptPath"
    Write-Host "日志目录: $LogDir"
    Write-Host ""
    Write-Host "管理命令:"
    Write-Host "  查看任务: schtasks /query /tn `"$TaskName`" /v"
    Write-Host "  手动运行: schtasks /run /tn `"$TaskName`""
    Write-Host "  删除任务: schtasks /delete /tn `"$TaskName`" /f"
    Write-Host ""
    Write-Host "下次运行时间:"
    schtasks /query /tn "$TaskName" /fo LIST | Select-String "Next Run"
} else {
    Write-Host ""
    Write-Host "创建失败！请以管理员身份运行此脚本：" -ForegroundColor Red
    Write-Host "  1. 右键 PowerShell → 以管理员身份运行" -ForegroundColor Yellow
    Write-Host "  2. 执行: powershell -ExecutionPolicy Bypass -File C:\stock-dashboard\setup_schedule.ps1" -ForegroundColor Yellow
}
