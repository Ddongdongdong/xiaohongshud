param()

$pids2 = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Sort-Object -Unique
foreach ($procId in $pids2) {
    if ($procId -gt 0) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "Killed PID $procId (port 8000)"
    }
}

Start-Sleep -Seconds 2

$startScript = "C:\Users\Administrator\Desktop\新建文件夹\XiaohongshuSkills\start_backend.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $startScript

Write-Host "后端已重启，等待 5 秒..."
Start-Sleep -Seconds 5
Write-Host "Done."
