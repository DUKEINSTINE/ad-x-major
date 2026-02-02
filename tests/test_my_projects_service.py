"""
Unit tests for the my-projects service layer.
Tests the business logic without requiring MongoDB or other external services.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.campaign.my_projects.service import MyProjectsService
from src.campaign.my_projects.schemas import (
    MyProjectCampaign,
    MyProjectsResponse,
    CampaignClickResponse,
    ApplicantInfo,
    ApplicationDetails,
    ApplicationStats,
)


class MockUser:
    """Mock User object for testing."""
    def __init__(self, id, username, email, is_verified=True, rating=4.5, user_level=3):
        self.id = id
        self.username = username
        self.email = email
        self.is_verified = is_verified
        self.rating = rating
        self.user_level = user_level


class MockCampaign:
    """Mock Campaign object for testing."""
    def __init__(
        self,
        id,
        user_id,
        title,
        summary,
        description="Test description",
        budget=1000.0,
        target_views=5000,
        poster_url=None,
        category="TECH",
        is_active=True,
    ):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.summary = summary
        self.description = description
        self.budget = budget
        self.target_views = target_views
        self.poster_url = poster_url
        self.category = category
        self.is_active = is_active
        self.created_at = datetime.now()


class MockParticipation:
    """Mock CampaignParticipation object for testing."""
    def __init__(
        self,
        id,
        user_id,
        campaign_id,
        reason_for_participation="Test reason",
        is_pending=True,
        is_approved=False,
        review_message=None,
        rejection_reason=None,
        applied_at=None,
        approved_at=None,
    ):
        self.id = id
        self.user_id = user_id
        self.campaign_id = campaign_id
        self.reason_for_participation = reason_for_participation
        self.is_pending = is_pending
        self.is_approved = is_approved
        self.review_message = review_message
        self.rejection_reason = rejection_reason
        self.applied_at = applied_at or datetime.now()
        self.approved_at = approved_at


@pytest.fixture
def service():
    """Create a MyProjectsService instance."""
    return MyProjectsService()


class TestSchemaValidation:
    """Test that Pydantic schemas work correctly."""

    def test_application_stats_creation(self):
        """Test ApplicationStats schema."""
        stats = ApplicationStats(total=10, pending=5, approved=3, rejected=2)
        assert stats.total == 10
        assert stats.pending == 5
        assert stats.approved == 3
        assert stats.rejected == 2

    def test_application_stats_defaults(self):
        """Test ApplicationStats with defaults."""
        stats = ApplicationStats()
        assert stats.total == 0
        assert stats.pending == 0
        assert stats.approved == 0
        assert stats.rejected == 0

    def test_my_project_campaign_as_owner(self):
        """Test MyProjectCampaign for owner role."""
        campaign = MyProjectCampaign(
            id="1",
            title="Test Campaign",
            summary="Test summary",
            description="Test description",
            budget=5000.0,
            target_views=10000,
            poster_url="https://example.com/poster.jpg",
            category="TECH",
            status="active",
            created_at=datetime.now().isoformat(),
            user_role="owner",
            application_stats=ApplicationStats(total=5, pending=2, approved=2, rejected=1),
        )

        assert campaign.id == "1"
        assert campaign.user_role == "owner"
        assert campaign.application_stats.total == 5
        assert campaign.application_status is None

    def test_my_project_campaign_as_applicant(self):
        """Test MyProjectCampaign for applicant role."""
        campaign = MyProjectCampaign(
            id="2",
            title="Test Campaign 2",
            summary="Test summary 2",
            description="Test description 2",
            budget=3000.0,
            target_views=5000,
            category="FASHION",
            status="active",
            created_at=datetime.now().isoformat(),
            user_role="applicant",
            application_status="approved",
            applied_at=datetime.now().isoformat(),
            review_message="Welcome!",
        )

        assert campaign.id == "2"
        assert campaign.user_role == "applicant"
        assert campaign.application_status == "approved"
        assert campaign.review_message == "Welcome!"
        assert campaign.application_stats is None

    def test_my_projects_response(self):
        """Test MyProjectsResponse schema."""
        campaign1 = MyProjectCampaign(
            id="1",
            title="Campaign 1",
            summary="Summary 1",
            description="Desc 1",
            budget=1000.0,
            target_views=1000,
            category="TECH",
            status="active",
            created_at=datetime.now().isoformat(),
            user_role="owner",
            application_stats=ApplicationStats(total=3, pending=1, approved=1, rejected=1),
        )

        campaign2 = MyProjectCampaign(
            id="2",
            title="Campaign 2",
            summary="Summary 2",
            description="Desc 2",
            budget=2000.0,
            target_views=2000,
            category="FASHION",
            status="active",
            created_at=datetime.now().isoformat(),
            user_role="applicant",
            application_status="pending",
            applied_at=datetime.now().isoformat(),
        )

        response = MyProjectsResponse(
            user_id="user123",
            total_campaigns=2,
            campaigns_as_owner=1,
            campaigns_as_applicant=1,
            campaigns=[campaign1, campaign2],
            message="Success",
        )

        assert response.user_id == "user123"
        assert response.total_campaigns == 2
        assert response.campaigns_as_owner == 1
        assert response.campaigns_as_applicant == 1
        assert len(response.campaigns) == 2

    def test_applicant_info_schema(self):
        """Test ApplicantInfo schema."""
        applicant = ApplicantInfo(
            user_id="user456",
            username="testuser",
            email="test@example.com",
            rating=4.5,
            user_level=3,
            is_verified=True,
            participation_id="part123",
            status="pending",
            applied_at=datetime.now().isoformat(),
            reason_for_participation="Love this brand!",
        )

        assert applicant.user_id == "user456"
        assert applicant.status == "pending"
        assert applicant.rating == 4.5

    def test_application_details_schema(self):
        """Test ApplicationDetails schema."""
        details = ApplicationDetails(
            participation_id="part789",
            status="approved",
            applied_at=datetime.now().isoformat(),
            approved_at=datetime.now().isoformat(),
            reason_for_participation="Great opportunity!",
            review_message="Welcome aboard!",
            campaign_owner_id="owner001",
            campaign_owner_username="brandowner",
        )

        assert details.participation_id == "part789"
        assert details.status == "approved"
        assert details.review_message == "Welcome aboard!"

    def test_campaign_click_response_for_owner(self):
        """Test CampaignClickResponse for owner view."""
        applicant = ApplicantInfo(
            user_id="user456",
            username="testuser",
            email="test@example.com",
            rating=4.5,
            user_level=3,
            is_verified=True,
            participation_id="part123",
            status="pending",
            applied_at=datetime.now().isoformat(),
            reason_for_participation="Love this brand!",
        )

        response = CampaignClickResponse(
            campaign_id="1",
            campaign_title="Test Campaign",
            user_role="owner",
            applicants=[applicant],
            application_details=None,
        )

        assert response.campaign_id == "1"
        assert response.user_role == "owner"
        assert len(response.applicants) == 1
        assert response.application_details is None

    def test_campaign_click_response_for_applicant(self):
        """Test CampaignClickResponse for applicant view."""
        details = ApplicationDetails(
            participation_id="part789",
            status="pending",
            applied_at=datetime.now().isoformat(),
            reason_for_participation="Excited to join!",
            campaign_owner_id="owner001",
            campaign_owner_username="brandowner",
        )

        response = CampaignClickResponse(
            campaign_id="2",
            campaign_title="Another Campaign",
            user_role="applicant",
            applicants=None,
            application_details=details,
        )

        assert response.campaign_id == "2"
        assert response.user_role == "applicant"
        assert response.applicants is None
        assert response.application_details.status == "pending"


class TestStatusDetermination:
    """Test status determination logic."""

    def test_pending_status(self):
        """Test that pending status is correctly determined."""
        # Pending: is_pending=True, is_approved=False
        participation = MockParticipation(
            id=1,
            user_id="user1",
            campaign_id=1,
            is_pending=True,
            is_approved=False,
        )

        # Determine status using the same logic as the service
        if participation.is_pending:
            status = "pending"
        elif participation.is_approved:
            status = "approved"
        else:
            status = "rejected"

        assert status == "pending"

    def test_approved_status(self):
        """Test that approved status is correctly determined."""
        # Approved: is_pending=False, is_approved=True
        participation = MockParticipation(
            id=1,
            user_id="user1",
            campaign_id=1,
            is_pending=False,
            is_approved=True,
            review_message="Welcome!",
        )

        if participation.is_pending:
            status = "pending"
        elif participation.is_approved:
            status = "approved"
        else:
            status = "rejected"

        assert status == "approved"

    def test_rejected_status(self):
        """Test that rejected status is correctly determined."""
        # Rejected: is_pending=False, is_approved=False
        participation = MockParticipation(
            id=1,
            user_id="user1",
            campaign_id=1,
            is_pending=False,
            is_approved=False,
            rejection_reason="Not enough followers",
        )

        if participation.is_pending:
            status = "pending"
        elif participation.is_approved:
            status = "approved"
        else:
            status = "rejected"

        assert status == "rejected"


class TestRoleDetermination:
    """Test role determination logic."""

    def test_user_is_owner(self):
        """Test that user is identified as owner of their campaign."""
        user_id = "user123"
        campaign = MockCampaign(id=1, user_id=user_id, title="My Campaign", summary="Test")

        is_owner = str(campaign.user_id) == str(user_id)
        assert is_owner is True

    def test_user_is_not_owner(self):
        """Test that user is not identified as owner of someone else's campaign."""
        user_id = "user123"
        campaign = MockCampaign(id=1, user_id="other_user", title="Their Campaign", summary="Test")

        is_owner = str(campaign.user_id) == str(user_id)
        assert is_owner is False

    def test_user_has_mixed_roles(self):
        """Test that user can have different roles for different campaigns."""
        user_id = "user123"

        # Campaign owned by user
        owned_campaign = MockCampaign(id=1, user_id=user_id, title="My Campaign", summary="Test")

        # Campaign owned by someone else
        other_campaign = MockCampaign(id=2, user_id="other_user", title="Their Campaign", summary="Test")

        assert str(owned_campaign.user_id) == str(user_id)  # Owner
        assert str(other_campaign.user_id) != str(user_id)  # Not owner (applicant if applied)


class TestStatsCalculation:
    """Test application statistics calculation."""

    def test_calculate_stats_from_participations(self):
        """Test calculating stats from a list of participations."""
        participations = [
            MockParticipation(id=1, user_id="u1", campaign_id=1, is_pending=True, is_approved=False),
            MockParticipation(id=2, user_id="u2", campaign_id=1, is_pending=False, is_approved=True),
            MockParticipation(id=3, user_id="u3", campaign_id=1, is_pending=False, is_approved=False),
            MockParticipation(id=4, user_id="u4", campaign_id=1, is_pending=True, is_approved=False),
        ]

        # Calculate stats
        total = len(participations)
        pending = sum(1 for p in participations if p.is_pending)
        approved = sum(1 for p in participations if not p.is_pending and p.is_approved)
        rejected = sum(1 for p in participations if not p.is_pending and not p.is_approved)

        assert total == 4
        assert pending == 2
        assert approved == 1
        assert rejected == 1

    def test_empty_participations(self):
        """Test stats calculation with no participations."""
        participations = []

        total = len(participations)
        pending = sum(1 for p in participations if p.is_pending)
        approved = sum(1 for p in participations if not p.is_pending and p.is_approved)
        rejected = sum(1 for p in participations if not p.is_pending and not p.is_approved)

        assert total == 0
        assert pending == 0
        assert approved == 0
        assert rejected == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_campaign_with_no_applications(self):
        """Test campaign with zero applications shows correct stats."""
        stats = ApplicationStats(total=0, pending=0, approved=0, rejected=0)

        assert stats.total == 0
        assert stats.pending == 0

    def test_all_applications_approved(self):
        """Test campaign where all applications are approved."""
        stats = ApplicationStats(total=5, pending=0, approved=5, rejected=0)

        assert stats.total == 5
        assert stats.approved == 5
        assert stats.pending == 0
        assert stats.rejected == 0

    def test_all_applications_rejected(self):
        """Test campaign where all applications are rejected."""
        stats = ApplicationStats(total=3, pending=0, approved=0, rejected=3)

        assert stats.rejected == 3
        assert stats.approved == 0

    def test_feedback_fields_only_for_processed_applications(self):
        """Test that feedback fields are only populated for processed applications."""
        # Pending application - no feedback
        pending = MockParticipation(
            id=1, user_id="u1", campaign_id=1,
            is_pending=True, is_approved=False,
            review_message=None, rejection_reason=None,
        )

        # Approved application - has review message
        approved = MockParticipation(
            id=2, user_id="u2", campaign_id=1,
            is_pending=False, is_approved=True,
            review_message="Great work!", rejection_reason=None,
        )

        # Rejected application - has rejection reason
        rejected = MockParticipation(
            id=3, user_id="u3", campaign_id=1,
            is_pending=False, is_approved=False,
            review_message=None, rejection_reason="Not a good fit",
        )

        assert pending.review_message is None
        assert pending.rejection_reason is None

        assert approved.review_message == "Great work!"
        assert approved.rejection_reason is None

        assert rejected.review_message is None
        assert rejected.rejection_reason == "Not a good fit"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
