; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
!macro KillBrowserMcpFleetProcesses
  DetailPrint "Stopping browser-mcp processes..."
  ExecWait 'taskkill /F /IM browser-mcp-backend.exe /T' $0
  ExecWait 'taskkill /F /IM browser-mcp-native.exe /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "browser-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "browser-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "browser-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "browser-mcp-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillBrowserMcpFleetProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillBrowserMcpFleetProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  IfFileExists "$INSTDIR\resources\install-mcp-clients.ps1" 0 mcp_hook_done
    DetailPrint "Optional: register browser-mcp in Cursor / Claude Desktop"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\resources\install-mcp-clients.ps1" -Interactive'
  mcp_hook_done:
!macroend
