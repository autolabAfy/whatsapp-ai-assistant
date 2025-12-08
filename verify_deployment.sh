#!/bin/bash

# Deployment Verification Script
# Run this after deploying to Railway to verify everything works

echo "🔍 Railway Deployment Verification"
echo "===================================="
echo ""

# Get Railway URL from user
read -p "Enter your Railway URL (e.g., https://your-app.up.railway.app): " RAILWAY_URL

# Remove trailing slash if present
RAILWAY_URL=${RAILWAY_URL%/}

echo ""
echo "Testing deployment at: $RAILWAY_URL"
echo ""

# Test 1: Health check
echo "1. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$RAILWAY_URL/health" 2>/dev/null)
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)

if [ "$HEALTH_CODE" = "200" ]; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed (HTTP $HEALTH_CODE)"
fi

# Test 2: API docs
echo "2. Testing API documentation..."
DOCS_RESPONSE=$(curl -s -w "\n%{http_code}" "$RAILWAY_URL/docs" 2>/dev/null)
DOCS_CODE=$(echo "$DOCS_RESPONSE" | tail -n 1)

if [ "$DOCS_CODE" = "200" ]; then
    echo "   ✅ API docs accessible at $RAILWAY_URL/docs"
else
    echo "   ❌ API docs failed (HTTP $DOCS_CODE)"
fi

# Test 3: Login endpoint
echo "3. Testing authentication..."
LOGIN_RESPONSE=$(curl -s -X POST "$RAILWAY_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}' 2>/dev/null)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "   ✅ Login working"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "   Token: ${ACCESS_TOKEN:0:50}..."
else
    echo "   ❌ Login failed"
    echo "   Response: $LOGIN_RESPONSE"
fi

# Test 4: Get current user
if [ ! -z "$ACCESS_TOKEN" ]; then
    echo "4. Testing authenticated endpoint..."
    ME_RESPONSE=$(curl -s "$RAILWAY_URL/api/auth/me" \
      -H "Authorization: Bearer $ACCESS_TOKEN" 2>/dev/null)

    if echo "$ME_RESPONSE" | grep -q "agent_id"; then
        echo "   ✅ Authentication working"
        echo "   User: $(echo "$ME_RESPONSE" | grep -o '"email":"[^"]*' | cut -d'"' -f4)"
    else
        echo "   ❌ Auth endpoint failed"
    fi
else
    echo "4. Skipping authenticated endpoint (no token)"
fi

# Test 5: Database check (conversations endpoint)
if [ ! -z "$ACCESS_TOKEN" ]; then
    echo "5. Testing database connection..."
    CONV_RESPONSE=$(curl -s "$RAILWAY_URL/api/mobile/conversations" \
      -H "Authorization: Bearer $ACCESS_TOKEN" 2>/dev/null)

    if echo "$CONV_RESPONSE" | grep -q "conversation_id" || echo "$CONV_RESPONSE" | grep -q "\[\]"; then
        echo "   ✅ Database connected"
    else
        echo "   ❌ Database connection failed"
        echo "   Response: $CONV_RESPONSE"
    fi
else
    echo "5. Skipping database check (no token)"
fi

echo ""
echo "===================================="
echo "Verification Complete!"
echo ""
echo "Next steps:"
echo "1. Update your mobile app's API_URL to: $RAILWAY_URL"
echo "2. Test login with demo@example.com / demo123"
echo "3. Setup Firebase for push notifications"
echo ""
echo "Integration guides:"
echo "- FRONTEND_INTEGRATION.md - Complete mobile app integration"
echo "- QUICK_INTEGRATION.md - Copy-paste code for React Native"
echo "- NEW_FEATURES_GUIDE.md - Images, Auth, Push Notifications"
