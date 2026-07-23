$WS = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WS.CreateShortcut("$Desktop\A股每日看板.lnk")
$Shortcut.TargetPath = "C:\stock-dashboard\output\latest.html"
$Shortcut.Save()
Write-Host "桌面快捷方式已创建: A股每日看板"
