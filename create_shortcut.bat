@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Creating a desktop shortcut for the Ship Mechanic Assistant...
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Desktop'); $lnk=Join-Path $d 'Ship Mechanic Assistant.lnk'; $s=$ws.CreateShortcut($lnk); $s.TargetPath='%~dp0start.bat'; $s.WorkingDirectory='%~dp0'; $s.Description='Ship Mechanic Assistant'; $s.Save()"
echo Done. Look for "Ship Mechanic Assistant" on your Desktop.
pause
