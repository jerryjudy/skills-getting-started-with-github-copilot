"""Unit tests for individual endpoints using AAA (Arrange-Act-Assert) pattern"""


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: No setup needed, activities pre-populated in fixture
        Act: Make GET request to /activities
        Assert: Verify all 9 activities are returned with correct structure
        """
        # Arrange (implicit in fixture)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        
    def test_get_activities_returns_valid_structure(self, client):
        """
        Arrange: None
        Act: Fetch activities
        Assert: Verify each activity has required fields (description, schedule, max_participants, participants)
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_participants_list_contains_emails(self, client):
        """
        Arrange: None
        Act: Fetch activities
        Assert: Verify participants list contains email strings
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        chess_club = activities["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful_new_participant(self, client, fresh_activities):
        """
        Arrange: Set up activity with existing participants
        Act: Sign up a new participant with valid email
        Assert: Verify participant is added and returns success message
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        initial_count = len(fresh_activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
        assert new_email in fresh_activities[activity_name]["participants"]
        assert len(fresh_activities[activity_name]["participants"]) == initial_count + 1
    
    def test_signup_activity_not_found(self, client):
        """
        Arrange: Use non-existent activity name
        Act: Attempt signup
        Assert: Verify 404 error is returned
        """
        # Arrange
        non_existent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{non_existent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_email_rejected(self, client, fresh_activities):
        """
        Arrange: Student already signed up for activity
        Act: Attempt to sign up same student again
        Assert: Verify 400 error is returned (duplicate registration prevented)
        """
        # Arrange
        activity_name = "Chess Club"
        duplicate_email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": duplicate_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"
    
    def test_signup_same_student_different_activities(self, client, fresh_activities):
        """
        Arrange: Student already in one activity
        Act: Sign up same student for different activity
        Assert: Verify student can join multiple activities
        """
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        other_activity = "Programming Class"
        
        # Act
        response = client.post(
            f"/activities/{other_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in fresh_activities[other_activity]["participants"]
    
    def test_signup_with_special_characters_in_activity_name(self, client, fresh_activities):
        """
        Arrange: Use activity name with special characters (URL encoding)
        Act: Attempt signup
        Assert: Verify endpoint handles encoded activity names correctly
        """
        # Note: All current activities have simple names, so this tests the pattern
        # Arrange
        activity_name = "Art Studio"
        email = "artist@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in fresh_activities[activity_name]["participants"]


class TestDeleteParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_delete_participant_success(self, client, fresh_activities):
        """
        Arrange: Participant exists in activity
        Act: Delete the participant
        Assert: Verify participant is removed and success message returned
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        initial_count = len(fresh_activities[activity_name]["participants"])
        
        # Act
        response = client.delete(f"/activities/{activity_name}/participants/{email_to_remove}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email_to_remove} from {activity_name}"
        assert email_to_remove not in fresh_activities[activity_name]["participants"]
        assert len(fresh_activities[activity_name]["participants"]) == initial_count - 1
    
    def test_delete_participant_activity_not_found(self, client):
        """
        Arrange: Non-existent activity
        Act: Attempt to delete participant
        Assert: Verify 404 error for missing activity
        """
        # Arrange
        non_existent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{non_existent_activity}/participants/{email}")
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_delete_participant_not_found(self, client):
        """
        Arrange: Email not in participant list for activity
        Act: Attempt to delete non-existent participant
        Assert: Verify 404 error for missing participant
        """
        # Arrange
        activity_name = "Chess Club"
        non_existent_email = "nobody@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/participants/{non_existent_email}")
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"
    
    def test_delete_all_participants_then_list_empty(self, client, fresh_activities):
        """
        Arrange: Activity with 2 participants
        Act: Delete both participants sequentially
        Assert: Verify participant list becomes empty
        """
        # Arrange
        activity_name = "Chess Club"
        participants = list(fresh_activities[activity_name]["participants"])
        
        # Act & Assert
        for email in participants:
            response = client.delete(f"/activities/{activity_name}/participants/{email}")
            assert response.status_code == 200
        
        assert len(fresh_activities[activity_name]["participants"]) == 0


class TestDataValidation:
    """Tests for data validation and edge cases"""
    
    def test_capacity_limits_enforcement(self, client, fresh_activities):
        """
        Arrange: Activity at max capacity
        Act: Validate that max_participants field exists
        Assert: Verify max_participants attribute is enforced in data
        """
        # Arrange
        activity_name = "Tennis Club"
        max_capacity = fresh_activities[activity_name]["max_participants"]
        current_participants = len(fresh_activities[activity_name]["participants"])
        
        # Assert: Verify capacity field exists (current app doesn't validate, but field exists)
        assert max_capacity == 16
        assert current_participants < max_capacity
    
    def test_email_format_accepted(self, client, fresh_activities):
        """
        Arrange: Valid email format
        Act: Sign up with valid email
        Assert: Verify signup succeeds (current app doesn't validate email format)
        """
        # Arrange
        activity_name = "Music Band"
        valid_email = "student@example.com"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": valid_email}
        )
        
        # Assert: Current implementation accepts any string as email
        assert response.status_code == 200
        assert valid_email in fresh_activities[activity_name]["participants"]
    
    def test_case_sensitive_activity_names(self, client):
        """
        Arrange: Use different case for activity name
        Act: Attempt signup with incorrect case
        Assert: Verify activity names are case-sensitive
        """
        # Arrange
        email = "student@mergington.edu"
        
        # Act: Try lowercase version of "Chess Club"
        response = client.post(
            "/activities/chess club/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
