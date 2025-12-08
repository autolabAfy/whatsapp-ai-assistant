#!/bin/bash

# Complete Deployment Script for WhatsApp AI Assistant
# Run this to deploy everything to Railway

echo "🚀 WhatsApp AI Assistant - Railway Deployment"
echo "=============================================="
echo ""

# Set brew path
eval "$(/opt/homebrew/bin/brew shellenv)"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Login to Railway
echo -e "${BLUE}Step 1: Login to Railway${NC}"
echo "This will open your browser..."
railway login

if [ $? -ne 0 ]; then
    echo -e "${RED}Login failed. Please try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Logged in successfully${NC}"
echo ""

# Step 2: Initialize project
echo -e "${BLUE}Step 2: Initialize Railway Project${NC}"
railway init --name whatsapp-ai-assistant

echo -e "${GREEN}✓ Project created${NC}"
echo ""

# Step 3: Add PostgreSQL
echo -e "${BLUE}Step 3: Adding PostgreSQL Database${NC}"
railway add --plugin postgresql

echo -e "${GREEN}✓ PostgreSQL added${NC}"
echo ""

# Step 4: Add Redis
echo -e "${BLUE}Step 4: Adding Redis${NC}"
railway add --plugin redis

echo -e "${GREEN}✓ Redis added${NC}"
echo ""

# Step 5: Set environment variables
echo -e "${BLUE}Step 5: Setting Environment Variables${NC}"
echo "Opening Railway dashboard for you to set variables..."
echo ""
echo "Please copy and paste these variables in the dashboard:"
echo "---------------------------------------------------"
cat << 'EOF'
GEMINI_API_KEY=AIzaSyAn64reHgmJJkJFNSBZ7sbT6BrnQDxepNg
GEMINI_MODEL=gemini-1.5-flash
AI_PROVIDER=gemini
GREEN_API_INSTANCE_ID=7105342242
GREEN_API_TOKEN=a4709845232254bd195fdf4ea47f23d6c87fc7809fb89447ea1
GREEN_API_BASE_URL=https://7105.api.green-api.com
ENVIRONMENT=production
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1024
JWT_SECRET_KEY=super-secret-jwt-key-change-this-in-production-12345
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
FCM_SERVER_KEY=your-firebase-server-key-here
MAX_UPLOAD_SIZE=10485760
EOF
echo "---------------------------------------------------"
echo ""
echo "Press Enter when done setting variables..."

railway open
read -p ""

echo -e "${GREEN}✓ Environment variables set${NC}"
echo ""

# Step 6: Deploy
echo -e "${BLUE}Step 6: Deploying to Railway${NC}"
railway up

echo -e "${GREEN}✓ Deployment initiated${NC}"
echo ""

# Step 7: Wait for deployment
echo -e "${BLUE}Step 7: Waiting for deployment to complete...${NC}"
sleep 10

# Step 8: Run migrations
echo -e "${BLUE}Step 8: Running Database Migrations${NC}"

echo "Running initial schema migration..."
railway run bash -c 'psql $DATABASE_URL < migrations/001_initial_schema.sql'

echo "Running features migration..."
railway run bash -c 'psql $DATABASE_URL < migrations/002_add_auth_and_features.sql'

echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Step 9: Generate domain
echo -e "${BLUE}Step 9: Generating Public Domain${NC}"
railway domain

echo -e "${GREEN}✓ Domain generated${NC}"
echo ""

# Step 10: Get deployment info
echo -e "${BLUE}Step 10: Getting Deployment URL${NC}"
RAILWAY_URL=$(railway domain)

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
echo "=============================================="
echo ""
echo "Your API is now live at:"
echo -e "${BLUE}${RAILWAY_URL}${NC}"
echo ""
echo "Next steps:"
echo "1. Test your API: ${RAILWAY_URL}/docs"
echo "2. Update mobile app with this URL"
echo "3. Test login with: demo@example.com / demo123"
echo ""
echo "View logs: railway logs"
echo "Check status: railway status"
echo "=============================================="
