# WhatsApp AI Assistant for Real Estate Agents

A production-ready micro-SaaS platform that enables real estate agents to manage AI-powered WhatsApp chatbots with instant human override control.

## Core Features

- **AI ↔ Human Toggle**: Instant per-conversation control switching
- **Agent-Owned Knowledge Base**: Manage property listings with structured data
- **AI Persona Customization**: Configure chatbot tone, style, and personality
- **WhatsApp Integration**: Via Green API (unofficial WhatsApp Web API)
- **Self-Healing Architecture**: Automatic error recovery and system improvement
- **Mobile-First Design**: Optimized for agents on the go

## Architecture

The system follows a **3-Layer Architecture**:

1. **Directive Layer** (SOPs) - What to do
   - Markdown files in `directives/`
   - Define goals, rules, and workflows

2. **Orchestration Layer** (Decision Making) - When to do it
   - AI agent routing logic
   - Error handling and escalation

3. **Execution Layer** (Deterministic Work) - How to do it
   - Python scripts in `execution/`
   - API calls, database operations, message handling

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Green API account ([green-api.com](https://green-api.com))
- Anthropic API key (Claude)

### Installation

1. **Clone and setup**
```bash
cd whatsapp-ai-assistant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Setup database**
```bash
# Create database
createdb whatsapp_ai_assistant

# Run migrations
psql whatsapp_ai_assistant < migrations/001_initial_schema.sql
```

4. **Start Redis**
```bash
redis-server
```

5. **Run the server**
```bash
python main.py
```

Server will start on `http://localhost:8000`

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/whatsapp_ai_assistant

# Redis
REDIS_URL=redis://localhost:6379/0

# Green API
GREEN_API_INSTANCE_ID=your_instance_id
GREEN_API_TOKEN=your_token

# Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key

# JWT Secret
JWT_SECRET_KEY=generate_a_random_secret_key
```

### Green API Setup

1. Sign up at [green-api.com](https://green-api.com)
2. Create an instance
3. Scan QR code with WhatsApp
4. Copy instance ID and token to `.env`
5. Configure webhook URL in Green API dashboard:
   ```
   https://your-domain.com/webhook/greenapi
   ```

## Project Structure

```
whatsapp-ai-assistant/
├── directives/              # SOPs and workflow definitions
│   ├── core/               # Core routing and control logic
│   ├── ai_behavior/        # AI response rules
│   └── edge_cases/         # Error handling and race conditions
├── execution/              # Deterministic Python scripts
│   ├── config.py          # Configuration management
│   ├── database.py        # Database utilities
│   ├── redis_client.py    # Redis lock and cache
│   ├── webhook_handler.py # Incoming message router
│   ├── generate_ai_response.py  # AI response generation
│   ├── send_whatsapp_message.py # Message sender
│   ├── property_lookup.py # Property search
│   └── manage_properties.py     # Property CRUD
├── migrations/            # Database migrations
├── templates/             # HTML templates
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## API Endpoints

### Webhooks

- `POST /webhook/greenapi` - Green API webhook (incoming messages)

### Conversations

- `GET /api/conversations/{id}` - Get conversation details
- `GET /api/conversations/{id}/messages` - Get conversation messages
- `POST /api/conversations/toggle-mode` - Toggle AI/HUMAN mode
- `GET /api/agents/{agent_id}/conversations` - List agent's conversations

### Properties

- `POST /api/properties/search` - Search properties
- `GET /api/properties/{id}` - Get property details
- `GET /api/agents/{agent_id}/properties` - List agent's properties

## Usage Examples

### Adding Properties

```bash
python execution/manage_properties.py <agent_id>
```

Or via Python:
```python
from execution.manage_properties import add_property

property_data = {
    "title": "Marina Bay Condo",
    "property_type": "condo",
    "location": "Marina Bay",
    "price": 1200000,
    "bedrooms": 3,
    "bathrooms": 2,
    "key_selling_points": "Sea view, pool, gym"
}

add_property(agent_id, property_data)
```

### Toggling Conversation Mode

```bash
# Switch to HUMAN mode
python execution/set_mode_human.py <conversation_id>

# Switch to AI mode
python execution/set_mode_ai.py <conversation_id>
```

### Searching Properties

```bash
python execution/property_lookup.py <agent_id> "Orchard"
```

## How It Works

### Incoming Message Flow

1. WhatsApp user sends message
2. Green API forwards to `/webhook/greenapi`
3. System identifies/creates conversation
4. Checks conversation mode:
   - **AI Mode**: Generate AI response → Send via WhatsApp
   - **Human Mode**: Store message → Update inbox (no AI response)

### AI Response Generation

1. Load agent's persona configuration
2. Detect property intent in user message
3. Query agent's property database
4. Build system prompt with persona + property context
5. Generate response via Claude
6. Send via Green API

### Mode Toggle

1. Agent clicks toggle in UI
2. API updates `conversation.current_mode`
3. If switching to HUMAN: Cancel pending AI follow-ups
4. All future messages route accordingly

## Safety Features

### Race Condition Prevention

- Conversation-level locks (Redis)
- Atomic mode checks before sending
- Webhook deduplication (5-min TTL)
- Idempotent message sending

### Escalation Triggers

AI automatically switches to HUMAN mode when:
- User requests negotiation
- User raises objections/concerns
- User asks for legal/contract details
- User explicitly requests human agent
- AI fails to find matching properties 3x

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

To add new migrations:
```bash
# Create new migration file
touch migrations/002_your_migration.sql

# Apply migration
psql whatsapp_ai_assistant < migrations/002_your_migration.sql
```

### Logging

Logs are written to:
- Console (stderr)
- `logs/app.log` (rotating, 500MB max)

Log level controlled by `LOG_LEVEL` in `.env`

## Deployment

### Production Checklist

1. **Environment**
   - [ ] Set `ENVIRONMENT=production` in `.env`
   - [ ] Generate secure `JWT_SECRET_KEY`
   - [ ] Configure production database URL
   - [ ] Setup Redis with persistence

2. **Database**
   - [ ] Run migrations
   - [ ] Setup backups
   - [ ] Configure connection pooling

3. **Security**
   - [ ] Enable HTTPS (required for Green API webhooks)
   - [ ] Configure CORS properly
   - [ ] Add authentication middleware
   - [ ] Rate limiting

4. **Monitoring**
   - [ ] Setup error tracking (Sentry)
   - [ ] Configure uptime monitoring
   - [ ] Database performance monitoring

5. **Green API**
   - [ ] Update webhook URL to production domain
   - [ ] Verify WhatsApp connection

### Deployment Options

**Option 1: VPS (DigitalOcean, AWS EC2)**
```bash
# Install dependencies
sudo apt update
sudo apt install postgresql redis-server python3-pip nginx

# Setup systemd service
sudo systemctl enable whatsapp-ai-assistant
sudo systemctl start whatsapp-ai-assistant

# Configure nginx as reverse proxy
```

**Option 2: Docker**
```dockerfile
# Dockerfile (create this)
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**Option 3: Cloud Platform**
- Railway
- Render
- Fly.io
- Heroku

## Troubleshooting

### Messages not being received

1. Check Green API webhook configuration
2. Verify webhook URL is publicly accessible (HTTPS)
3. Check `webhook_logs` table for errors
4. Ensure WhatsApp is still connected in Green API dashboard

### AI not responding

1. Check conversation mode: `SELECT current_mode FROM conversations WHERE conversation_id = '...'`
2. Verify Anthropic API key in `.env`
3. Check logs for AI generation errors
4. Ensure properties exist for the agent

### Database connection errors

1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check `DATABASE_URL` in `.env`
3. Ensure database exists: `psql -l`
4. Check database logs

## License

Proprietary - All rights reserved

## Support

For issues and feature requests, contact support.
