# Railway Deployment Guide - Phase 1.5

## 🚀 Quick Deployment Steps

### Prerequisites
- ✅ Railway CLI installed (via Homebrew)
- ⚠️ Need to login interactively

---

## Step-by-Step Commands

### 1. Login to Railway (Interactive - Run in Terminal)

```bash
cd back
railway login
```

**Expected:** Opens browser for authentication, or prompts for email/password

---

### 2. Create New Railway Project

```bash
# From back/ directory
railway init
```

**When prompted:**
- **Name:** `adx-dev-backend`
- **Select:** `New Project` ✅

---

### 3. Link Project (if needed)

```bash
railway link
```

**Select:** `adx-dev-backend` ✅

---

### 4. Configure Environment Variables

**Option A: Via Railway Dashboard (Recommended)**
1. Go to: https://railway.app/dashboard
2. Select project: `adx-dev-backend`
3. Go to Variables tab
4. Add required variables:
   - `DATABASE_URL` (if using external DB)
   - `ENVIRONMENT=production`
   - Any other required env vars from `.env`

**Option B: Via CLI**
```bash
railway variables set DATABASE_URL="your-db-url"
railway variables set ENVIRONMENT=production
```

---

### 5. Deploy Backend

```bash
railway up
```

**Expected Output:**
```
✓ Building...
✓ Deploying...
✓ Deployed to: https://adx-dev-backend-production.up.railway.app
```

**Save the URL!** This is your new backend URL.

---

### 6. Verify Deployment

```bash
curl -X POST https://YOUR-NEW-URL/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"creator_id":"1","reviewer_id":"2","rating":5}' \
  -v
```

**Expected:** `HTTP/1.1 201 Created` or `401 Unauthorized` (NOT 404)

---

### 7. Update Frontend Configuration

**File:** `front/lib/core/constants/api_constants.dart`

**Update:**
```dart
/// Production API base URL
static const String prodApiBaseUrl = 'https://YOUR-NEW-RAILWAY-URL';
```

**Also update:**
```dart
/// Development API base URL (if using same backend)
static const String devApiBaseUrl = 'https://YOUR-NEW-RAILWAY-URL';
```

---

### 8. Test Flutter App

```bash
cd front
flutter clean
flutter pub get
flutter run -d chrome
```

**Check Console:**
- Look for API calls to `/v1/reviews/*`
- Should return 200/201 (not 404)

---

## ✅ Success Criteria

- [ ] Railway project created: `adx-dev-backend`
- [ ] Backend deployed successfully
- [ ] `POST /v1/reviews` returns 201/401 (NOT 404)
- [ ] Frontend config updated with new URL
- [ ] Flutter app connects successfully
- [ ] ReviewService works end-to-end

---

## 🔧 Troubleshooting

### Railway Login Issues
```bash
# Check if already logged in
railway whoami

# If not, login
railway login
```

### Deployment Fails
```bash
# Check Railway logs
railway logs

# Check project status
railway status
```

### Backend Returns 404
1. Verify router registration in `main.py`
2. Check Railway deployment logs
3. Verify environment variables are set
4. Test locally first: `uvicorn main:app --reload`

---

## 📝 Quick Reference

**Current Backend URL (Old):**
- `https://adx-web-backend.up.railway.app` (outdated deployment)

**New Backend URL (After Deployment):**
- `https://adx-dev-backend-production.up.railway.app` (or similar)

**Frontend Config File:**
- `front/lib/core/constants/api_constants.dart`

**Backend Entry Point:**
- `back/main.py`

---

## 🎯 Next Steps After Deployment

1. ✅ Verify `/v1/reviews` endpoint works
2. ✅ Update frontend config
3. ✅ Test Flutter app
4. ✅ Proceed to Phase 2 (CSRF Mock Mode + DB env fix)

---

## 📞 Support

If deployment fails:
1. Check Railway dashboard for errors
2. Review `railway logs` output
3. Verify all environment variables are set
4. Test backend locally first

