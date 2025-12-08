# Setup Instructions

Detailed step-by-step guide to get WhatsApp AI Assistant running.

## System Requirements

- **OS**: macOS, Linux, or Windows (WSL recommended)
- **Python**: 3.9 or higher
- **PostgreSQL**: 13 or higher
- **Redis**: 6 or higher
- **RAM**: Minimum 2GB
- **Storage**: 1GB+ for application and database

## Step 1: Install Prerequisites

### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# Install Redis
brew install redis
brew services start redis

# Install Python 3.9+
brew install python@3.9
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install Redis
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip
```

### Windows (WSL)

```bash
# Follow Ubuntu instructions above in WSL terminal
```

## Step 2: Database Setup

### Create PostgreSQL Database

```bash
# Switch to postgres user (Linux)
sudo -u postgres psql

# Or connect directly (macOS)
psql postgres
```

In PostgreSQL shell:
```sql
-- Create database
CREATE DATABASE whatsapp_ai_assistant;

-- Create user (optional, for production)
CREATE USER whatsapp_user WITH PASSWORD 'secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE whatsapp_ai_assistant TO whatsapp_user;

-- Exit
\q
```

### Run Migrations

```bash
# Navigate to project directory
cd /path/to/whatsapp-ai-assistant

# Run initial schema migration
psql whatsapp_ai_assistant < migrations/001_initial_schema.sql

# Verify tables created
psql whatsapp_ai_assistant -c "\dt"
```

You should see tables:
- agents
- conversations
- messages
- properties
- followups
- appointments
- webhook_logs
- escalations
- sent_messages_log

## Step 3: Python Environment Setup

### Create Virtual Environment

```bash
cd /path/to/whatsapp-ai-assistant

# Create virtual environment
python3.9 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows (WSL):
source venv/bin/activate
```

### Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

This will install:
- FastAPI (web framework)
- PostgreSQL drivers
- Redis client
- Anthropic SDK (Claude)
- And all dependencies

## Step 4: Green API Setup

### Create Green API Account

1. Go to [green-api.com](https://green-api.com)
2. Sign up for an account
3. Click "Create Instance"
4. Choose plan (free plan available for testing)

### Connect WhatsApp

1. In Green API dashboard, find your instance
2. Click "Scan QR Code"
3. Open WhatsApp on your phone
4. Go to Settings → Linked Devices → Link a Device
5. Scan the QR code from Green API dashboard
6. Wait for connection confirmation

### Get Credentials

From Green API dashboard, copy:
- **Instance ID** (e.g., `1234567890`)
- **API Token** (long string)

Keep these for Step 5.

### Configure Webhook (Later)

You'll need to configure webhook URL after deployment. For now, note:
- Webhook URL format: `https://your-domain.com/webhook/greenapi`
- You'll configure this after getting a public URL (Step 7)

## Step 5: Configuration

### Create Environment File

```bash
cd /path/to/whatsapp-ai-assistant

# Copy example
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

### Configure .env

```bash
# Database (update if you created custom user)
DATABASE_URL=postgresql://localhost:5432/whatsapp_ai_assistant
# Or with custom user:
# DATABASE_URL=postgresql://whatsapp_user:secure_password_here@localhost:5432/whatsapp_ai_assistant

# Redis (default)
REDIS_URL=redis://localhost:6379/0

# Green API (from Step 4)
GREEN_API_BASE_URL=https://api.green-api.com
GREEN_API_INSTANCE_ID=YOUR_INSTANCE_ID_HERE
GREEN_API_TOKEN=YOUR_TOKEN_HERE

# Anthropic API Key
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY_HERE

# JWT Secret (generate random string)
JWT_SECRET_KEY=YOUR_RANDOM_SECRET_HERE

# Environment
ENVIRONMENT=development

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
WEBHOOK_BASE_URL=http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

### Get Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up / log in
3. Go to API Keys
4. Create new key
5. Copy and paste into `.env`

### Generate JWT Secret

```bash
# Generate random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy output to JWT_SECRET_KEY in .env
```

## Step 6: Create Demo Agent

```bash
# Activate virtual environment
source venv/bin/activate

# Connect to database
psql whatsapp_ai_assistant
```

In PostgreSQL:
```sql
-- The demo agent was created by the migration, but let's update it with your Green API credentials

UPDATE agents
SET green_api_instance_id = 'YOUR_INSTANCE_ID',
    green_api_token = 'YOUR_TOKEN'
WHERE email = 'demo@example.com';

-- Get the agent_id for later use
SELECT agent_id, email, full_name FROM agents WHERE email = 'demo@example.com';

-- Copy the agent_id (UUID) - you'll need it
```

## Step 7: Run the Application

### Start the Server

```bash
# Make sure you're in project directory with venv activated
cd /path/to/whatsapp-ai-assistant
source venv/bin/activate

# Create logs directory
mkdir -p logs

# Run server
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     WhatsApp AI Assistant starting up...
INFO:     Database connected successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test the Server

Open another terminal:
```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"ok","database":"ok","environment":"development"}
```

## Step 8: Expose to Internet (for WhatsApp Webhooks)

Green API needs to send webhooks to your server. You need a public HTTPS URL.

### Option A: ngrok (Quick Testing)

```bash
# Install ngrok
brew install ngrok  # macOS
# Or download from ngrok.com

# Start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

### Option B: Production Deployment

See README.md deployment section for production setup.

### Configure Green API Webhook

1. Go to Green API dashboard
2. Select your instance
3. Click "Settings" or "Webhooks"
4. Set webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/greenapi`
   (or your production domain)
5. Enable "Incoming Messages" webhook
6. Save

## Step 9: Test End-to-End

### Add Test Property

```bash
# Get agent_id from Step 6
# Run property manager
python execution/manage_properties.py <agent_id>

# This creates a sample property
```

### Send Test Message

1. Send WhatsApp message to the number connected to Green API
2. Message: "Show me properties in Marina Bay"
3. Check logs:
   ```bash
   tail -f logs/app.log
   ```
4. You should see:
   - Webhook received
   - Message processed
   - AI response generated
   - Response sent

### View in Database

```sql
-- Check conversations
SELECT * FROM conversations;

-- Check messages
SELECT * FROM messages ORDER BY timestamp DESC LIMIT 10;

-- Check webhook logs
SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 5;
```

## Step 10: Access UI

Open browser:
```
http://localhost:8000/templates/inbox.html
```

Note: Update the `agentId` variable in the HTML file with your actual agent_id from Step 6.

## Common Issues

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### PostgreSQL connection refused
```bash
# Check if PostgreSQL is running
# macOS:
brew services list

# Linux:
sudo systemctl status postgresql

# Start if not running:
brew services start postgresql@14  # macOS
sudo systemctl start postgresql     # Linux
```

### Redis connection refused
```bash
# Check if Redis is running
redis-cli ping

# Should return: PONG

# If not, start Redis:
brew services start redis           # macOS
sudo systemctl start redis-server   # Linux
```

### Module not found errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Green API not sending webhooks
1. Verify webhook URL in Green API dashboard
2. Ensure URL is publicly accessible (use ngrok for testing)
3. Check Green API instance status (must be "connected")
4. Verify WhatsApp Web session is still active

## Next Steps

1. **Customize AI Persona**: Update agent persona in database
2. **Add Real Properties**: Use property management scripts
3. **Test Conversations**: Send various types of messages
4. **Monitor Logs**: Watch `logs/app.log` for issues
5. **Deploy to Production**: Follow README.md deployment guide

## Getting Help

If you encounter issues:
1. Check logs: `logs/app.log`
2. Check database: `SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 10;`
3. Verify all services are running (PostgreSQL, Redis, app server)
4. Check Green API dashboard for connection status
