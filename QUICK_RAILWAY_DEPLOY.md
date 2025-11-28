# 🚀 Quick Railway Deployment (5 Minutes)

## ✅ Prerequisites Check

- [x] Railway CLI installed: `brew install railway` ✅
- [ ] Railway login: **YOU NEED TO RUN THIS MANUALLY**

---

## 📋 Step-by-Step (Copy-Paste)

### Step 1: Login to Railway (Interactive)

```bash
cd back
railway login
```

**This will:**
- Open browser for authentication, OR
- Prompt for email/password

**Wait for:** `✓ Logged in as: your-email@example.com`

---

### Step 2: Create New Project

```bash
railway init
```

**When prompted:**
- **Name:** `adx-dev-backend`
- **Select:** `New Project` ✅

**Output:** `✓ Project created: adx-dev-backend`

---

### Step 3: Deploy

```bash
railway up
```

**Expected Output:**
```
✓ Building...
✓ Deploying...
✓ Deployed to: https://adx-dev-backend-production.up.railway.app
```

**📝 SAVE THIS URL!** This is your new backend URL.

---

### Step 4: Verify Deployment

```bash
curl -X POST https://YOUR-NEW-URL/v1/reviews \
  -H "Content-Type: application/json" \
  -d '{"creator_id":"1","reviewer_id":"2","rating":5}' \
  -v
```

**Expected:** 
- `HTTP/1.1 201 Created` ✅ OR
- `HTTP/1.1 401 Unauthorized` ✅ (auth required)
- **NOT:** `HTTP/1.1 404 Not Found` ❌

---

### Step 5: Update Frontend Config

**File:** `front/lib/core/constants/api_constants.dart`

**Find line 23:**
```dart
static const String prodApiBaseUrl = 'https://adx-web-backend.up.railway.app';
```

**Replace with:**
```dart
static const String prodApiBaseUrl = 'https://YOUR-NEW-RAILWAY-URL';
```

**Also update line 17 (dev URL if using same backend):**
```dart
static const String devApiBaseUrl = 'https://YOUR-NEW-RAILWAY-URL';
```

---

### Step 6: Test Flutter App

```bash
cd front
flutter clean
flutter pub get
flutter run -d chrome
```

**In Browser Console, check:**
- Network tab → Look for `/v1/reviews/*` calls
- Should return 200/201 (not 404)

---

## ✅ Success Checklist

- [ ] Railway project: `adx-dev-backend` created
- [ ] Backend deployed: `https://xxx.railway.app`
- [ ] `POST /v1/reviews` → 201/401 (NOT 404)
- [ ] Frontend config updated
- [ ] Flutter app connects successfully

---

## 📝 Reply Format

Once complete, reply with:

```
NEW RAILWAY URL: https://xxx.railway.app
CURL RESULT: [paste output]
STATUS: [READY/PHASE1 VERIFIED]
```

---

## 🔧 Troubleshooting

### "Cannot login in non-interactive mode"
**Solution:** Run `railway login` manually in your terminal (not via script)

### "Project not found"
**Solution:** Run `railway init` first, then `railway link`

### Deployment fails
**Solution:** Check `railway logs` for errors

### Still getting 404 on /v1/reviews
**Solution:** 
1. Verify `back/main.py` has `api_v1.include_router(reviews_router)`
2. Check Railway deployment logs
3. Test locally first: `uvicorn main:app --reload`

---

## 🎯 What This Fixes

- ✅ Backend serves at `/v1/reviews` (matches code)
- ✅ Frontend connects to YOUR backend (full control)
- ✅ No dependency on old backend team
- ✅ Phase 1 complete → Ready for Phase 2

---

**Ready? Start with Step 1: `railway login`**

