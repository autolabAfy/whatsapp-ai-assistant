#!/bin/bash

# WhatsApp AI Assistant - Dependency Installation Script
# Run this script to install PostgreSQL and Redis

set -e  # Exit on error

echo "=========================================="
echo "Installing PostgreSQL and Redis"
echo "=========================================="
echo ""
echo "This script will install:"
echo "  - Homebrew (if not installed)"
echo "  - PostgreSQL 14"
echo "  - Redis"
echo ""
echo "You will be asked for your password."
echo ""
read -p "Press Enter to continue..."

# Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    echo ""
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH (for ARM Mac)
    echo ""
    echo "Adding Homebrew to PATH..."
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "✓ Homebrew already installed"
fi

# Install PostgreSQL
echo ""
echo "Installing PostgreSQL 14..."
brew install postgresql@14

# Install Redis
echo ""
echo "Installing Redis..."
brew install redis

# Start services
echo ""
echo "Starting PostgreSQL..."
brew services start postgresql@14

echo ""
echo "Starting Redis..."
brew services start redis

# Wait a moment for services to start
echo ""
echo "Waiting for services to start..."
sleep 3

# Verify installations
echo ""
echo "=========================================="
echo "Verifying installations..."
echo "=========================================="

echo ""
echo "PostgreSQL version:"
psql postgres -c "SELECT version();" || echo "ERROR: PostgreSQL not responding"

echo ""
echo "Redis status:"
redis-cli ping || echo "ERROR: Redis not responding"

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create database: cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant && createdb whatsapp_ai_assistant"
echo "2. Run migrations: psql whatsapp_ai_assistant < migrations/001_initial_schema.sql"
echo "3. Start server: source venv/bin/activate && python main.py"
echo ""
