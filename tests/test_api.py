"""
Unit tests for the FastAPI endpoints in main.py
Tests all API endpoints and their functionality
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI app"""
    # Override the database URL for testing
    with patch.dict(os.environ, {"DATABASE_URL": TEST_DATABASE_URL}):
        # Create test database
        from main import Base, SessionLocal

        # Create engine for testing
        test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

        # Create tables
        Base.metadata.create_all(bind=test_engine)

        # Override the database session
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        # Create test client
        client = TestClient(app)

        # Override dependencies
        app.dependency_overrides[SessionLocal] = override_get_db

        yield client

        # Cleanup
        Base.metadata.drop_all(bind=test_engine)


class TestAPIEndpoints:
    """Test cases for all API endpoints"""

    def test_health_check_endpoint(self, test_client):
        """Test the health check endpoint"""
        response = test_client.get("/api")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_index_endpoint(self, test_client):
        """Test the index endpoint returns HTML"""
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"

    def test_generate_report_endpoint_success(self, test_client):
        """Test successful report generation"""
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = [
                "Research agent: Use Tavily to perform a broad web search",
                "Writer agent: Generate the final comprehensive Markdown report"
            ]

            payload = {
                "prompt": "Test research topic",
                "model": "qwen-turbo"
            }

            response = test_client.post("/generate_report", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert isinstance(data["task_id"], str)

            # Verify task was created in database
            task_id = data["task_id"]
            status_response = test_client.get(f"/task_status/{task_id}")
            assert status_response.status_code == 200
            assert status_response.json()["status"] == "running"

    def test_generate_report_endpoint_missing_prompt(self, test_client):
        """Test report generation with missing prompt"""
        payload = {"model": "qwen-turbo"}  # Missing prompt

        response = test_client.post("/generate_report", json=payload)

        assert response.status_code == 422  # Validation error

    def test_task_progress_endpoint(self, test_client):
        """Test task progress endpoint"""
        # First create a task
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1", "Step 2"]

            payload = {"prompt": "Test topic", "model": "qwen-turbo"}
            create_response = test_client.post("/generate_report", json=payload)
            task_id = create_response.json()["task_id"]

        # Get progress
        response = test_client.get(f"/task_progress/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert len(data["steps"]) == 2

    def test_task_progress_endpoint_nonexistent_task(self, test_client):
        """Test task progress for nonexistent task"""
        response = test_client.get("/task_progress/nonexistent-task-id")

        assert response.status_code == 200
        assert response.json()["steps"] == []

    def test_task_status_endpoint(self, test_client):
        """Test task status endpoint"""
        # Create a task first
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            payload = {"prompt": "Test topic", "model": "qwen-turbo"}
            create_response = test_client.post("/generate_report", json=payload)
            task_id = create_response.json()["task_id"]

        # Get status
        response = test_client.get(f"/task_status/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"

    def test_task_status_endpoint_nonexistent_task(self, test_client):
        """Test task status for nonexistent task"""
        response = test_client.get("/task_status/nonexistent-task-id")

        assert response.status_code == 404

    def test_list_tasks_endpoint(self, test_client):
        """Test list tasks endpoint"""
        # Create a few tasks first
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            for i in range(3):
                payload = {"prompt": f"Test topic {i}", "model": "qwen-turbo"}
                test_client.post("/generate_report", json=payload)

        # List tasks
        response = test_client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

        # Check task structure
        for task in data:
            assert "id" in task
            assert "prompt" in task
            assert "status" in task
            assert "created_at" in task

    def test_get_task_endpoint(self, test_client):
        """Test get specific task endpoint"""
        # Create a task first
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            payload = {"prompt": "Test topic for get", "model": "qwen-turbo"}
            create_response = test_client.post("/generate_report", json=payload)
            task_id = create_response.json()["task_id"]

        # Get task details
        response = test_client.get(f"/task/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["prompt"] == "Test topic for get"
        assert "status" in data
        assert "created_at" in data

    def test_get_task_endpoint_nonexistent_task(self, test_client):
        """Test get task for nonexistent task"""
        response = test_client.get("/task/nonexistent-task-id")

        assert response.status_code == 404


class TestTaskWorkflow:
    """Test the complete task workflow"""

    def test_complete_task_workflow(self, test_client):
        """Test complete workflow from creation to completion"""
        # Mock all the agent functions
        with patch('main.planner_agent') as mock_planner, \
             patch('main.executor_agent_step') as mock_executor:

            # Setup mocks
            mock_planner.return_value = [
                "Research agent: Use Tavily to search",
                "Writer agent: Generate report"
            ]

            # Mock executor to return successful completion
            mock_executor.side_effect = [
                ("Research step", "research_agent", "Research findings"),
                ("Writer step", "writer_agent", "Final report content")
            ]

            # Create task
            payload = {"prompt": "Complete workflow test", "model": "qwen-turbo"}
            create_response = test_client.post("/generate_report", json=payload)

            assert create_response.status_code == 200
            task_id = create_response.json()["task_id"]

            # Check initial status
            status_response = test_client.get(f"/task_status/{task_id}")
            assert status_response.json()["status"] == "running"

            # Check progress
            progress_response = test_client.get(f"/task_progress/{task_id}")
            assert len(progress_response.json()["steps"]) == 2


class TestErrorHandling:
    """Test error handling in API endpoints"""

    def test_generate_report_with_planner_error(self, test_client):
        """Test report generation when planner fails"""
        with patch('main.planner_agent') as mock_planner:
            mock_planner.side_effect = Exception("Planner error")

            payload = {"prompt": "Test topic", "model": "qwen-turbo"}
            response = test_client.post("/generate_report", json=payload)

            # Should still create task but may have issues during execution
            assert response.status_code == 200  # Task creation succeeds

            task_id = response.json()["task_id"]

            # Task should eventually show error status
            # (This would happen in the background thread)
            status_response = test_client.get(f"/task_status/{task_id}")
            # Status might still be "running" since error happens in background
            assert status_response.status_code == 200

    def test_invalid_json_payload(self, test_client):
        """Test handling of invalid JSON payload"""
        response = test_client.post("/generate_report", data="invalid json")

        assert response.status_code == 422  # Unprocessable Entity

    def test_cors_headers(self, test_client):
        """Test CORS headers are properly set"""
        response = test_client.get("/api")

        # Should have CORS headers since we added CORSMiddleware
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"


class TestDataValidation:
    """Test data validation in API endpoints"""

    def test_prompt_request_validation(self, test_client):
        """Test PromptRequest model validation"""
        # Test with empty prompt
        payload = {"prompt": "", "model": "qwen-turbo"}
        response = test_client.post("/generate_report", json=payload)

        # Should still accept empty prompt (FastAPI doesn't validate content, just type)
        assert response.status_code == 200

    def test_model_parameter_validation(self, test_client):
        """Test model parameter handling"""
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            # Test with custom model
            payload = {"prompt": "Test", "model": "custom-model"}
            response = test_client.post("/generate_report", json=payload)

            assert response.status_code == 200

            # Verify the custom model was passed
            call_args = mock_planner.call_args
            assert call_args[1]['model'] == "custom-model"

    def test_default_model_parameter(self, test_client):
        """Test default model parameter"""
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            # Test without specifying model
            payload = {"prompt": "Test"}
            response = test_client.post("/generate_report", json=payload)

            assert response.status_code == 200

            # Should use default model
            call_args = mock_planner.call_args
            assert call_args[1]['model'] == "qwen-turbo"


class TestDatabaseOperations:
    """Test database operations through API"""

    def test_task_persistence(self, test_client):
        """Test that tasks are properly persisted in database"""
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            # Create task
            payload = {"prompt": "Persistence test", "model": "qwen-turbo"}
            create_response = test_client.post("/generate_report", json=payload)
            task_id = create_response.json()["task_id"]

            # Get task from database
            get_response = test_client.get(f"/task/{task_id}")
            task_data = get_response.json()

            assert task_data["prompt"] == "Persistence test"
            assert task_data["status"] == "running"
            assert "created_at" in task_data

    def test_multiple_tasks_isolation(self, test_client):
        """Test that multiple tasks don't interfere with each other"""
        task_ids = []

        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            # Create multiple tasks
            for i in range(3):
                payload = {"prompt": f"Task {i}", "model": "qwen-turbo"}
                response = test_client.post("/generate_report", json=payload)
                task_ids.append(response.json()["task_id"])

        # Verify each task is independent
        for i, task_id in enumerate(task_ids):
            response = test_client.get(f"/task/{task_id}")
            task_data = response.json()
            assert task_data["prompt"] == f"Task {i}"

    def test_task_listing_limit(self, test_client):
        """Test that task listing respects the limit"""
        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            # Create many tasks
            for i in range(60):  # More than the 50 limit
                payload = {"prompt": f"Task {i}", "model": "qwen-turbo"}
                test_client.post("/generate_report", json=payload)

        # Get task list
        response = test_client.get("/tasks")
        tasks = response.json()

        # Should be limited to 50
        assert len(tasks) <= 50

    def test_task_ordering(self, test_client):
        """Test that tasks are ordered by creation date (descending)"""
        task_ids = []

        with patch('main.planner_agent') as mock_planner:
            mock_planner.return_value = ["Step 1"]

            # Create tasks with slight delay
            for i in range(3):
                payload = {"prompt": f"Task {i}", "model": "qwen-turbo"}
                response = test_client.post("/generate_report", json=payload)
                task_ids.append(response.json()["task_id"])

        # Get task list
        response = test_client.get("/tasks")
        tasks = response.json()

        # Most recent tasks should appear first
        recent_tasks = [task for task in tasks if task["id"] in task_ids]
        assert len(recent_tasks) == 3

        # Check ordering (most recent first)
        for i in range(len(recent_tasks) - 1):
            current_time = recent_tasks[i]["created_at"]
            next_time = recent_tasks[i + 1]["created_at"]
            assert current_time >= next_time  # Should be descending order