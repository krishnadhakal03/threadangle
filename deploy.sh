#!/bin/bash
# deploy.sh — Production deployment script for Threadangle
# This script deploys both backend and frontend to kriangle.com

set -e  # Exit on any error

SERVER="ubuntu@kriangle.com"  # Replace with your EC2 IP or domain

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          THREADANGLE PRODUCTION DEPLOYMENT                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check if we're on main branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo "⚠️  Warning: You're on branch '$BRANCH', not 'main'"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠️  You have uncommitted changes"
    read -p "Commit and push them now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        read -p "Enter commit message: " COMMIT_MSG
        git commit -m "${COMMIT_MSG:-Deploy: $(date +%Y-%m-%d %H:%M:%S)}"
    else
        echo "❌ Aborting deployment"
        exit 1
    fi
fi

# Push to Git
echo ""
echo "➡️  Pushing code to main..."
git push origin main

# Deploy to server
echo ""
echo "🌐 Connecting to production server..."
echo ""

ssh $SERVER << 'ENDSSH'
  set -e
  
  echo "📥 Pulling latest code..."
  cd /home/ubuntu/threadangle
  git pull origin main
  
  echo ""
  echo "🔧 Setting up backend..."
  cd backend
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Install/update dependencies
  pip install -r requirements.txt --quiet
  
  # Run database migrations
  echo "Running database migrations..."
  python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"
  
  # Restart backend service
  echo "Restarting backend service..."
  pm2 restart threadangle-api || pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name threadangle-api
  
  echo ""
  echo "🎨 Building frontend..."
  cd ../frontend
  
  # Install dependencies
  npm install --quiet
  
  # Build for production
  npm run build
  
  # Deploy static files
  echo "Deploying static files..."
  sudo cp -r dist/* /var/www/kriangle.com/html/
  
  # Restart nginx (if needed)
  sudo systemctl reload nginx
  
  echo ""
  echo "✅ Deployment complete!"
  echo "🌐 Application available at: https://kriangle.com"
  
ENDSSH

echo ""
echo "══════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "🌐 Live URL: https://kriangle.com"
echo "📊 Backend: https://kriangle.com/api/docs"
echo ""
echo "Next steps:"
echo "  1. Test the live site"
echo "  2. Verify payment flow works"
echo "  3. Check email notifications"
echo "  4. Monitor error logs"
echo ""
echo "Monitor logs with:"
echo "  ssh $SERVER 'pm2 logs threadangle-api'"
echo ""
