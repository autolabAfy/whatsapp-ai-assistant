# Deploy WhatsApp AI Assistant to Railway

## Quick Deploy (5 Minutes)

### Step 1: Install Railway CLI

```bash
brew install railway
```

### Step 2: Login to Railway

```bash
railway login
```

This opens your browser - sign up with GitHub (free).

### Step 3: Initialize Project

```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
railway init
```

Choose:
- "Create new project"
- Name it: "whatsapp-ai-assistant"

### Step 4: Add PostgreSQL Database

```bash
railway add
```

Choose: **PostgreSQL**

Railway will automatically:
- Create a PostgreSQL database
- Set `DATABASE_URL` environment variable
- Connect it to your app

### Step 5: Add Redis

```bash
railway add
```

Choose: **Redis**

### Step 6: Set Environment Variables

```bash
# Copy all environment variables from .env
railway variables set GEMINI_API_KEY=AIzaSyAn64reHgmJJkJFNSBZ7sbT6BrnQDxepNg
railway variables set GEMINI_MODEL=gemini-1.5-flash
railway variables set AI_PROVIDER=gemini
railway variables set GREEN_API_INSTANCE_ID=7105342242
railway variables set GREEN_API_TOKEN=a4709845232254bd195fdf4ea47f23d6c87fc7809fb89447ea1
railway variables set GREEN_API_BASE_URL=https://7105.api.green-api.com
railway variables set ENVIRONMENT=production
railway variables set AI_TEMPERATURE=0.7
railway variables set AI_MAX_TOKENS=1024
```

Or set them all at once in Railway dashboard (easier):
1. Go to https://railway.app/dashboard
2. Click your project
3. Click "Variables" tab
4. Paste from .env

### Step 7: Run Database Migrations

After deploy, run migrations:

```bash
# Connect to Railway PostgreSQL
railway run psql $DATABASE_URL < migrations/001_initial_schema.sql
```

Or manually:
1. Railway dashboard → PostgreSQL → "Data" tab
2. Click "psql" button
3. Paste contents of `migrations/001_initial_schema.sql`
4. Execute

### Step 8: Deploy!

```bash
railway up
```

This will:
- Upload your code
- Install dependencies
- Start the server
- Give you a public URL

### Step 9: Get Your Public URL

```bash
railway domain
```

Or create custom domain:
```bash
railway domain --new
```

You'll get something like:
```
https://whatsapp-ai-assistant-production.up.railway.app
```

---

## Alternative: Deploy via GitHub

### Step 1: Push to GitHub

```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant

# Initialize git if not already
git init
git add .
git commit -m "Initial commit - WhatsApp AI Assistant"

# Create GitHub repo, then:
git remote add origin https://github.com/YOUR_USERNAME/whatsapp-ai-assistant.git
git push -u origin main
```

### Step 2: Connect to Railway

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repo
5. Railway auto-detects Python and deploys

### Step 3: Add Services

In Railway dashboard:
- Click "New" → "Database" → "Add PostgreSQL"
- Click "New" → "Database" → "Add Redis"

### Step 4: Set Environment Variables

Dashboard → Variables → Add all from `.env`

### Step 5: Run Migrations

Railway dashboard → PostgreSQL → "Data" → Copy migration SQL

---

## Verify Deployment

### Test Health Endpoint

```bash
curl https://your-app.up.railway.app/health
```

Should return:
```json
{"status":"ok","database":"ok","environment":"production"}
```

### Test API Docs

Open in browser:
```
https://your-app.up.railway.app/docs
```

### Test Mobile Endpoint

```bash
curl https://your-app.up.railway.app/api/mobile/conversations
```

---

## Update Mobile App

Once deployed, update your mobile app's API URL:

**From:**
```javascript
const API_URL = "https://entitled-aggregate-advisors-commodities.trycloudflare.com";
```

**To:**
```javascript
const API_URL = "https://your-app.up.railway.app";
```

This URL is **permanent** (unlike Cloudflare tunnel which changes).

---

## Railway Free Tier

**What you get free:**
- $5 credit per month (resets monthly)
- ~500 hours of uptime
- PostgreSQL database (500MB)
- Redis database
- Custom domain

**Good for:**
- MVP testing
- Up to ~1000 messages/day
- Small user base

**Cost if you exceed:**
- ~$5-10/month for moderate usage

---

## Troubleshooting

### Build Fails

Check logs:
```bash
railway logs
```

Common issues:
- Missing dependencies in `requirements.txt`
- Wrong Python version (set to 3.9+)

### Database Connection Error

Check `DATABASE_URL`:
```bash
railway variables
```

Ensure it's set automatically by PostgreSQL addon.

### App Won't Start

Check Procfile:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Or check Railway dashboard → Deployments → Logs

---

## Monitoring

**View Logs:**
```bash
railway logs
```

**View Metrics:**
Railway dashboard → your project → "Metrics" tab

**Database Access:**
Railway dashboard → PostgreSQL → "Data" tab

---

## Rollback if Needed

```bash
# List deployments
railway status

# Rollback to previous
railway rollback
```

---

## Next Steps After Deploy

1. ✅ Get your Railway URL
2. ✅ Update mobile app with new URL
3. ✅ Test all endpoints
4. ✅ Run migrations
5. ✅ Add sample properties
6. ✅ Test full flow

---

**Railway is perfect for your MVP - deploys in minutes, handles database automatically!** 🚀
