Set WshShell = CreateObject("WScript.Shell") 
WshShell.Run chr(34) & "c:\stock market\start_dashboard.bat" & Chr(34), 0
Set WshShell = Nothing
