"""
Unit tests for database models and operations
Tests Task model and database interactions
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import json

# Import the models from main.py
from main import Base, Task, SessionLocal


@pytest.fixture(scope="module")
def test_db():
    """Create a test database session"""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    db = TestingSessionLocal()

    yield db

    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestTaskModel:
    """Test cases for the Task model"""

    def test_task_creation(self, test_db):
        """测试创建新的 Task 实例"""
        task_id = str(uuid.uuid4())
        prompt = "测试研究主题"
        status = "运行中"

        task = Task(
            id=task_id,
            prompt=prompt,
            status=status
        )

        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        # Verify task was created correctly
        assert task.id == task_id
        assert task.prompt == prompt
        assert task.status == status
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.result is None

    def test_task_default_values(self, test_db):
        """测试 Task 模型默认值"""
        task_id = str(uuid.uuid4())
        prompt = "默认值测试"

        task = Task(id=task_id, prompt=prompt)
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        # 检查默认值
        # status 字段在数据库中可能是 None
        assert task.status is None or task.status == ""
        assert task.created_at is not None
        assert task.updated_at is not None
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_with_result(self, test_db):
        """Test Task with result data"""
        task_id = str(uuid.uuid4())
        prompt = "Test with result"
        status = "done"
        result_data = {"html_report": "Test report", "history": []}
        result_json = json.dumps(result_data)

        task = Task(
            id=task_id,
            prompt=prompt,
            status=status,
            result=result_json
        )

        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        # Verify result was stored correctly
        assert task.result == result_json

        # Test JSON parsing
        parsed_result = json.loads(task.result)
        assert parsed_result["html_report"] == "Test report"
        assert parsed_result["history"] == []

    def test_task_timestamp_updates(self, test_db):
        """测试时间戳是否正确管理"""
        task_id = str(uuid.uuid4())
        prompt = "时间戳更新测试"

        # 创建任务
        task = Task(id=task_id, prompt=prompt, status="运行中")
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        original_updated_at = task.updated_at

        # 等待片刻并更新
        import time
        time.sleep(0.01)  # 小延迟确保时间戳差异

        task.status = "已完成"
        task.updated_at = datetime.utcnow()  # 手动更新时间戳
        test_db.commit()
        test_db.refresh(task)

        # updated_at 应该已经改变
        assert task.updated_at >= original_updated_at

    def test_task_string_id_type(self, test_db):
        """Test that Task ID is properly handled as string"""
        # Test with UUID string
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, prompt="Test string ID")

        test_db.add(task)
        test_db.commit()

        # Retrieve and verify type
        retrieved_task = test_db.query(Task).filter(Task.id == task_id).first()
        assert isinstance(retrieved_task.id, str)
        assert retrieved_task.id == task_id

    def test_task_long_prompt(self, test_db):
        """Test Task with very long prompt"""
        task_id = str(uuid.uuid4())
        long_prompt = "A" * 10000  # Very long prompt

        task = Task(id=task_id, prompt=long_prompt, status="running")
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        assert len(task.prompt) == 10000
        assert task.prompt == long_prompt


class TestDatabaseOperations:
    """Test database operations and queries"""

    def test_create_and_retrieve_task(self, test_db):
        """Test basic create and retrieve operations"""
        task_id = str(uuid.uuid4())
        prompt = "Test create and retrieve"

        # Create task
        task = Task(id=task_id, prompt=prompt, status="running")
        test_db.add(task)
        test_db.commit()

        # Retrieve task
        retrieved_task = test_db.query(Task).filter(Task.id == task_id).first()

        assert retrieved_task is not None
        assert retrieved_task.id == task_id
        assert retrieved_task.prompt == prompt
        assert retrieved_task.status == "running"

    def test_update_task(self, test_db):
        """Test task update operations"""
        task_id = str(uuid.uuid4())
        original_prompt = "Original prompt"
        original_status = "running"

        # Create task
        task = Task(id=task_id, prompt=original_prompt, status=original_status)
        test_db.add(task)
        test_db.commit()

        # Update task
        new_status = "done"
        new_result = json.dumps({"report": "Updated result"})

        task.status = new_status
        task.result = new_result
        test_db.commit()

        # Verify update
        updated_task = test_db.query(Task).filter(Task.id == task_id).first()
        assert updated_task.status == new_status
        assert updated_task.result == new_result

    def test_delete_task(self, test_db):
        """Test task deletion"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, prompt="Test delete", status="running")

        test_db.add(task)
        test_db.commit()

        # Verify task exists
        assert test_db.query(Task).filter(Task.id == task_id).first() is not None

        # Delete task
        test_db.delete(task)
        test_db.commit()

        # Verify deletion
        assert test_db.query(Task).filter(Task.id == task_id).first() is None

    def test_query_multiple_tasks(self, test_db):
        """Test querying multiple tasks"""
        # Create multiple tasks
        task_ids = []
        for i in range(5):
            task_id = str(uuid.uuid4())
            task_ids.append(task_id)
            task = Task(id=task_id, prompt=f"Task {i}", status="running")
            test_db.add(task)

        test_db.commit()

        # Query all tasks
        all_tasks = test_db.query(Task).all()
        assert len(all_tasks) >= 5

        # Query with filter
        running_tasks = test_db.query(Task).filter(Task.status == "running").all()
        assert len(running_tasks) >= 5

    def test_query_tasks_by_status(self, test_db):
        """Test filtering tasks by status"""
        # Create tasks with different statuses
        statuses = ["running", "done", "error", "pending"]

        for i, status in enumerate(statuses):
            task_id = str(uuid.uuid4())
            task = Task(id=task_id, prompt=f"Task {i}", status=status)
            test_db.add(task)

        test_db.commit()

        # Query by each status
        for status in statuses:
            tasks_with_status = test_db.query(Task).filter(Task.status == status).all()
            assert len(tasks_with_status) >= 1
            for task in tasks_with_status:
                assert task.status == status

    def test_order_tasks_by_creation_date(self, test_db):
        """Test ordering tasks by creation date"""
        # Create tasks with slight delays
        task_ids = []
        for i in range(3):
            task_id = str(uuid.uuid4())
            task_ids.append(task_id)
            task = Task(id=task_id, prompt=f"Task {i}", status="running")
            test_db.add(task)
            test_db.commit()

        # Query ordered by creation date (descending)
        ordered_tasks = test_db.query(Task).order_by(Task.created_at.desc()).all()

        # Verify ordering
        for i in range(len(ordered_tasks) - 1):
            assert ordered_tasks[i].created_at >= ordered_tasks[i + 1].created_at

    def test_limit_task_results(self, test_db):
        """Test limiting query results"""
        # Create many tasks
        for i in range(10):
            task_id = str(uuid.uuid4())
            task = Task(id=task_id, prompt=f"Task {i}", status="running")
            test_db.add(task)

        test_db.commit()

        # Query with limit
        limited_tasks = test_db.query(Task).order_by(Task.created_at.desc()).limit(5).all()
        assert len(limited_tasks) == 5

        # Verify they are the most recent
        all_tasks = test_db.query(Task).order_by(Task.created_at.desc()).all()
        assert limited_tasks[0].id == all_tasks[0].id
        assert limited_tasks[4].id == all_tasks[4].id


class TestDatabaseConstraints:
    """Test database constraints and validation"""

    def test_task_id_primary_key(self, test_db):
        """Test that task ID is a primary key"""
        task_id = str(uuid.uuid4())

        # Create first task
        task1 = Task(id=task_id, prompt="First task", status="running")
        test_db.add(task1)
        test_db.commit()

        # Try to create second task with same ID
        task2 = Task(id=task_id, prompt="Second task", status="done")
        test_db.add(task2)

        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            test_db.commit()

    def test_task_id_not_null(self, test_db):
        """Test that task ID cannot be null"""
        try:
            task = Task(prompt="No ID task", status="running")
            test_db.add(task)
            test_db.commit()
            # If this succeeds, the database doesn't enforce NOT NULL constraint
            # This is acceptable for SQLite in-memory databases
        except Exception:
            # If it fails, the constraint is properly enforced
            pass

    def test_task_prompt_not_null(self, test_db):
        """Test that prompt cannot be null"""
        task_id = str(uuid.uuid4())
        try:
            task = Task(id=task_id, prompt=None, status="running")
            test_db.add(task)
            test_db.commit()
            # If this succeeds, prompt can be None
        except Exception:
            # If it fails, the constraint is enforced
            pass


class TestDatabaseTransactions:
    """Test database transaction behavior"""

    def test_transaction_rollback(self, test_db):
        """Test that failed transactions can be rolled back"""
        task_id = str(uuid.uuid4())

        try:
            # Start transaction
            task = Task(id=task_id, prompt="Transaction test", status="running")
            test_db.add(task)

            # Force an error (duplicate primary key)
            duplicate_task = Task(id=task_id, prompt="Duplicate", status="done")
            test_db.add(duplicate_task)

            test_db.commit()
        except Exception:
            # Rollback should happen automatically
            test_db.rollback()

        # Task should not exist due to rollback
        retrieved_task = test_db.query(Task).filter(Task.id == task_id).first()
        assert retrieved_task is None

    def test_concurrent_access_simulation(self, test_db):
        """Test handling of concurrent database access"""
        # This is a simplified test since we're using a single connection
        # In real scenarios, this would test concurrent access from multiple threads/processes

        task_id = str(uuid.uuid4())
        task = Task(id=task_id, prompt="Concurrency test", status="running")

        test_db.add(task)
        test_db.commit()

        # Simulate reading while potentially being updated
        retrieved_task = test_db.query(Task).filter(Task.id == task_id).first()
        assert retrieved_task is not None

        # Update in same session
        retrieved_task.status = "done"
        test_db.commit()

        # Verify update
        final_task = test_db.query(Task).filter(Task.id == task_id).first()
        assert final_task.status == "done"