"""Integration tests for multi-step workflows using AAA (Arrange-Act-Assert) pattern"""
import pytest
import threading
import time


class TestSignupWorkflows:
    """Tests for signup workflows and state persistence"""
    
    def test_signup_updates_activity_availability(self, client, fresh_activities):
        """
        Arrange: Get initial availability
        Act: Sign up new participant
        Assert: Verify availability decreases by 1
        """
        # Arrange
        activity_name = "Programming Class"
        new_email = "newprogrammer@mergington.edu"
        initial_availability = (
            fresh_activities[activity_name]["max_participants"] - 
            len(fresh_activities[activity_name]["participants"])
        )
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        response = client.get("/activities")
        activities_after = response.json()
        
        # Assert
        availability_after = (
            activities_after[activity_name]["max_participants"] - 
            len(activities_after[activity_name]["participants"])
        )
        assert availability_after == initial_availability - 1
        assert new_email in activities_after[activity_name]["participants"]
    
    def test_full_signup_delete_lifecycle(self, client, fresh_activities):
        """
        Arrange: Fresh state
        Act: Sign up → retrieve → delete → retrieve
        Assert: Verify state changes correctly at each step
        """
        # Arrange
        activity_name = "Music Band"
        email = "newmusician@mergington.edu"
        
        # Act 1: Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Act 2: Retrieve and verify signup
        get_response = client.get("/activities")
        activities = get_response.json()
        assert email in activities[activity_name]["participants"]
        participants_after_signup = len(activities[activity_name]["participants"])
        
        # Act 3: Delete
        delete_response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        assert delete_response.status_code == 200
        
        # Act 4: Retrieve and verify deletion
        get_response = client.get("/activities")
        activities = get_response.json()
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == participants_after_signup - 1
    
    def test_multiple_students_signup_same_activity(self, client, fresh_activities):
        """
        Arrange: Activity with existing participants
        Act: Sign up multiple new students sequentially
        Assert: Verify all are added to participant list
        """
        # Arrange
        activity_name = "Gym Class"
        new_emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        initial_count = len(fresh_activities[activity_name]["participants"])
        
        # Act
        for email in new_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        response = client.get("/activities")
        activities = response.json()
        final_count = len(activities[activity_name]["participants"])
        
        assert final_count == initial_count + len(new_emails)
        for email in new_emails:
            assert email in activities[activity_name]["participants"]
    
    def test_state_persists_across_requests(self, client, fresh_activities):
        """
        Arrange: Make initial change
        Act: Make multiple GET requests
        Assert: Verify state remains consistent across requests
        """
        # Arrange
        activity_name = "Debate Club"
        email = "debater@mergington.edu"
        
        # Act: Signup and make multiple requests
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: All subsequent requests see the same state
        for _ in range(3):
            response = client.get("/activities")
            activities = response.json()
            assert email in activities[activity_name]["participants"]
    
    def test_re_signup_after_deletion(self, client, fresh_activities):
        """
        Arrange: Student already in activity
        Act: Delete → signup same student again
        Assert: Verify student can re-join after deletion
        """
        # Arrange
        activity_name = "Science Club"
        email = "scientist@mergington.edu"
        
        # Act 1: Signup new student
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act 2: Delete student
        delete_response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        assert delete_response.status_code == 200
        
        # Act 3: Re-signup same student
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert signup_response.status_code == 200
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity_name]["participants"]


class TestConcurrentAccess:
    """Tests for concurrent/parallel access patterns"""
    
    def test_concurrent_signups_no_race_condition(self, client, fresh_activities):
        """
        Arrange: Setup for concurrent signups including duplicate emails
        Act: Multiple threads sign up for same activity simultaneously, some with the same email
        Assert: Unique emails succeed (200) and concurrent duplicate emails yield exactly
                one success (200) and the rest rejections (400)
        """
        # Arrange
        activity_name = "Art Studio"
        unique_emails = [f"artist{i}@mergington.edu" for i in range(3)]
        duplicate_email = "duplicate.artist@mergington.edu"
        # Three threads will attempt to sign up the same duplicate_email concurrently
        all_signup_args = unique_emails + [duplicate_email] * 3
        results = []
        lock = threading.Lock()

        def signup(email):
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            with lock:
                results.append((email, response.status_code))

        # Act: Launch concurrent signups (unique + duplicate attempts)
        threads = [threading.Thread(target=signup, args=(email,)) for email in all_signup_args]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert: All threads completed
        assert len(results) == len(all_signup_args)

        # Assert: Each unique email was accepted exactly once
        response = client.get("/activities")
        activities = response.json()
        for email in unique_emails:
            statuses = [s for e, s in results if e == email]
            assert statuses == [200], f"Expected unique signup for {email} to succeed"
            assert email in activities[activity_name]["participants"]

        # Assert: Exactly one duplicate signup succeeds; the rest are rejected
        duplicate_statuses = [s for e, s in results if e == duplicate_email]
        assert duplicate_statuses.count(200) == 1, (
            "Exactly one concurrent signup for the duplicate email should succeed"
        )
        assert duplicate_statuses.count(400) == 2, (
            "Remaining concurrent duplicate signups should be rejected with 400"
        )
        assert duplicate_email in activities[activity_name]["participants"]
    
    def test_concurrent_delete_and_signup_same_participant(self, client, fresh_activities):
        """
        Arrange: Setup thread-based concurrent operations
        Act: Attempt delete and re-signup of same participant simultaneously
        Assert: One operation succeeds, second properly fails/succeeds based on race result
        """
        # Arrange
        activity_name = "Tennis Club"
        email = "concurrent.player@mergington.edu"
        results = []
        
        # First, add the participant
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        def delete_op():
            response = client.delete(
                f"/activities/{activity_name}/participants/{email}"
            )
            results.append(("delete", response.status_code))
        
        def signup_op():
            time.sleep(0.001)  # Small delay to increase chance delete runs first
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            results.append(("signup", response.status_code))
        
        # Act: Launch concurrent operations
        threads = [
            threading.Thread(target=delete_op),
            threading.Thread(target=signup_op)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Assert: Both operations executed and produced an allowed race outcome
        assert len(results) == 2
        operations = [op[0] for op in results]
        assert operations.count("delete") == 1
        assert operations.count("signup") == 1

        status_by_operation = dict(results)
        delete_status = status_by_operation["delete"]
        signup_status = status_by_operation["signup"]

        # Allowed outcomes depend on thread ordering:
        # - delete always succeeds (200) since participant was pre-added and no other delete runs
        # - signup runs concurrently: finds participant still present (400) or finds it deleted (200)
        assert delete_status == 200
        assert signup_status in (200, 400)

        response = client.get("/activities")
        activities = response.json()
        participants = activities[activity_name]["participants"]
        participant_present = email in participants

        # Verify final state matches one of the two possible orderings:
        # - delete ran first, then signup added participant back: signup 200, participant present
        # - signup attempted while participant existed (400), then delete removed: participant absent
        assert (
            (signup_status == 200 and participant_present) or
            (signup_status == 400 and not participant_present)
        )
