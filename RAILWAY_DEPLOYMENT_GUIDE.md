# Railway Deployment Guide - Complete Setup

## Quick Deploy (5 Minutes)

### Step 1: Create Railway Project

1. Go to https://railway.app/new
2. Click **"Deploy from GitHub repo"**
3. Select repository: `whatsapp-ai-assistant`
4. Click **"Deploy Now"**

### Step 2: Add Databases

In your Railway project dashboard:

1. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Click **"+ New"** → **"Database"** → **"Add Redis"**

Railway automatically sets these environment variables:
- `DATABASE_URL` (PostgreSQL connection string)
- `REDIS_URL` (Redis connection string)

### Step 3: Add Environment Variables

Click on your service → **"Variables"** tab → **"Raw Editor"** and paste:

```bash
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
PORT=8000
```

Click **"Save"** - Railway will automatically redeploy.

### Step 4: Generate Public Domain

1. Click on your service
2. Go to **"Settings"** tab
3. Scroll to **"Networking"**
4. Click **"Generate Domain"**
5. Copy the URL (e.g., `https://your-app.up.railway.app`)

### Step 5: Run Database Migrations

1. Click on your service
2. Go to **"Deployments"** tab
3. Click the **three dots (...)** on the latest deployment
4. Select **"View Logs"**
5. In the top right, click **"..."** → **"Open Shell"**

In the shell, run:

```bash
psql $DATABASE_URL < migrations/001_initial_schema.sql
psql $DATABASE_URL < migrations/002_add_auth_and_features.sql
```

### Step 6: Verify Deployment

Test your API at: `https://your-app.up.railway.app/docs`

You should see the FastAPI interactive documentation with all endpoints.

### Step 7: Test Login

Try logging in with demo account:

```bash
curl -X POST https://your-app.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}'
```

You should get back an access token.

---

## Your Deployment Checklist

- [ ] Railway project created from GitHub
- [ ] PostgreSQL added
- [ ] Redis added
- [ ] Environment variables set
- [ ] Public domain generated
- [ ] Migration 001 completed
- [ ] Migration 002 completed
- [ ] API docs accessible at /docs
- [ ] Demo login working

---

## What You'll Get

**Your API URL**: `https://your-app-name.up.railway.app`

**Demo Account**:
- Email: `demo@example.com`
- Password: `demo123`

**Available Endpoints**:
- `/docs` - API documentation
- `/api/auth/login` - Login
- `/api/auth/register` - Register new agent
- `/api/mobile/conversations` - Get all chats
- `/api/mobile/chat/send` - Send message
- `/api/mobile/properties/search` - Search properties
- `/api/mobile/appointments` - Manage calendar
- `/api/mobile/agent/settings` - Agent settings

---

## Next Steps After Deployment

1. **Update Mobile App**
   - Set `API_URL` to your Railway URL
   - Test login with demo account
   - Test chat functionality

2. **Setup Firebase** (for push notifications)
   - Create Firebase project
   - Get FCM server key
   - Update `FCM_SERVER_KEY` in Railway variables

3. **Production Setup**
   - Change `JWT_SECRET_KEY` to a secure random string
   - Update demo account password
   - Configure custom domain (optional)

---

## Troubleshooting

### Deployment Failed
- Check **"Deployments"** → **"Logs"** for errors
- Verify all dependencies in `requirements.txt`
- Ensure Python version is 3.9+

### Database Connection Error
- Verify PostgreSQL plugin is added
- Check `DATABASE_URL` is set in environment variables
- Make sure migrations ran successfully

### API Returns 500 Error
- Check deployment logs for Python errors
- Verify all environment variables are set
- Test locally first with `python main.py`

### Can't Access /docs
- Verify domain is generated and active
- Check if deployment is running (not crashed)
- Test basic endpoint: `curl https://your-app.up.railway.app/health`

---

## Manual CLI Deployment (Alternative)

If you prefer command line:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up

# Run migrations
railway run bash -c 'psql $DATABASE_URL < migrations/001_initial_schema.sql'
railway run bash -c 'psql $DATABASE_URL < migrations/002_add_auth_and_features.sql'

# Get domain
railway domain
```

---

## Your Backend is Production-Ready!

✅ Secure JWT authentication
✅ Property image uploads
✅ Push notifications ready
✅ AI-powered chat
✅ Full REST API for mobile app
✅ PostgreSQL + Redis
✅ Auto-scaling on Railway

**Now integrate with your RealtorAI Connect mobile app!**
