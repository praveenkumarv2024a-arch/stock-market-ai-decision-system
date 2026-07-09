$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = $WshShell.SpecialFolders.Item("Desktop")
$TargetPath = "http://127.0.0.1:5001"
# Use a browser-like icon (shell32.dll, 14 is globe/network)
$IconLocation = "C:\Windows\System32\shell32.dll,14"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
# For web shortcuts, we might need a .url file instead of .lnk for direct URL
# But .lnk to a URL works by opening default browser.
# Let's actually create a .url file which is more standard for web links
$ShortcutPath = "$DesktopPath\AI Stock Market.url"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "http://127.0.0.1:5001"
$Shortcut.IconFile = "C:\Windows\System32\shell32.dll"
$Shortcut.IconIndex = 14
$Shortcut.Save()

Write-Host "Shortcut created on Desktop: $ShortcutPath"
