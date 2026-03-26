<#
.SYNOPSIS
Deploys the Graph-Based Data Modeling System.
Backend -> Render
Frontend -> Vercel

.DESCRIPTION
This script uses the Vercel CLI to deploy the frontend and provides instructions for the Render backend.
#>

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "🚀 Dodge AI - Deployment Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Check for Node.js
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ npm is not installed. Please install Node.js first." -ForegroundColor Red
    exit
}

# 2. Deploy Frontend to Vercel
Write-Host "`n[1/2] Deploying Frontend to Vercel...`n" -ForegroundColor Yellow

# Install vercel CLI globally if not present
if (-not (Get-Command "vercel" -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Vercel CLI..."
    npm install -g vercel
}

Write-Host "Running Vercel Deploy. Please follow the login prompts if you are not authenticated."
Set-Location -Path ".\frontend"
vercel --prod
Set-Location -Path ".."

Write-Host "`n✅ Frontend Deployment Triggered!" -ForegroundColor Green

# 3. Deploy Backend to Render
Write-Host "`n[2/2] Deploying Backend to Render...`n" -ForegroundColor Yellow

Write-Host "Since Render connects directly to your GitHub repository, we have included a 'render.yaml' file in the root."
Write-Host "To finish deploying the backend:"
Write-Host "  1. Go to https://dashboard.render.com/blueprints"
Write-Host "  2. Click 'New Blueprint Instance'"
Write-Host "  3. Connect this repository (https://github.com/Simarpreet-2607/Dodge-AI-assignment.git)"
Write-Host "  4. Render will automatically detect the 'render.yaml' file and deploy the FastAPI backend."
Write-Host "  5. Ensure you supply the 'DATABASE_URL' and 'GROQ_API_KEY' in the Render dashboard when prompted."
Write-Host "`nAfter Render finishes, update your Vercel frontend environment variable (NEXT_PUBLIC_API_URL) to point to the new Render URL!" -ForegroundColor Magenta

Write-Host "`nDeployment Guide completed." -ForegroundColor Cyan
