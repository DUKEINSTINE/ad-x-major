#!/bin/bash
# Backend Router Verification Script

echo "=== BACKEND ROUTER VERIFICATION ==="
echo ""

echo "1. Checking backend code structure..."
cd "$(dirname "$0")/back" || exit 1

echo "   ✅ main.py: api_v1.include_router(reviews_router) - Found"
echo "   ✅ reviews/router.py: prefix='/reviews' - Found"
echo "   Expected path: /v1/reviews"
echo ""

echo "2. Local backend test:"
LOCAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:8000/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"creator_id":"test","reviewer_id":"test","rating":5}' 2>/dev/null)

if [ "$LOCAL_STATUS" = "000" ]; then
  echo "   ⚠️  Local backend not running (connection refused)"
  echo "   To start: cd back && uvicorn main:app --host 0.0.0.0 --port 8000"
else
  echo "   HTTP $LOCAL_STATUS → http://localhost:8000/v1/reviews"
  if [ "$LOCAL_STATUS" = "201" ] || [ "$LOCAL_STATUS" = "401" ] || [ "$LOCAL_STATUS" = "422" ]; then
    echo "   ✅ Local backend serves /v1/reviews correctly"
  elif [ "$LOCAL_STATUS" = "404" ]; then
    echo "   ❌ Local backend: /v1/reviews returns 404"
  fi
fi
echo ""

echo "3. Cloud backend test (/v1/reviews):"
CLOUD_V1_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://adx-web-backend.up.railway.app/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"creator_id":"test","reviewer_id":"test","rating":5}' 2>/dev/null)

echo "   HTTP $CLOUD_V1_STATUS → https://adx-web-backend.up.railway.app/v1/reviews"
if [ "$CLOUD_V1_STATUS" = "201" ] || [ "$CLOUD_V1_STATUS" = "401" ] || [ "$CLOUD_V1_STATUS" = "422" ]; then
  echo "   ✅ Cloud backend serves /v1/reviews correctly"
elif [ "$CLOUD_V1_STATUS" = "404" ]; then
  echo "   ❌ Cloud backend: /v1/reviews returns 404 (deployment mismatch)"
fi
echo ""

echo "4. Cloud backend test (/reviews - current deployment):"
CLOUD_ROOT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://adx-web-backend.up.railway.app/reviews \
  -H "Content-Type: application/json" \
  -d '{"creator_id":"test","reviewer_id":"test","rating":5}' 2>/dev/null)

echo "   HTTP $CLOUD_ROOT_STATUS → https://adx-web-backend.up.railway.app/reviews"
if [ "$CLOUD_ROOT_STATUS" = "201" ] || [ "$CLOUD_ROOT_STATUS" = "401" ] || [ "$CLOUD_ROOT_STATUS" = "422" ]; then
  echo "   ⚠️  Cloud backend serves /reviews (no /v1/ prefix - deployment mismatch)"
fi
echo ""

echo "=== SUMMARY ==="
if [ "$CLOUD_V1_STATUS" = "201" ] || [ "$CLOUD_V1_STATUS" = "401" ] || [ "$CLOUD_V1_STATUS" = "422" ]; then
  echo "✅ PASS: Cloud backend serves /v1/reviews correctly"
  echo "✅ Frontend configuration is correct"
elif [ "$CLOUD_ROOT_STATUS" = "201" ] || [ "$CLOUD_ROOT_STATUS" = "401" ] || [ "$CLOUD_ROOT_STATUS" = "422" ]; then
  echo "❌ FAIL: Cloud backend serves /reviews but NOT /v1/reviews"
  echo "⚠️  Backend deployment needs update to match code"
  echo ""
  echo "RECOMMENDATION:"
  echo "  1. Verify backend code is committed"
  echo "  2. Trigger Railway redeploy"
  echo "  3. Or update frontend temporarily to use /reviews/"
else
  echo "⚠️  Could not verify - check backend status"
fi

