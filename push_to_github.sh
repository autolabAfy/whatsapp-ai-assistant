#!/bin/bash

# Push to GitHub Script
# Run this after creating the repository on GitHub

echo "🚀 Pushing whatsapp-ai-assistant to GitHub"
echo "=========================================="
echo ""

# Get GitHub username
read -p "Enter your GitHub username (e.g., autolabAfy): " GITHUB_USERNAME

# Add remote
echo "Adding GitHub remote..."
git remote add origin "https://github.com/$GITHUB_USERNAME/whatsapp-ai-assistant.git"

# Push to GitHub
echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo ""
echo "Your repository: https://github.com/$GITHUB_USERNAME/whatsapp-ai-assistant"
echo ""
echo "Next steps:"
echo "1. Go to Railway: https://railway.app/new"
echo "2. Click 'Deploy from GitHub repo'"
echo "3. Select 'whatsapp-ai-assistant'"
echo "4. Follow RAILWAY_DEPLOYMENT_GUIDE.md"
