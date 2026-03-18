$body = @{
    protocol = "pelco_d"
    connection_type = "serial"
    port = "COM3"
    baudrate = 9600
} | ConvertTo-Json

try {
    $r = Invoke-RestMethod -Uri "http://localhost:8001/api/camera/ptz/connect" `
        -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Output "=== connect result ==="
    $r | ConvertTo-Json -Depth 5
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
}

Write-Output ""
Write-Output "=== ptz status ==="
try {
    $s = Invoke-RestMethod -Uri "http://localhost:8001/api/camera/ptz/status" -TimeoutSec 5
    $s | ConvertTo-Json -Depth 5
} catch {
    Write-Output "STATUS ERROR: $($_.Exception.Message)"
}
