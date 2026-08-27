@echo off
set "SYNCTHING_HOME={{USER_HOME}}\AppData\Local\Syncthing"
set "SYNCTHING_EXE={{USER_HOME}}\AppData\Local\Microsoft\WinGet\Packages\Syncthing.Syncthing_Microsoft.Winget.Source_8wekyb3d8bbwe\syncthing-windows-amd64-v2.0.16\syncthing.exe"
cd /d "{{USER_HOME}}\AppData\Local\Syncthing"
"%SYNCTHING_EXE%" serve --no-browser --no-console --log-file=default --home "%SYNCTHING_HOME%"
