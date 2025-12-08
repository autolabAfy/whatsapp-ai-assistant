#!/bin/bash

# WhatsApp AI Assistant - Quick Start Script
# This script automates initial setup for development

set -e  # Exit on error

echo "========================================"
echo "WhatsApp AI Assistant - Quick Start"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in project directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from the whatsapp-ai-assistant directory${NC}"
    exit 1
fi

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check PostgreSQL
echo "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL not found. Please install PostgreSQL 13+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL found${NC}"

# Check Redis
echo "Checking Redis..."
if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}Redis not found. Please install Redis 6+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Redis found${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env if not exists
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please update .env with your credentials:${NC}"
    echo "  - GREEN_API_INSTANCE_ID"
    echo "  - GREEN_API_TOKEN"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - JWT_SECRET_KEY (generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
    echo ""
    read -p "Press Enter to continue after updating .env..."
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Database setup
echo ""
echo "Setting up database..."
read -p "Create database 'whatsapp_ai_assistant'? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if database exists
    if psql -lqt | cut -d \| -f 1 | grep -qw whatsapp_ai_assistant; then
        echo -e "${YELLOW}Database already exists${NC}"
    else
        createdb whatsapp_ai_assistant
        echo -e "${GREEN}✓ Database created${NC}"
    fi

    # Run migrations
    echo "Running migrations..."
    psql whatsapp_ai_assistant < migrations/001_initial_schema.sql > /dev/null 2>&1
    echo -e "${GREEN}✓ Migrations complete${NC}"
fi

# Create logs directory
echo ""
echo "Creating logs directory..."
mkdir -p logs
echo -e "${GREEN}✓ Logs directory created${NC}"

# Start Redis if not running
echo ""
echo "Checking Redis status..."
if ! redis-cli ping &> /dev/null; then
    echo -e "${YELLOW}Redis not running. Attempting to start...${NC}"
    if command -v brew &> /dev/null; then
        brew services start redis
    else
        sudo systemctl start redis-server
    fi
    sleep 2
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ Redis started${NC}"
    else
        echo -e "${RED}Failed to start Redis. Please start manually.${NC}"
    fi
else
    echo -e "${GREEN}✓ Redis is running${NC}"
fi

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Ensure .env is configured with your API keys"
echo "2. Start the server: python main.py"
echo "3. Expose webhook URL (ngrok http 8000)"
echo "4. Configure webhook in Green API dashboard"
echo "5. Send test message on WhatsApp"
echo ""
echo "For detailed instructions, see SETUP.md"
echo ""
echo "To start the server:"
echo -e "${GREEN}source venv/bin/activate && python main.py${NC}"
echo ""
