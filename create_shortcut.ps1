$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\SessionClean Demo.lnk")
$Shortcut.TargetPath = "C:\Users\crist\AppData\Local\Programs\Python\Python312\pythonw.exe"
$Shortcut.Arguments = "C:\Users\crist\sessionclean\demo.py"
$Shortcut.WorkingDirectory = "C:\Users\crist\sessionclean"
$Shortcut.Description = "SessionClean UI Demo"
$Shortcut.Save()
Write-Host "Shortcut created on Desktop"
