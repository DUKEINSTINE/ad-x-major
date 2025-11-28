#!/bin/bash
# Railway Deployment Script
# Run this AFTER logging in with: railway login

set -e

echo "=== Railway Backend Deployment ==="
echo ""

# Check if in back directory
if [ ! -f "main.py" ]; then
  echo "❌ Error: Must run from back/ directory"
  echo "Usage: cd back && ../deploy_to_railway.sh"
  exit 1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
  echo "❌ Railway CLI not found"
  echo "Install with: brew install railway"
  exit 1
fi

# Check if logged in
echo "1. Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
  echo "⚠️  Not logged in to Railway"
  echo "Please run: railway login"
  echo "Then run this script again"
  exit 1
fi

echo "✅ Logged in to Railway"
echo ""

# Initialize project (if not already)
echo "2. Checking Railway project..."
if [ ! -f ".railway" ]; then
  echo "⚠️  No Railway project found"
  echo "Run: railway init"
  echo "   Name: adx-dev-backend"
  echo "   Select: New Project"
  exit 1
fi

echo "✅ Railway project linked"
echo ""

# Deploy
echo "3. Deploying backend to Railway..."
echo "   This may take 2-5 minutes..."
echo ""

railway up

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "📋 Next Steps:"
echo "   1. Get your Railway URL from the output above"
echo "   2. Update front/lib/core/constants/api_constants.dart"
echo "   3. Test: curl -X POST YOUR-URL/v1/reviews ..."
echo "   4. Run Flutter app and verify /v1/reviews works"
echo ""

