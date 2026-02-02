# Application Flow Mental Model
## My Projects + Accept/Reject System

**Document:** `APPLICATION_FLOW_MENTAL_MODEL.md`
**Last Updated:** 2026-02-02
**Status:** Production Ready

---

## Quick Reference

```
Creator applies → DB record created → Owner sees in My Projects → Accept/Reject → Creator notified
```

---

## 1. DATABASE LAYER

### Table: `campaign_participations`

```
┌─────────────────────────────────────────────────────────────────┐
│                    campaign_participations                       │
├─────────────────────────────────────────────────────────────────┤
│ id                  │ BigInteger  │ Primary Key                 │
│ user_id             │ String      │ FK → users.id (applicant)   │
│ campaign_id         │ BigInteger  │ FK → campaigns.id           │
│ reason_for_participation │ Text   │ Cover letter / why apply    │
│ social_media_handles│ JSON        │ Optional social links       │
│ media_kit           │ String(500) │ Optional portfolio URL      │
│ is_pending          │ Boolean     │ Default: True               │
│ is_approved         │ Boolean     │ Default: False              │
│ applied_at          │ DateTime    │ Auto: now()                 │
│ approved_at         │ DateTime    │ Set on approval             │
│ terms_accepted      │ Boolean     │ Default: False              │
│ review_message      │ Text        │ Message on APPROVE          │
│ rejection_reason    │ Text        │ Message on REJECT           │
│ completed_at        │ DateTime    │ Campaign completion         │
│ earnings            │ Numeric     │ Payment on completion       │
└─────────────────────────────────────────────────────────────────┘
```

### Status Logic (TWO BOOLEANS, NOT ENUM)

```
┌────────────────┬────────────┬─────────────┬─────────────────────┐
│ Status         │ is_pending │ is_approved │ Meaning             │
├────────────────┼────────────┼─────────────┼─────────────────────┤
│ PENDING        │ True       │ False       │ Awaiting review     │
│ APPROVED       │ False      │ True        │ Accepted by owner   │
│ REJECTED       │ False      │ False       │ Declined by owner   │
└────────────────┴────────────┴─────────────┴─────────────────────┘
```

**Why two booleans?**
- Legacy design decision
- `is_pending` = "not yet reviewed"
- `is_approved` = "review outcome was positive"
- Rejected = reviewed (not pending) + negative outcome (not approved)

---

## 2. APPLICATION SUBMISSION

### Endpoint
```
POST /campaigns/{campaign_id}/apply
```

### File Location
```
Backend: src/campaign/router.py (lines 198-265)
```

### Request
```json
{
  "cover_letter": "string (50-500 chars, required)",
  "media_kit": "string (optional URL)",
  "social_media_handles": {"instagram": "...", "tiktok": "..."},
  "terms_accepted": true
}
```

### What Happens
```
1. Validate user is authenticated
2. Check campaign exists and is active
3. Check user hasn't already applied
4. Check user isn't the campaign owner
5. Create CampaignParticipation record:
   - is_pending = True
   - is_approved = False
   - applied_at = now()
6. Return success with participation_id
```

### Rate Limit
```
5 applications per minute per user
```

---

## 3. MY PROJECTS - UNIFIED VIEW

### The Problem (Old System)
```
- Two separate tabs: "My Campaigns" vs "Applied Campaigns"
- Frontend tried to determine roles (unreliable)
- appliedCreators list often empty
- Confusing UX
```

### The Solution (New System)
```
- Single unified list
- Backend determines role per campaign
- Returns user_role: "owner" OR "applicant"
- Frontend just displays what backend says
```

### Endpoint
```
GET /my-projects/applications
```

### File Locations
```
Backend Router:  src/campaign/my_projects/router.py
Backend Service: src/campaign/my_projects/service.py
Backend Schemas: src/campaign/my_projects/schemas.py
```

### Response Structure
```json
{
  "user_id": "123",
  "total_campaigns": 5,
  "campaigns_as_owner": 2,
  "campaigns_as_applicant": 3,
  "campaigns": [
    {
      "id": "1",
      "title": "Summer Campaign",
      "user_role": "owner",
      "application_stats": {
        "total": 10,
        "pending": 4,
        "approved": 5,
        "rejected": 1
      }
    },
    {
      "id": "2",
      "title": "Brand Collab",
      "user_role": "applicant",
      "application_status": "approved",
      "review_message": "Welcome aboard!",
      "applied_at": "2026-01-15T10:00:00Z",
      "approved_at": "2026-01-16T14:30:00Z"
    }
  ]
}
```

### Role Determination Logic
```python
# In service.py

# Step 1: Get campaigns user CREATED
owned = db.query(Campaign).filter(Campaign.user_id == user_id).all()
# → user_role = "owner"

# Step 2: Get campaigns user APPLIED TO
applied = db.query(CampaignParticipation).filter(
    CampaignParticipation.user_id == user_id
).all()
# → user_role = "applicant" (skip if also owner)
```

---

## 4. CAMPAIGN CLICK - DETAIL VIEW

### Endpoint
```
GET /my-projects/applications/{campaign_id}
```

### Behavior Based on Role

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER CLICKS CAMPAIGN                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Determine Role  │
                    └─────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       ┌─────────────┐                 ┌─────────────┐
       │   OWNER     │                 │  APPLICANT  │
       └─────────────┘                 └─────────────┘
              │                               │
              ▼                               ▼
    ┌──────────────────┐           ┌──────────────────┐
    │ Return list of   │           │ Return own       │
    │ all applicants   │           │ application      │
    │ with statuses    │           │ details + status │
    └──────────────────┘           └──────────────────┘
```

### Owner Response
```json
{
  "campaign_id": "1",
  "campaign_title": "Summer Campaign",
  "user_role": "owner",
  "applicants": [
    {
      "user_id": "456",
      "username": "creator_jane",
      "email": "jane@example.com",
      "rating": 4.8,
      "participation_id": "789",
      "status": "pending",
      "applied_at": "2026-01-20T09:00:00Z",
      "reason_for_participation": "I love this brand..."
    }
  ]
}
```

### Applicant Response
```json
{
  "campaign_id": "2",
  "campaign_title": "Brand Collab",
  "user_role": "applicant",
  "application_details": {
    "participation_id": "101",
    "status": "approved",
    "applied_at": "2026-01-15T10:00:00Z",
    "approved_at": "2026-01-16T14:30:00Z",
    "reason_for_participation": "Excited to collaborate...",
    "review_message": "Welcome to the team!",
    "campaign_owner_username": "brand_owner"
  }
}
```

---

## 5. ACCEPT / REJECT APPLICATIONS

### Endpoint
```
POST /campaigns/{campaign_id}/applicants/manage
```

### File Location
```
Backend: src/campaign/campaign_applicants/router.py (lines 450-505)
```

### Request
```json
{
  "participation_id": "789",
  "action": "approve",  // or "reject"
  "message": "Welcome aboard! Looking forward to working with you."
}
```

### What Happens

```
┌─────────────────────────────────────────────────────────────────┐
│                        APPROVE ACTION                            │
├─────────────────────────────────────────────────────────────────┤
│ 1. Verify current_user is campaign owner                        │
│ 2. Find CampaignParticipation by participation_id               │
│ 3. Update fields:                                               │
│    - is_pending = False                                         │
│    - is_approved = True                                         │
│    - approved_at = now()                                        │
│    - review_message = message (from request)                    │
│ 4. Return updated participation                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        REJECT ACTION                             │
├─────────────────────────────────────────────────────────────────┤
│ 1. Verify current_user is campaign owner                        │
│ 2. Find CampaignParticipation by participation_id               │
│ 3. Update fields:                                               │
│    - is_pending = False                                         │
│    - is_approved = False                                        │
│    - rejection_reason = message (from request)                  │
│ 4. Return updated participation                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Message Storage
```
APPROVE → review_message field
REJECT  → rejection_reason field
```

---

## 6. COMPLETE FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE APPLICATION FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

    CREATOR                          DATABASE                         OWNER
    ───────                          ────────                         ─────
       │                                │                               │
       │  POST /campaigns/{id}/apply    │                               │
       │───────────────────────────────►│                               │
       │                                │                               │
       │                         ┌──────┴──────┐                        │
       │                         │   CREATE    │                        │
       │                         │ Participation│                        │
       │                         │ is_pending=T │                        │
       │                         │ is_approved=F│                        │
       │                         └──────┬──────┘                        │
       │                                │                               │
       │                                │  GET /my-projects/applications│
       │                                │◄──────────────────────────────│
       │                                │                               │
       │                                │  (returns campaigns with      │
       │                                │   user_role + stats)          │
       │                                │──────────────────────────────►│
       │                                │                               │
       │                                │  GET /my-projects/apps/{id}   │
       │                                │◄──────────────────────────────│
       │                                │                               │
       │                                │  (returns applicant list)     │
       │                                │──────────────────────────────►│
       │                                │                               │
       │                                │  POST /campaigns/{id}/        │
       │                                │       applicants/manage       │
       │                                │◄──────────────────────────────│
       │                                │  {action: "approve",          │
       │                                │   message: "Welcome!"}        │
       │                                │                               │
       │                         ┌──────┴──────┐                        │
       │                         │   UPDATE    │                        │
       │                         │ is_pending=F │                        │
       │                         │ is_approved=T│                        │
       │                         │ review_msg=  │                        │
       │                         │  "Welcome!"  │                        │
       │                         └──────┬──────┘                        │
       │                                │                               │
       │  GET /my-projects/applications │                               │
       │───────────────────────────────►│                               │
       │                                │                               │
       │  (shows status: "approved",    │                               │
       │   review_message: "Welcome!")  │                               │
       │◄───────────────────────────────│                               │
       │                                │                               │
```

---

## 7. FILE REFERENCE MAP

```
Backend Files:
├── core/models.py                              # CampaignParticipation model
├── src/campaign/
│   ├── router.py                               # POST /apply endpoint
│   ├── campaign_applicants/
│   │   └── router.py                           # POST /manage (accept/reject)
│   └── my_projects/
│       ├── __init__.py
│       ├── router.py                           # GET /applications endpoints
│       ├── service.py                          # Role determination logic
│       └── schemas.py                          # Pydantic response models
└── tests/
    ├── test_my_projects.py                     # Integration tests
    └── test_my_projects_service.py             # Unit tests (21 tests)

Frontend Files (Reference):
├── lib/models/campaign_models.dart             # MyProjectCampaign model
├── lib/services/campaign_service.dart          # API calls
├── lib/features/projects/my_projects_page.dart # Unified UI
└── lib/services/user_role_service.dart         # DEPRECATED (see file header)
```

---

## 8. API QUICK REFERENCE

| Action | Method | Endpoint | Who Calls |
|--------|--------|----------|-----------|
| Apply to campaign | POST | `/campaigns/{id}/apply` | Creator |
| Get my projects | GET | `/my-projects/applications` | Both |
| Get campaign details | GET | `/my-projects/applications/{id}` | Both |
| Accept/Reject | POST | `/campaigns/{id}/applicants/manage` | Owner |
| Get applicants list | GET | `/campaigns/{id}/applicants` | Owner |

---

## 9. STATUS TRANSITIONS

```
                    ┌─────────────┐
                    │   (none)    │
                    └──────┬──────┘
                           │
                     User applies
                           │
                           ▼
                    ┌─────────────┐
                    │   PENDING   │
                    │ is_pending=T│
                    │ is_approved=F│
                    └──────┬──────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
      Owner approves               Owner rejects
            │                             │
            ▼                             ▼
     ┌─────────────┐               ┌─────────────┐
     │  APPROVED   │               │  REJECTED   │
     │ is_pending=F│               │ is_pending=F│
     │ is_approved=T│               │ is_approved=F│
     │ review_msg=X │               │ reject_rsn=X │
     │ approved_at=Y│               └─────────────┘
     └─────────────┘
           │
           │ (Campaign completed)
           ▼
     ┌─────────────┐
     │  COMPLETED  │
     │ completed_at│
     │ earnings=Z  │
     └─────────────┘
```

---

## 10. COMMON QUERIES

### Get all pending applications for a campaign
```python
db.query(CampaignParticipation).filter(
    CampaignParticipation.campaign_id == campaign_id,
    CampaignParticipation.is_pending == True
).all()
```

### Get user's approved campaigns (as applicant)
```python
db.query(CampaignParticipation).filter(
    CampaignParticipation.user_id == user_id,
    CampaignParticipation.is_approved == True
).all()
```

### Count applications by status for a campaign
```python
participations = db.query(CampaignParticipation).filter(
    CampaignParticipation.campaign_id == campaign_id
).all()

stats = {
    "total": len(participations),
    "pending": len([p for p in participations if p.is_pending]),
    "approved": len([p for p in participations if p.is_approved]),
    "rejected": len([p for p in participations if not p.is_pending and not p.is_approved])
}
```

---

## 11. TESTING

### Run Unit Tests
```bash
cd /Users/dukeinstine/Desktop/Ad-x-Backend-master
pytest tests/test_my_projects_service.py -v
```

### Test Coverage
- Schema validation (7 tests)
- Status determination (3 tests)
- Role determination (3 tests)
- Stats calculation (2 tests)
- Edge cases (6 tests)

---

## 12. PRODUCTION NOTES

### Test Endpoints
```python
# Controlled by environment variable
ENABLE_TEST_ENDPOINTS = os.getenv("ENABLE_TEST_ENDPOINTS", "true").lower() == "true"

# Test endpoints (no auth required):
# GET /my-projects/test/applications/{user_id}
# GET /my-projects/test/applications/{user_id}/campaign/{campaign_id}

# In production: Set ENABLE_TEST_ENDPOINTS=false
```

### Security Considerations
- All /my-projects/* endpoints require authentication (except /test/*)
- Owner can only manage their own campaigns
- User can only see their own applications
- Rate limiting on /apply endpoint

---

*This mental model represents the current production implementation as of February 2026.*
