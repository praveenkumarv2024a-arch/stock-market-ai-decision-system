$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")

# 1. Define Paths
$ShortcutName = "AI Stock Market.lnk"
$ShortcutPath = Join-Path $DesktopPath $ShortcutName
$TargetPath = "c:\stock market\open_app.bat"
$IconLocation = "C:\Windows\System32\shell32.dll,14" # Globe icon

# 2. Function to create shortcut
function Create-Shortcut($path) {
    Write-Host "Creating shortcut at: $path"
    $Shortcut = $WshShell.CreateShortcut($path)
    $Shortcut.TargetPath = $TargetPath
    $Shortcut.IconLocation = $IconLocation
    $Shortcut.Description = "Open AI Stock Dashboard"
    $Shortcut.WorkingDirectory = "c:\stock market"
    $Shortcut.Save()
}

# 3. Create on Standard Desktop
Create-Shortcut $ShortcutPath

# 4. Check for OneDrive Desktop and create there too if different
$OneDriveDesktop = "C:\Users\prave\OneDrive\Desktop"
if ((Test-Path $OneDriveDesktop) -and ($OneDriveDesktop -ne $DesktopPath)) {
    $ODShortcutPath = Join-Path $OneDriveDesktop $ShortcutName
    Create-Shortcut $ODShortcutPath
}

Write-Host "Done."
