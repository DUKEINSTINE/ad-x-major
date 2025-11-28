#!/bin/bash
# Quick deployment verification script
# Run this AFTER redeploying backend to verify /v1/reviews works

echo "=== Backend Deployment Verification ==="
echo ""
echo "Testing: https://adx-web-backend.up.railway.app/v1/reviews"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST 'https://adx-web-backend.up.railway.app/v1/reviews' \
  -H "Content-Type: application/json" \
  -d '{"creator_id":"1","reviewer_id":"2","rating":5}')

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

echo "Response Body:"
echo "$BODY" | head -3
echo ""
echo "HTTP Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "422" ]; then
  echo "✅ SUCCESS: Backend serves /v1/reviews correctly!"
  echo "✅ Frontend will work correctly"
  echo ""
  echo "Next: Test frontend review features"
elif [ "$HTTP_CODE" = "404" ]; then
  echo "❌ FAIL: Backend still returns 404"
  echo "⚠️  Deployment may not be complete or code not pushed"
  echo ""
  echo "Check:"
  echo "  1. Is code committed and pushed?"
  echo "  2. Is Railway deployment complete?"
  echo "  3. Check Railway logs for errors"
else
  echo "⚠️  Unexpected status: $HTTP_CODE"
  echo "Response: $BODY"
fi

