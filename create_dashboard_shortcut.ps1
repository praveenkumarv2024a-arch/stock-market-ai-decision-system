$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = $WshShell.SpecialFolders.Item("Desktop")
$ShortcutPath = "$DesktopPath\Start AI Trade.lnk"

# Create Shortcut to the Batch File
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "c:\stock market\start_dashboard.bat"
$Shortcut.WorkingDirectory = "c:\stock market"
$Shortcut.WindowStyle = 1 # Normal window
$Shortcut.Description = "Launch AI Stock Market Dashboard"
# Use a graph-like icon if possible, or generic
$Shortcut.IconLocation = "C:\Windows\System32\shell32.dll,43" 
$Shortcut.Save()

Write-Host "Shortcut created: $ShortcutPath"
