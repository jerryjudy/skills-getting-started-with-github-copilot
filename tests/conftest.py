"""Shared fixtures for all tests"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """
    Provide a TestClient with a fresh, isolated copy of activities for each test.
    This ensures test isolation and prevents state leakage between tests.
    """
    # Arrange: Create a deep copy of the original activities to isolate tests
    original_activities = copy.deepcopy(activities)
    activities.clear()
    activities.update(original_activities)
    
    yield TestClient(app)
    
    # Cleanup: Restore original state after test completes
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def fresh_activities():
    """
    Provide direct access to the activities dict for tests that need it.
    Ensures fresh state before each test and restores after completion.
    """
    original = copy.deepcopy(activities)
    activities.clear()
    activities.update(original)
    yield activities
    activities.clear()
    activities.update(original)
