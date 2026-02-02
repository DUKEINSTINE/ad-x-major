# my_projects/schemas.py
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


class ApplicationStats(BaseModel):
    """Stats for a campaign's applications (for owners)"""
    total: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0


class MyProjectCampaign(BaseModel):
    """
    A campaign in the user's projects list.
    Contains role information to determine what view to show on click.
    """
    # Campaign details
    id: str
    title: str
    summary: str
    description: str
    budget: float
    target_views: int
    poster_url: Optional[str] = None
    category: str
    status: str  # active, inactive, completed
    created_at: datetime

    # User's role for this campaign
    user_role: Literal["owner", "applicant"]

    # Owner-specific data (only populated if user_role == "owner")
    application_stats: Optional[ApplicationStats] = None

    # Applicant-specific data (only populated if user_role == "applicant")
    application_status: Optional[Literal["pending", "approved", "rejected"]] = None
    applied_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    review_message: Optional[str] = None
    rejection_reason: Optional[str] = None


class MyProjectsResponse(BaseModel):
    """Response for the unified my-projects/applications endpoint"""
    user_id: str
    total_campaigns: int
    campaigns_as_owner: int
    campaigns_as_applicant: int
    campaigns: List[MyProjectCampaign]
    message: str


class CampaignClickResponse(BaseModel):
    """
    Response when user clicks a campaign.
    Returns appropriate data based on user's role.
    """
    campaign_id: str
    campaign_title: str
    user_role: Literal["owner", "applicant"]

    # For owners - list of applicants
    applicants: Optional[List["ApplicantInfo"]] = None

    # For applicants - their application details
    application_details: Optional["ApplicationDetails"] = None


class ApplicantInfo(BaseModel):
    """Info about an applicant (shown to campaign owner)"""
    user_id: str
    username: str
    email: str
    profile_image_url: Optional[str] = None
    rating: float
    user_level: int
    is_verified: bool

    # Application details
    participation_id: str
    status: Literal["pending", "approved", "rejected"]
    applied_at: datetime
    approved_at: Optional[datetime] = None
    reason_for_participation: str
    review_message: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApplicationDetails(BaseModel):
    """Details of user's own application (shown to applicant)"""
    participation_id: str
    status: Literal["pending", "approved", "rejected"]
    applied_at: datetime
    approved_at: Optional[datetime] = None
    reason_for_participation: str
    review_message: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Campaign owner info
    campaign_owner_id: str
    campaign_owner_username: str


# Update forward references
CampaignClickResponse.model_rebuild()
