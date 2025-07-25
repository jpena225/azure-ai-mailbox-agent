# Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Green

# Remove existing deployment.zip if it exists
if (Test-Path "deployment.zip") {
    Remove-Item "deployment.zip"
}

# Create zip file with all necessary files
$filesToInclude = @(
    "web_agent.py",
    "requirements.txt", 
    "startup.txt",
    "templates\*",
    ".env"
)

# Check if all files exist
foreach ($file in $filesToInclude) {
    if ($file -eq "templates\*") {
        if (-not (Test-Path "templates")) {
            Write-Error "Templates directory not found!"
            exit 1
        }
    } elseif (-not (Test-Path $file)) {
        Write-Warning "File not found: $file"
    }
}

# Create the zip file
Compress-Archive -Path $filesToInclude -DestinationPath "deployment.zip" -Force

Write-Host "Deployment package created: deployment.zip" -ForegroundColor Green
Write-Host "Package contents:" -ForegroundColor Yellow
Get-ChildItem -Path . -Include $filesToInclude -Recurse | ForEach-Object { Write-Host "  - $($_.Name)" }
