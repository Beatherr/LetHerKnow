param (
    [string]$action,
    [string]$target
)

function Get-TargetProcess {
    param ([string]$scriptName)
    Get-CimInstance Win32_Process | Where-Object { 
        ($_.Name -eq "python.exe" -or $_.Name -eq "pythonw.exe") -and ($_.CommandLine -like "*$scriptName*")
    }
}

if ($action -eq "status") {
    $proc = Get-TargetProcess $target
    if ($proc) { exit 0 } else { exit 1 }
}
elseif ($action -eq "stop") {
    $proc = Get-TargetProcess $target
    if ($proc) {
        $proc | Stop-Process -Force
    }
}