# Azure App Service Deployment Script

# Variables - Update these with your values
$resourceGroupName = "your-resource-group-name"
$appServiceName = "mailbox-agent-app"
$appServicePlanName = "mailbox-agent-plan"
$location = "East US"  # or your preferred region

# Create Resource Group (if it doesn't exist)
Write-Host "Creating resource group..." -ForegroundColor Green
az group create --name $resourceGroupName --location $location

# Create App Service Plan (Linux, Python)
Write-Host "Creating App Service Plan..." -ForegroundColor Green
az appservice plan create --name $appServicePlanName --resource-group $resourceGroupName --sku B1 --is-linux

# Create Web App
Write-Host "Creating Web App..." -ForegroundColor Green
az webapp create --resource-group $resourceGroupName --plan $appServicePlanName --name $appServiceName --runtime "PYTHON|3.11"

# Configure startup command
Write-Host "Configuring startup command..." -ForegroundColor Green
az webapp config set --resource-group $resourceGroupName --name $appServiceName --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 web_agent:app"

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Green
az webapp config appsettings set --resource-group $resourceGroupName --name $appServiceName --settings `
    PROJECT_ENDPOINT="$env:PROJECT_ENDPOINT" `
    MODEL_DEPLOYMENT_NAME="$env:MODEL_DEPLOYMENT_NAME" `
    FLASK_SECRET_KEY="$(New-Guid)"

# Deploy code
Write-Host "Deploying application..." -ForegroundColor Green
az webapp deployment source config-zip --resource-group $resourceGroupName --name $appServiceName --src "deployment.zip"

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Your app will be available at: https://$appServiceName.azurewebsites.net" -ForegroundColor Yellow
