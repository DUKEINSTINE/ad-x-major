# my_projects/router.py
"""
Unified My Projects API endpoints.

This module provides endpoints for the unified "My Projects" feature that combines
both owner (brand) and applicant (creator) views into a single interface.

Architecture:
- GET /applications - Returns all user's campaigns (owned + applied)
- GET /applications/{id} - Returns role-specific view on click

The backend determines the user's role for each campaign and returns appropriate data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from core.models import User
from .service import my_projects_service
from .schemas import MyProjectsResponse, CampaignClickResponse
import logging
import os

logger = logging.getLogger(__name__)

# Production safety: Disable test endpoints unless explicitly enabled
ENABLE_TEST_ENDPOINTS = os.getenv("ENABLE_TEST_ENDPOINTS", "true").lower() == "true"

router = APIRouter(prefix="/my-projects", tags=["My Projects"])


@router.get("/applications", response_model=MyProjectsResponse)
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MyProjectsResponse:
    """
    Get unified list of all campaigns where user is either owner OR applicant.

    This endpoint returns a single list containing:
    - Campaigns the user created (user_role = "owner")
    - Campaigns the user applied to (user_role = "applicant")

    Each campaign includes a `user_role` field that determines what view
    to show when the campaign is clicked:
    - "owner" → Show list of applicants with accept/reject actions
    - "applicant" → Show application status and feedback

    **Response includes:**
    - Campaign details (title, budget, category, etc.)
    - Role-specific data:
      - For owners: application_stats (total, pending, approved, rejected)
      - For applicants: application_status, review_message, rejection_reason
    """
    try:
        user_id = str(current_user.id)
        result = my_projects_service.get_user_projects(db, user_id)
        logger.info(f"Retrieved {result.total_campaigns} projects for user {user_id}")
        return result

    except ValueError as e:
        logger.error(f"User not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching my projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch projects")


@router.get("/applications/{campaign_id}", response_model=CampaignClickResponse)
def get_campaign_details_for_user(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CampaignClickResponse:
    """
    Get campaign details based on user's role.

    When user clicks a campaign, this endpoint returns the appropriate view:

    **If user is OWNER:**
    - Returns list of all applicants
    - Each applicant includes: user info, application status, cover letter
    - Owner can then use /manage endpoint to accept/reject

    **If user is APPLICANT:**
    - Returns their own application details
    - Includes: status (pending/approved/rejected), feedback message
    - Shows campaign owner info

    **Error cases:**
    - 404 if campaign doesn't exist
    - 403 if user has no relationship with the campaign
    """
    try:
        user_id = str(current_user.id)
        result = my_projects_service.get_campaign_click_data(db, user_id, campaign_id)
        logger.info(f"Retrieved campaign {campaign_id} details for user {user_id} (role: {result.user_role})")
        return result

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif "no relationship" in error_msg.lower():
            raise HTTPException(status_code=403, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Error fetching campaign details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch campaign details")


# Test endpoint without authentication (for development)
@router.get("/test/applications/{user_id}", response_model=MyProjectsResponse)
def test_get_my_applications(
    user_id: str,
    db: Session = Depends(get_db),
) -> MyProjectsResponse:
    """
    TEST ENDPOINT - Get unified list without authentication.
    For development/testing purposes only.

    **Warning:** This endpoint is disabled in production unless
    ENABLE_TEST_ENDPOINTS=true is set.
    """
    if not ENABLE_TEST_ENDPOINTS:
        logger.warning(f"Test endpoint called in production by user {user_id}")
        raise HTTPException(
            status_code=403,
            detail="Test endpoints are disabled in production"
        )

    try:
        logger.debug(f"Test endpoint: fetching projects for user {user_id}")
        result = my_projects_service.get_user_projects(db, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch projects")


@router.get("/test/applications/{user_id}/campaign/{campaign_id}", response_model=CampaignClickResponse)
def test_get_campaign_details(
    user_id: str,
    campaign_id: str,
    db: Session = Depends(get_db),
) -> CampaignClickResponse:
    """
    TEST ENDPOINT - Get campaign click data without authentication.
    For development/testing purposes only.

    **Warning:** This endpoint is disabled in production unless
    ENABLE_TEST_ENDPOINTS=true is set.
    """
    if not ENABLE_TEST_ENDPOINTS:
        logger.warning(f"Test endpoint called in production: user={user_id}, campaign={campaign_id}")
        raise HTTPException(
            status_code=403,
            detail="Test endpoints are disabled in production"
        )

    try:
        logger.debug(f"Test endpoint: fetching campaign {campaign_id} for user {user_id}")
        result = my_projects_service.get_campaign_click_data(db, user_id, campaign_id)
        return result
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif "no relationship" in error_msg.lower():
            raise HTTPException(status_code=403, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch campaign details")
