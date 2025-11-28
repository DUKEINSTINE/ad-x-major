# Phase 1: ReviewService Testing Checklist

## ✅ Implementation Complete

All review endpoints have been updated to use `/v1/reviews/*` prefix and `ApiEndpoints` constants.

### Changes Made:
1. ✅ Added review endpoints to `ApiEndpoints` class with `/v1/` prefix
2. ✅ Updated `ReviewService` to use `ApiConfig.baseUrl` instead of `AppConfig.apiUrl`
3. ✅ All 9 endpoints now use `ApiEndpoints` constants (no hardcoded strings)
4. ✅ Added Dio logging interceptor for debugging
5. ✅ Improved error handling with specific `DioException` checks

### Files Modified:
- `front/lib/core/config/api_endpoints.dart` - Added review endpoints
- `front/lib/services/review_service.dart` - Updated all methods

---

## 🧪 Testing Instructions

### 1. App Status
- ✅ App is running on Chrome (debug mode)
- ✅ Dio logging is enabled (check browser console)
- ✅ All endpoints use `/v1/reviews/*` prefix

### 2. Open Browser Console
Press `F12` or `Cmd+Option+I` (Mac) to open DevTools and check the Console tab.

### 3. Test All Endpoints

#### ✅ Test 1: Create Review
**Action:** Create a new review from campaign details or profile
- **Expected:** `POST /v1/reviews` → `201 Created`
- **Check Console:** Should see `[ReviewService] POST /v1/reviews` with no 404 errors
- **Verify:** Review appears in UI

#### ✅ Test 2: Update Review
**Action:** Edit an existing review
- **Expected:** `PUT /v1/reviews/{reviewId}` → `200 OK`
- **Check Console:** Should see `[ReviewService] PUT /v1/reviews/{reviewId}` with no 404 errors
- **Verify:** Review updates successfully

#### ✅ Test 3: Delete Review
**Action:** Delete a review
- **Expected:** `DELETE /v1/reviews/{reviewId}` → `200 OK`
- **Check Console:** Should see `[ReviewService] DELETE /v1/reviews/{reviewId}` with no 404 errors
- **Verify:** Review is removed from UI

#### ✅ Test 4: Get Reviews Given By User
**Action:** Navigate to profile → "Reviews Given" section
- **Expected:** `GET /v1/reviews/given-by/{userId}` → `200 OK` with `List<Review>`
- **Check Console:** Should see `[ReviewService] GET /v1/reviews/given-by/{userId}` with no 404 errors
- **Verify:** List of reviews displayed

#### ✅ Test 5: Get Reviews For Creator
**Action:** Navigate to creator profile → "Reviews" section
- **Expected:** `GET /v1/reviews/for-creator/{creatorId}` → `200 OK` with `List<Review>`
- **Check Console:** Should see `[ReviewService] GET /v1/reviews/for-creator/{creatorId}` with no 404 errors
- **Verify:** List of reviews displayed

#### ✅ Test 6: Get Review Stats
**Action:** Navigate to profile → View review statistics
- **Expected:** `GET /v1/reviews/stats/{userId}` → `200 OK` with `ReviewStats`
- **Check Console:** Should see `[ReviewService] GET /v1/reviews/stats/{userId}` with no 404 errors
- **Verify:** Stats displayed (average rating, total reviews, etc.)

#### ✅ Test 7: Get Review By ID
**Action:** Click on a specific review to view details
- **Expected:** `GET /v1/reviews/{reviewId}` → `200 OK` with `Review`
- **Check Console:** Should see `[ReviewService] GET /v1/reviews/{reviewId}` with no 404 errors
- **Verify:** Review details displayed

#### ✅ Test 8: Report Review
**Action:** Report an inappropriate review
- **Expected:** `POST /v1/reviews/{reviewId}/report` → `200 OK`
- **Check Console:** Should see `[ReviewService] POST /v1/reviews/{reviewId}/report` with no 404 errors
- **Verify:** Report submitted successfully

#### ✅ Test 9: Get Recent Reviews
**Action:** Navigate to homepage or discovery page
- **Expected:** `GET /v1/reviews/recent?limit=10` → `200 OK` with `List<Review>`
- **Check Console:** Should see `[ReviewService] GET /v1/reviews/recent` with no 404 errors
- **Verify:** Recent reviews displayed

#### ✅ Test 10: Get Existing Review
**Action:** Check if user has already reviewed a creator (before creating new review)
- **Expected:** `GET /v1/reviews/existing/{creatorId}/{reviewerId}` → `200 OK` with `Review` or `404` (null)
- **Check Console:** Should see `[ReviewService] GET /v1/reviews/existing/{creatorId}/{reviewerId}` 
- **Note:** 404 is expected if no review exists (this is handled gracefully)
- **Verify:** No error thrown, returns null if no review exists

---

## 🔍 What to Look For in Console

### ✅ Success Indicators:
```
[ReviewService] --> POST /v1/reviews
[ReviewService] <-- 201 Created
[ReviewService] Response: {...}
```

### ❌ Error Indicators (Should NOT see):
```
[ReviewService] --> POST /reviews  ❌ WRONG (missing /v1/)
[ReviewService] <-- 404 Not Found ❌ WRONG (endpoint not found)
```

### ✅ All Endpoints Should Show:
- Request method and full path with `/v1/reviews/*`
- Status code 200 or 201 (not 404)
- Response data (in debug mode)

---

## 📋 Test Both Roles

### Brand Role:
- [ ] Create review for a creator
- [ ] View reviews given
- [ ] Update/delete own reviews
- [ ] View creator profiles with reviews

### Creator Role:
- [ ] View reviews received
- [ ] View review statistics
- [ ] Report inappropriate reviews
- [ ] Check existing reviews before creating new one

---

## ✅ Verification Checklist

After testing, verify:

- [ ] **No 404 errors** in console for any `/v1/reviews/*` endpoint
- [ ] **All endpoints return 200/201** (not 404)
- [ ] **All requests show `/v1/reviews/*`** in console (not `/reviews/*`)
- [ ] **All review operations work** (create, update, delete, fetch)
- [ ] **Both Brand and Creator roles** can use review features
- [ ] **Error messages are user-friendly** (not raw exceptions)

---

## 🐛 If You See 404 Errors

1. **Check backend is running** and accessible at `ApiConfig.baseUrl`
2. **Verify backend has `/v1/reviews` routes** registered
3. **Check network tab** in DevTools for actual HTTP requests
4. **Verify authentication** - some endpoints require auth tokens
5. **Check CORS** - ensure backend allows requests from Chrome

---

## 📝 Test Results

After completing all tests, fill in:

- [ ] All 10 endpoints tested
- [ ] No 404 errors found
- [ ] All endpoints return correct status codes
- [ ] Both roles tested successfully
- [ ] Console logs show correct `/v1/reviews/*` paths

**Status:** ⬜ Pending | ✅ Pass | ❌ Fail

---

## 🎯 Next Steps

Once all tests pass:
1. Reply: **"Phase 1 VERIFIED - ReviewService fixed. All review endpoints return 200/201, no 404s."**
2. Proceed to **Phase 2: CSRF Mock Mode + DB env fix**

---

## 📸 Screenshots (Optional)

If possible, capture:
- Console logs showing successful `/v1/reviews/*` requests
- Network tab showing 200/201 responses
- UI showing reviews working correctly

