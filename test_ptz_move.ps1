# 查询云台当前状态
Write-Output "=== PTZ Status ==="
$s = Invoke-RestMethod "http://localhost:8001/api/camera/ptz/status" -TimeoutSec 5
$s | ConvertTo-Json -Depth 5

# 如果未连接先连接（模拟模式）
if (-not $s.data.connected) {
    Write-Output "`n=== Connecting... ==="
    $body = @{ protocol = "pelco_d"; connection_type = "serial"; port = "COM3"; baudrate = 9600 } | ConvertTo-Json
    $c = Invoke-RestMethod "http://localhost:8001/api/camera/ptz/connect" -Method POST -Body $body -ContentType "application/json"
    $c | ConvertTo-Json -Depth 3
}

# 手动发送 pan_right 动作（直接测试execute_action通路）
Write-Output "`n=== Move RIGHT (speed=50) ==="
$moveBody = @{ action = "pan_right"; speed = 50 } | ConvertTo-Json
$m = Invoke-RestMethod "http://localhost:8001/api/camera/ptz/action" -Method POST -Body $moveBody -ContentType "application/json"
$m | ConvertTo-Json -Depth 5

Start-Sleep 1

# 查询位置变化
Write-Output "`n=== Position After Move ==="
$s2 = Invoke-RestMethod "http://localhost:8001/api/camera/ptz/status" -TimeoutSec 5
$s2.data | ConvertTo-Json -Depth 3

# 停止
Write-Output "`n=== STOP ==="
$stopBody = @{ action = "stop"; speed = 0 } | ConvertTo-Json
$st = Invoke-RestMethod "http://localhost:8001/api/camera/ptz/action" -Method POST -Body $stopBody -ContentType "application/json"
$st | ConvertTo-Json -Depth 3
