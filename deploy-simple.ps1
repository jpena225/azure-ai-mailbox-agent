# Simple deployment using curl (works without Azure CLI)
# Replace YOUR-APP-NAME with your actual app service name

$appName = "YOUR-APP-NAME"  # Replace with your app service name
$username = "YOUR-DEPLOYMENT-USERNAME"  # Get from Deployment Center > Deployment Credentials
$password = "YOUR-DEPLOYMENT-PASSWORD"  # Get from Deployment Center > Deployment Credentials

# Deploy using REST API
$uri = "https://$appName.scm.azurewebsites.net/api/zipdeploy"
$zipFile = "deployment.zip"

Write-Host "Deploying $zipFile to $appName..." -ForegroundColor Green

# Create credentials
$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(("{0}:{1}" -f $username, $password)))

# Deploy
Invoke-RestMethod -Uri $uri -Method Post -InFile $zipFile -ContentType "application/zip" -Headers @{Authorization=("Basic {0}" -f $base64AuthInfo)}

Write-Host "Deployment complete!" -ForegroundColor Green
