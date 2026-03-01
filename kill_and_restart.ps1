param()

# 杀掉占用 8000 和 5173 端口的所有进程
foreach ($port in @(8000, 5173)) {
    $pids = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess | Sort-Object -Unique
    foreach ($procId in $pids) {
        if ($procId -gt 0) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Write-Host "Killed PID $procId (port $port)"
        }
    }
}

Start-Sleep -Seconds 2

# 检查是否清理干净
$remaining = Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "Warning: some ports still in use, forcing..."
    foreach ($conn in $remaining) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

# 启动后端（通过 start_backend.ps1 设置 NO_PROXY，避免 requests 走代理访问 CDP）
$startScript = "C:\Users\Administrator\Desktop\新建文件夹\XiaohongshuSkills\start_backend.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $startScript

Start-Sleep -Seconds 3

# 启动前端
$frontendDir = "C:\Users\Administrator\Desktop\新建文件夹\XiaohongshuSkills\frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendDir'; npm run dev"

Write-Host "已启动！"
Write-Host "前端: http://localhost:5173"
Write-Host "后端: http://localhost:8000/docs"
