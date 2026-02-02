# my_projects/service.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core.models import User, Campaign, CampaignParticipation
from .schemas import (
    MyProjectCampaign,
    MyProjectsResponse,
    CampaignClickResponse,
    ApplicantInfo,
    ApplicationDetails,
    ApplicationStats,
)
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class MyProjectsService:
    """
    Service for unified my-projects functionality.
    Handles both owner and applicant views in a single interface.
    """

    def get_user_projects(self, db: Session, user_id: str) -> MyProjectsResponse:
        """
        Get all campaigns where user is either owner OR applicant.
        Returns unified list with role indicator for each campaign.
        """
        logger.info(f"🔍 Getting user projects for user_id={user_id}")

        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        campaigns_list: List[MyProjectCampaign] = []

        # 1. Get campaigns user CREATED (owner role)
        owned_campaigns = db.query(Campaign).filter(Campaign.user_id == user_id).all()

        for campaign in owned_campaigns:
            # Calculate application stats for this campaign
            participations = db.query(CampaignParticipation).filter(
                CampaignParticipation.campaign_id == campaign.id
            ).all()

            stats = ApplicationStats(
                total=len(participations),
                pending=len([p for p in participations if p.is_pending]),
                approved=len([p for p in participations if p.is_approved]),
                rejected=len([p for p in participations if not p.is_pending and not p.is_approved]),
            )

            campaigns_list.append(MyProjectCampaign(
                id=str(campaign.id),
                title=campaign.title,
                summary=campaign.summary,
                description=campaign.description,
                budget=campaign.budget,
                target_views=campaign.target_views,
                poster_url=campaign.poster_url,
                category=campaign.category,
                status="active" if campaign.is_active else "inactive",
                created_at=campaign.created_at,
                user_role="owner",
                application_stats=stats,
                # Applicant fields are None for owner
                application_status=None,
                applied_at=None,
                approved_at=None,
                review_message=None,
                rejection_reason=None,
            ))

        # 2. Get campaigns user APPLIED TO (applicant role)
        participations = db.query(CampaignParticipation).filter(
            CampaignParticipation.user_id == user_id
        ).all()

        for participation in participations:
            campaign = participation.campaign

            # Skip if user is also the owner (already added above)
            if str(campaign.user_id) == str(user_id):
                continue

            # Determine application status
            if participation.is_pending:
                status = "pending"
            elif participation.is_approved:
                status = "approved"
            else:
                status = "rejected"

            campaigns_list.append(MyProjectCampaign(
                id=str(campaign.id),
                title=campaign.title,
                summary=campaign.summary,
                description=campaign.description,
                budget=campaign.budget,
                target_views=campaign.target_views,
                poster_url=campaign.poster_url,
                category=campaign.category,
                status="active" if campaign.is_active else "inactive",
                created_at=campaign.created_at,
                user_role="applicant",
                # Owner fields are None for applicant
                application_stats=None,
                # Applicant-specific fields
                application_status=status,
                applied_at=participation.applied_at,
                approved_at=participation.approved_at,
                review_message=participation.review_message,
                rejection_reason=participation.rejection_reason,
            ))

        # Sort by created_at descending (most recent first)
        campaigns_list.sort(key=lambda x: x.created_at, reverse=True)

        # Calculate counts
        owner_count = len([c for c in campaigns_list if c.user_role == "owner"])
        applicant_count = len([c for c in campaigns_list if c.user_role == "applicant"])

        logger.info(
            f"✅ Found {len(campaigns_list)} campaigns for user {user_id} "
            f"(owner={owner_count}, applicant={applicant_count})"
        )

        return MyProjectsResponse(
            user_id=user_id,
            total_campaigns=len(campaigns_list),
            campaigns_as_owner=owner_count,
            campaigns_as_applicant=applicant_count,
            campaigns=campaigns_list,
            message=f"Found {len(campaigns_list)} campaigns for user {user_id}",
        )

    def get_campaign_click_data(
        self, db: Session, user_id: str, campaign_id: str
    ) -> CampaignClickResponse:
        """
        Get data for when user clicks a campaign.
        Returns appropriate view data based on user's role.
        """
        logger.info(f"🔍 Getting campaign click data for user={user_id}, campaign={campaign_id}")

        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == int(campaign_id)).first()
        if not campaign:
            logger.warning(f"Campaign not found: {campaign_id}")
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Determine user's role for this campaign
        is_owner = str(campaign.user_id) == str(user_id)

        participation = db.query(CampaignParticipation).filter(
            CampaignParticipation.campaign_id == int(campaign_id),
            CampaignParticipation.user_id == user_id,
        ).first()

        is_applicant = participation is not None

        if is_owner:
            # User is owner - return list of applicants
            applicants = self._get_campaign_applicants(db, campaign_id)
            return CampaignClickResponse(
                campaign_id=campaign_id,
                campaign_title=campaign.title,
                user_role="owner",
                applicants=applicants,
                application_details=None,
            )
        elif is_applicant:
            # User is applicant - return their application details
            application_details = self._get_application_details(db, participation, campaign)
            return CampaignClickResponse(
                campaign_id=campaign_id,
                campaign_title=campaign.title,
                user_role="applicant",
                applicants=None,
                application_details=application_details,
            )
        else:
            raise ValueError(f"User {user_id} has no relationship with campaign {campaign_id}")

    def _get_campaign_applicants(self, db: Session, campaign_id: str) -> List[ApplicantInfo]:
        """Get all applicants for a campaign (for owner view)"""
        participations = db.query(CampaignParticipation).filter(
            CampaignParticipation.campaign_id == int(campaign_id)
        ).all()

        applicants = []
        for p in participations:
            user = db.query(User).filter(User.id == p.user_id).first()
            if not user:
                continue

            # Determine status
            if p.is_pending:
                status = "pending"
            elif p.is_approved:
                status = "approved"
            else:
                status = "rejected"

            applicants.append(ApplicantInfo(
                user_id=str(user.id),
                username=user.username,
                email=user.email,
                profile_image_url=user.profile_image_url,
                rating=float(user.rating) if user.rating else 0.0,
                user_level=user.user_level,
                is_verified=user.is_verified,
                participation_id=str(p.id),
                status=status,
                applied_at=p.applied_at,
                approved_at=p.approved_at,
                reason_for_participation=p.reason_for_participation or "",
                review_message=p.review_message,
                rejection_reason=p.rejection_reason,
            ))

        # Sort by applied_at descending
        applicants.sort(key=lambda x: x.applied_at, reverse=True)
        return applicants

    def _get_application_details(
        self, db: Session, participation: CampaignParticipation, campaign: Campaign
    ) -> ApplicationDetails:
        """Get application details for user's own application (for applicant view)"""
        # Get campaign owner info
        owner = db.query(User).filter(User.id == campaign.user_id).first()

        # Determine status
        if participation.is_pending:
            status = "pending"
        elif participation.is_approved:
            status = "approved"
        else:
            status = "rejected"

        return ApplicationDetails(
            participation_id=str(participation.id),
            status=status,
            applied_at=participation.applied_at,
            approved_at=participation.approved_at,
            reason_for_participation=participation.reason_for_participation or "",
            review_message=participation.review_message,
            rejection_reason=participation.rejection_reason,
            campaign_owner_id=str(owner.id) if owner else "",
            campaign_owner_username=owner.username if owner else "Unknown",
        )


# Singleton instance
my_projects_service = MyProjectsService()
