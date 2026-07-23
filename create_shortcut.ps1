$WS = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WS.CreateShortcut("$Desktop\AStockDashboard.lnk")
$Shortcut.TargetPath = "C:\stock-dashboard\output\latest.html"
$Shortcut.Save()
Write-Host "Desktop shortcut created: AStockDashboard.lnk"
