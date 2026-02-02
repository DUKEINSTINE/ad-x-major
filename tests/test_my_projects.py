"""
Functional tests for the unified my-projects endpoints.

Tests the following scenarios:
1. GET /my-projects/applications - Returns unified list of user's campaigns
2. GET /my-projects/applications/{campaign_id} - Returns role-specific view on click
3. Owner sees applicant list when clicking their campaign
4. Applicant sees their application details when clicking a campaign they applied to
5. Role filtering works correctly
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from core.database import Base, get_db
from core.models import User, Campaign, CampaignParticipation

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Apply the override
app.dependency_overrides[get_db] = override_get_db

# Create the test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_users(db_session):
    """Create sample users for testing."""
    # Brand owner user
    brand_user = User(
        id="brand_user_001",
        username="techbrand",
        email="brand@test.com",
        hashed_password="hashedpw123",
        is_active=True,
        is_verified=True,
    )

    # Creator/applicant user
    creator_user = User(
        id="creator_user_001",
        username="creator_john",
        email="creator@test.com",
        hashed_password="hashedpw456",
        is_active=True,
        is_verified=True,
    )

    # Another creator
    creator_user_2 = User(
        id="creator_user_002",
        username="creator_jane",
        email="jane@test.com",
        hashed_password="hashedpw789",
        is_active=True,
        is_verified=True,
    )

    db_session.add_all([brand_user, creator_user, creator_user_2])
    db_session.commit()

    return {
        "brand": brand_user,
        "creator1": creator_user,
        "creator2": creator_user_2,
    }


@pytest.fixture
def sample_campaigns(db_session, sample_users):
    """Create sample campaigns for testing."""
    # Campaign owned by brand_user
    campaign1 = Campaign(
        id=1,
        user_id=sample_users["brand"].id,
        title="Tech Product Launch",
        summary="Promote our new tech gadget",
        description="Full campaign description here",
        budget=5000.0,
        target_views=10000,
        category="TECH",
        is_active=True,
    )

    # Another campaign owned by brand_user
    campaign2 = Campaign(
        id=2,
        user_id=sample_users["brand"].id,
        title="Software Launch Campaign",
        summary="Launch our new software",
        description="Another campaign description",
        budget=3000.0,
        target_views=5000,
        category="SOFTWARE",
        is_active=True,
    )

    # Campaign owned by creator1 (they're also a brand for this one)
    campaign3 = Campaign(
        id=3,
        user_id=sample_users["creator1"].id,
        title="Creator's Own Campaign",
        summary="Creator is the brand here",
        description="Creator-owned campaign",
        budget=1000.0,
        target_views=2000,
        category="LIFESTYLE",
        is_active=True,
    )

    db_session.add_all([campaign1, campaign2, campaign3])
    db_session.commit()

    return {
        "campaign1": campaign1,
        "campaign2": campaign2,
        "campaign3": campaign3,
    }


@pytest.fixture
def sample_participations(db_session, sample_users, sample_campaigns):
    """Create sample participations (applications) for testing."""
    # Creator1 applied to Campaign1 (pending)
    participation1 = CampaignParticipation(
        id=1,
        user_id=sample_users["creator1"].id,
        campaign_id=sample_campaigns["campaign1"].id,
        reason_for_participation="I love tech content!",
        is_pending=True,
        is_approved=False,
        terms_accepted=True,
    )

    # Creator1 applied to Campaign2 (approved)
    participation2 = CampaignParticipation(
        id=2,
        user_id=sample_users["creator1"].id,
        campaign_id=sample_campaigns["campaign2"].id,
        reason_for_participation="Software is my passion",
        is_pending=False,
        is_approved=True,
        terms_accepted=True,
        review_message="Welcome to the team!",
    )

    # Creator2 applied to Campaign1 (rejected)
    participation3 = CampaignParticipation(
        id=3,
        user_id=sample_users["creator2"].id,
        campaign_id=sample_campaigns["campaign1"].id,
        reason_for_participation="Tech enthusiast here",
        is_pending=False,
        is_approved=False,
        terms_accepted=True,
        rejection_reason="Not enough followers",
    )

    # Creator2 applied to Campaign3 (pending)
    participation4 = CampaignParticipation(
        id=4,
        user_id=sample_users["creator2"].id,
        campaign_id=sample_campaigns["campaign3"].id,
        reason_for_participation="Lifestyle content creator",
        is_pending=True,
        is_approved=False,
        terms_accepted=True,
    )

    db_session.add_all([participation1, participation2, participation3, participation4])
    db_session.commit()

    return {
        "p1": participation1,
        "p2": participation2,
        "p3": participation3,
        "p4": participation4,
    }


class TestUnifiedMyProjectsEndpoints:
    """Test cases for the unified my-projects endpoints."""

    def test_get_my_projects_as_brand_owner(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """
        Test that a brand owner sees their campaigns with application stats.

        Expected: brand_user owns 2 campaigns, should see them with stats.
        """
        user_id = sample_users["brand"].id
        response = client.get(f"/my-projects/test/applications/{user_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "user_id" in data
        assert "total_campaigns" in data
        assert "campaigns_as_owner" in data
        assert "campaigns_as_applicant" in data
        assert "campaigns" in data

        # brand_user owns 2 campaigns and has applied to 0
        assert data["campaigns_as_owner"] == 2
        assert data["campaigns_as_applicant"] == 0
        assert data["total_campaigns"] == 2

        # Check that campaigns have owner role
        for campaign in data["campaigns"]:
            assert campaign["user_role"] == "owner"
            assert "application_stats" in campaign

    def test_get_my_projects_as_applicant(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """
        Test that an applicant sees campaigns they applied to with status info.

        Expected: creator1 owns 1 campaign and applied to 2 campaigns.
        """
        user_id = sample_users["creator1"].id
        response = client.get(f"/my-projects/test/applications/{user_id}")

        assert response.status_code == 200
        data = response.json()

        # creator1 owns 1 campaign and applied to 2
        assert data["campaigns_as_owner"] == 1
        assert data["campaigns_as_applicant"] == 2
        assert data["total_campaigns"] == 3

        # Check campaigns
        for campaign in data["campaigns"]:
            if campaign["user_role"] == "applicant":
                assert "application_status" in campaign
                assert campaign["application_status"] in ["pending", "approved", "rejected"]
            else:
                assert "application_stats" in campaign

    def test_get_my_projects_mixed_roles(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """
        Test that a user with both roles sees correct view for each.

        Expected: creator1 has both owner and applicant roles across different campaigns.
        """
        user_id = sample_users["creator1"].id
        response = client.get(f"/my-projects/test/applications/{user_id}")

        assert response.status_code == 200
        data = response.json()

        owner_campaigns = [c for c in data["campaigns"] if c["user_role"] == "owner"]
        applicant_campaigns = [c for c in data["campaigns"] if c["user_role"] == "applicant"]

        # creator1 owns campaign3
        assert len(owner_campaigns) == 1
        assert owner_campaigns[0]["id"] == "3"

        # creator1 applied to campaign1 and campaign2
        assert len(applicant_campaigns) == 2
        campaign_ids = [c["id"] for c in applicant_campaigns]
        assert "1" in campaign_ids
        assert "2" in campaign_ids

    def test_campaign_click_as_owner(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """
        Test that clicking a campaign as owner returns applicant list.

        Expected: brand_user clicking campaign1 sees list of applicants.
        """
        user_id = sample_users["brand"].id
        campaign_id = sample_campaigns["campaign1"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/{campaign_id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify owner view
        assert data["user_role"] == "owner"
        assert data["campaign_id"] == str(campaign_id)
        assert "applicants" in data
        assert data["application_details"] is None

        # campaign1 has 2 applicants (creator1 and creator2)
        assert len(data["applicants"]) == 2

        # Check applicant data structure
        for applicant in data["applicants"]:
            assert "user_id" in applicant
            assert "username" in applicant
            assert "status" in applicant
            assert applicant["status"] in ["pending", "approved", "rejected"]

    def test_campaign_click_as_applicant(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """
        Test that clicking a campaign as applicant returns application details.

        Expected: creator1 clicking campaign1 sees their application status.
        """
        user_id = sample_users["creator1"].id
        campaign_id = sample_campaigns["campaign1"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/{campaign_id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify applicant view
        assert data["user_role"] == "applicant"
        assert data["campaign_id"] == str(campaign_id)
        assert "application_details" in data
        assert data["applicants"] is None

        # Check application details
        details = data["application_details"]
        assert details["status"] == "pending"
        assert "reason_for_participation" in details
        assert "applied_at" in details

    def test_application_status_pending(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Test that pending application shows correct status."""
        user_id = sample_users["creator1"].id
        campaign_id = sample_campaigns["campaign1"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/{campaign_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["application_details"]["status"] == "pending"

    def test_application_status_approved_with_message(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Test that approved application shows review message."""
        user_id = sample_users["creator1"].id
        campaign_id = sample_campaigns["campaign2"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/{campaign_id}"
        )

        assert response.status_code == 200
        data = response.json()

        details = data["application_details"]
        assert details["status"] == "approved"
        assert details["review_message"] == "Welcome to the team!"

    def test_application_status_rejected_with_reason(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Test that rejected application shows rejection reason."""
        user_id = sample_users["creator2"].id
        campaign_id = sample_campaigns["campaign1"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/{campaign_id}"
        )

        assert response.status_code == 200
        data = response.json()

        details = data["application_details"]
        assert details["status"] == "rejected"
        assert details["rejection_reason"] == "Not enough followers"

    def test_campaign_not_found(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Test that clicking a non-existent campaign returns 404."""
        user_id = sample_users["brand"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/99999"
        )

        assert response.status_code == 404

    def test_no_relationship_with_campaign(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Test that user with no relationship to campaign returns 404."""
        # creator2 has no relationship with campaign2
        user_id = sample_users["creator2"].id
        campaign_id = sample_campaigns["campaign2"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/{campaign_id}"
        )

        # Should return 404 since user is neither owner nor applicant
        assert response.status_code == 404

    def test_empty_projects_for_new_user(self, db_session, sample_users):
        """Test that a user with no campaigns or applications gets empty list."""
        # Create a new user with no campaigns or applications
        new_user = User(
            id="new_user_001",
            username="newbie",
            email="newbie@test.com",
            hashed_password="hashedpw000",
            is_active=True,
        )
        db_session.add(new_user)
        db_session.commit()

        response = client.get(f"/my-projects/test/applications/{new_user.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["total_campaigns"] == 0
        assert data["campaigns_as_owner"] == 0
        assert data["campaigns_as_applicant"] == 0
        assert len(data["campaigns"]) == 0

    def test_application_stats_accuracy(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Test that application stats for owner are accurate."""
        user_id = sample_users["brand"].id
        response = client.get(f"/my-projects/test/applications/{user_id}")

        assert response.status_code == 200
        data = response.json()

        # Find campaign1 in the response
        campaign1_data = next(
            (c for c in data["campaigns"] if c["id"] == "1"), None
        )
        assert campaign1_data is not None

        # campaign1 has 2 applicants: 1 pending, 1 rejected
        stats = campaign1_data["application_stats"]
        assert stats["total"] == 2
        assert stats["pending"] == 1
        assert stats["rejected"] == 1
        assert stats["approved"] == 0

        # Find campaign2 in the response
        campaign2_data = next(
            (c for c in data["campaigns"] if c["id"] == "2"), None
        )
        assert campaign2_data is not None

        # campaign2 has 1 applicant: approved
        stats = campaign2_data["application_stats"]
        assert stats["total"] == 1
        assert stats["pending"] == 0
        assert stats["rejected"] == 0
        assert stats["approved"] == 1


class TestMyProjectsResponseStructure:
    """Test the response structure matches the expected schema."""

    def test_my_projects_response_schema(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Verify the my-projects response matches the expected schema."""
        user_id = sample_users["creator1"].id
        response = client.get(f"/my-projects/test/applications/{user_id}")

        assert response.status_code == 200
        data = response.json()

        # Top-level fields
        assert isinstance(data["user_id"], str)
        assert isinstance(data["total_campaigns"], int)
        assert isinstance(data["campaigns_as_owner"], int)
        assert isinstance(data["campaigns_as_applicant"], int)
        assert isinstance(data["campaigns"], list)
        assert isinstance(data["message"], str)

    def test_campaign_schema_for_owner(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Verify campaign schema when user is owner."""
        user_id = sample_users["brand"].id
        response = client.get(f"/my-projects/test/applications/{user_id}")

        data = response.json()
        campaign = data["campaigns"][0]

        # Campaign fields
        assert isinstance(campaign["id"], str)
        assert isinstance(campaign["title"], str)
        assert isinstance(campaign["summary"], str)
        assert isinstance(campaign["budget"], (int, float))
        assert isinstance(campaign["category"], str)
        assert campaign["user_role"] == "owner"

        # Owner-specific fields
        assert isinstance(campaign["application_stats"], dict)
        assert "total" in campaign["application_stats"]
        assert "pending" in campaign["application_stats"]
        assert "approved" in campaign["application_stats"]
        assert "rejected" in campaign["application_stats"]

    def test_campaign_schema_for_applicant(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Verify campaign schema when user is applicant."""
        user_id = sample_users["creator1"].id
        response = client.get(f"/my-projects/test/applications/{user_id}")

        data = response.json()

        # Find an applicant campaign
        applicant_campaign = next(
            (c for c in data["campaigns"] if c["user_role"] == "applicant"), None
        )
        assert applicant_campaign is not None

        # Applicant-specific fields
        assert applicant_campaign["user_role"] == "applicant"
        assert applicant_campaign["application_status"] in ["pending", "approved", "rejected"]
        assert "applied_at" in applicant_campaign

    def test_campaign_click_response_schema_for_owner(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Verify campaign click response schema for owner."""
        user_id = sample_users["brand"].id
        campaign_id = sample_campaigns["campaign1"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/{campaign_id}"
        )

        data = response.json()

        assert isinstance(data["campaign_id"], str)
        assert isinstance(data["campaign_title"], str)
        assert data["user_role"] == "owner"
        assert isinstance(data["applicants"], list)
        assert data["application_details"] is None

        # Verify applicant schema
        if data["applicants"]:
            applicant = data["applicants"][0]
            assert "user_id" in applicant
            assert "username" in applicant
            assert "status" in applicant
            assert "applied_at" in applicant

    def test_campaign_click_response_schema_for_applicant(
        self, db_session, sample_users, sample_campaigns, sample_participations
    ):
        """Verify campaign click response schema for applicant."""
        user_id = sample_users["creator1"].id
        campaign_id = sample_campaigns["campaign2"].id

        response = client.get(
            f"/my-projects/test/applications/{user_id}/campaign/{campaign_id}"
        )

        data = response.json()

        assert isinstance(data["campaign_id"], str)
        assert isinstance(data["campaign_title"], str)
        assert data["user_role"] == "applicant"
        assert data["applicants"] is None
        assert isinstance(data["application_details"], dict)

        # Verify application details schema
        details = data["application_details"]
        assert "participation_id" in details
        assert "status" in details
        assert "applied_at" in details
        assert "reason_for_participation" in details


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
