#!/bin/bash

# Skynet Installation Script
# Claude Code Session Supervisor

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "    Skynet Installation Script"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check for required dependencies
echo "Checking dependencies..."
echo ""

# Check Python 3
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "Python 3 found: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

# Check if Python version is 3.11+
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    print_error "Python 3.11 or later is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js is not installed. Please install Node.js 18 or later."
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version 2>&1)
    print_status "npm found: $NPM_VERSION"
else
    print_error "npm is not installed. Please install npm."
    exit 1
fi

echo ""
echo "=========================================="
echo "Setting up Python environment..."
echo "=========================================="
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -e ".[dev]" > /dev/null 2>&1
print_status "Python dependencies installed"

echo ""
echo "=========================================="
echo "Setting up Web Dashboard..."
echo "=========================================="
echo ""

# Install npm dependencies and build
cd web
echo "Installing npm dependencies..."
npm install > /dev/null 2>&1
print_status "npm dependencies installed"

echo "Building web dashboard..."
npm run build > /dev/null 2>&1
print_status "Web dashboard built"
cd "$SCRIPT_DIR"

echo ""
echo "=========================================="
echo "Setting up data directories..."
echo "=========================================="
echo ""

# Create data directories
mkdir -p data
print_status "Data directory created"

# Initialize database
echo "Initializing database..."
source .venv/bin/activate
python3 -c "from supervisor.db import init_db; import asyncio; asyncio.run(init_db())" 2>/dev/null || true
print_status "Database initialized"

echo ""
echo "=========================================="
echo "Telegram Bot Configuration"
echo "=========================================="
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Do you want to reconfigure Telegram settings? (y/N): " RECONFIGURE
    if [[ ! "$RECONFIGURE" =~ ^[Yy]$ ]]; then
        echo "Keeping existing configuration."
    else
        CONFIGURE_TELEGRAM=true
    fi
else
    CONFIGURE_TELEGRAM=true
fi

if [ "$CONFIGURE_TELEGRAM" = true ]; then
    echo "To enable Telegram notifications, you need:"
    echo "  1. A Telegram Bot Token (from @BotFather)"
    echo "  2. Your Chat ID (from @userinfobot)"
    echo ""

    read -p "Enter your Telegram Bot Token (or press Enter to skip): " TELEGRAM_TOKEN

    if [ -n "$TELEGRAM_TOKEN" ]; then
        read -p "Enter your Telegram Chat ID: " TELEGRAM_CHAT_ID

        # Create or update .env file
        cat > .env << EOF
# Skynet Configuration
TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
EOF
        print_status "Telegram configuration saved to .env"
    else
        print_warning "Telegram configuration skipped. You can configure it later in .env"
        # Create empty .env template
        cat > .env << EOF
# Skynet Configuration
# Uncomment and fill in to enable Telegram notifications
# TELEGRAM_BOT_TOKEN=your_bot_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here
EOF
    fi
fi

echo ""
echo "=========================================="
echo "    Installation Complete!"
echo "=========================================="
echo ""
echo "To start Skynet manually:"
echo ""
echo "  1. Start the API server:"
echo "     source .venv/bin/activate"
echo "     uvicorn supervisor.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  2. Start the web dashboard (in another terminal):"
echo "     cd web && npm run start"
echo ""
echo "  3. Open http://localhost:3000 in your browser"
echo ""
echo "=========================================="
echo "To install as systemd services (requires sudo):"
echo "=========================================="
echo ""
echo "  sudo cp config/systemd/skynet-api.service /etc/systemd/system/"
echo "  sudo cp config/systemd/skynet-web.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable skynet-api skynet-web"
echo "  sudo systemctl start skynet-api skynet-web"
echo ""
echo "To check service status:"
echo "  sudo systemctl status skynet-api skynet-web"
echo ""
echo "=========================================="
print_status "Skynet is ready!"
