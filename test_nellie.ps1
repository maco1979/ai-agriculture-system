# Test Nellie reasoning endpoint
$url = "http://localhost:8001/api/nellie/reason"

Write-Host "Testing Nellie reasoning endpoint: $url"

# Prepare the request body
$body = @{
    query = "预测小麦产量"
    context = @{
        CropType = "wheat"
        GrowthStage = "tillering"
    }
} | ConvertTo-Json

# Send the request
$response = Invoke-WebRequest -Uri $url -Method POST -Body $body -ContentType "application/json" -TimeoutSec 5 -UseBasicParsing

Write-Host "Status Code: $($response.StatusCode)"
Write-Host "Response Content: $($response.Content)"