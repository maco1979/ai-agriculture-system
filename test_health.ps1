# Test health check endpoint
$url = "http://localhost:8001/api/system/health"

Write-Host "Testing health check endpoint: $url"

# Use Invoke-WebRequest instead of Invoke-RestMethod for better error handling
$response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing

Write-Host "Status Code: $($response.StatusCode)"
Write-Host "Response Content: $($response.Content)"