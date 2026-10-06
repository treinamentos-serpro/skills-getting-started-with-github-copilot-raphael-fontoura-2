import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app, follow_redirects=False)


@pytest.fixture
def seeded_activities(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 10,
            "participants": ["existing@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


def test_root_redirects_to_static_index(client):
    # Arrange

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_available_activities(client, seeded_activities):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == seeded_activities


def test_signup_adds_student_to_activity(client, seeded_activities):
    # Arrange
    email = "new@example.com"

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@example.com for Chess Club"}
    assert email in seeded_activities["Chess Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client, seeded_activities):
    # Arrange
    email = "new@example.com"

    # Act
    response = client.post(
        "/activities/Unknown Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_existing_student(client, seeded_activities):
    # Arrange
    email = "existing@example.com"

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_requires_email(client, seeded_activities):
    # Arrange

    # Act
    response = client.post("/activities/Chess Club/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_removes_student_from_activity(client, seeded_activities):
    # Arrange
    email = "existing@example.com"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@example.com from Chess Club"
    }
    assert email not in seeded_activities["Chess Club"]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(
    client, seeded_activities
):
    # Arrange
    email = "existing@example.com"

    # Act
    response = client.delete(
        "/activities/Unknown Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_student(
    client, seeded_activities
):
    # Arrange
    email = "not-enrolled@example.com"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student not signed up for this activity"
    }