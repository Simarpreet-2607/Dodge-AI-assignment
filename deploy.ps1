<#
.SYNOPSIS
Complete Automated Deployment Script for Dodge AI.
This script will:
1. Commit any unsaved changes to Git.
2. Push your project up to your GitHub Repository.
3. Automatically launch Vercel to deploy the Next.js Frontend.
#>

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "🚀 Dodge AI - Auto Deployer" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Handle Git Commit & Push
Write-Host "`n[1/3] Syncing code to GitHub...`n" -ForegroundColor Yellow

# Check if there's anything to commit
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "Uncommitted changes found. Committing now..."
    git add .
    git commit -m "Automated deployment commit"
} else {
    Write-Host "No new changes to commit."
}

# Ensure we are pushing to the newly branched 'main'
git branch -M main
git push -u origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to push to GitHub. Please ensure you are logged in to Git." -ForegroundColor Red
    exit
}
Write-Host "✅ Successfully pushed code to GitHub repository!" -ForegroundColor Green

# 2. Render Check
Write-Host "`n[2/3] Backend Deployment Setup (Render)...`n" -ForegroundColor Yellow
Write-Host "Because your code is now synced to GitHub, Render can auto-deploy the Backend!"
Write-Host "1. Go to https://dashboard.render.com"
Write-Host "2. Click 'New Blueprint Instance' and connect your repository."
Write-Host "3. Render will use the 'render.yaml' file to instantly launch your FastAPI server."

# 3. Vercel Frontend
Write-Host "`n[3/3] Deploying Frontend to Vercel...`n" -ForegroundColor Yellow

if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ npm is not installed. Vercel requires Node.js." -ForegroundColor Red
    exit
}

if (-not (Get-Command "vercel" -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Vercel CLI Globally..."
    npm install -g vercel
}

Write-Host "Triggering Vercel deployment for the frontend..."
Set-Location -Path ".\frontend"
vercel --prod
Set-Location -Path ".."

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "🎉 Deployment Script Finished!" -ForegroundColor Green
Write-Host "Once Render finishes deploying your Backend, copy the Render URL and update your NEXT_PUBLIC_API_URL in your Vercel Dashboard settings!" -ForegroundColor Magenta
