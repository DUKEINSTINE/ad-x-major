#!/bin/bash
# Monitor ReviewService API calls in real-time

echo "🔍 Monitoring ReviewService API calls..."
echo "Press Ctrl+C to stop"
echo ""
echo "Looking for:"
echo "  - [ReviewService] logs"
echo "  - /v1/reviews/* endpoints"
echo "  - 404 errors"
echo ""
echo "=========================================="
echo ""

tail -f /tmp/flutter_logs.txt 2>/dev/null | grep --line-buffered -i -E "ReviewService|v1/reviews|404|POST.*reviews|GET.*reviews|PUT.*reviews|DELETE.*reviews" || echo "Waiting for ReviewService API calls... (Interact with review features in the app)"

