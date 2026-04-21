#!/bin/bash
# server-setup.sh — Initial server configuration for Threadangle
# Run this once on a fresh Ubuntu 22.04 server.

echo "🚀 Starting Threadangle server setup..."

# 1. Update and install basic dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip git nginx curl -y

# 2. Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# 3. Install PM2
sudo npm install -g pm2

# 4. Create directory structure
sudo mkdir -p /var/www/threadangle
sudo chown ubuntu:ubuntu /var/www/threadangle

# 5. Clone repository (User will need to do this or provide access)
# git clone https://github.com/YOUR_USERNAME/threadangle.git /home/ubuntu/threadangle

# 6. Setup Backend environment
cd /home/ubuntu/threadangle/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Create .env template
if [ ! -f .env ]; then
  cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_key_here
STRIPE_SECRET_KEY=your_stripe_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
STRIPE_STARTER_PRICE_ID=price_...
STRIPE_PRO_PRICE_ID=price_...
JWT_SECRET=your_jwt_secret
DATABASE_URL=sqlite+aiosqlite:///./threadangle.db
ENVIRONMENT=production
FRONTEND_URL=https://kriangle.com
EOF
  echo "⚠️  Created .env template. Please update with real keys!"
fi

# 8. Start PM2 process
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name threadangle-api
pm2 save
pm2 startup

echo "✅ Server setup complete! Now configure Nginx and get SSL with Certbot."
