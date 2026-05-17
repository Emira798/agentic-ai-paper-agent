"""
Unit tests for the planning agent module (src/planning_agent.py)
Tests planner_agent and executor_agent_step functions
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from typing import List
from src.planning_agent import planner_agent, executor_agent_step


class TestPlannerAgent:
    """Test cases for the planner_agent function"""

    @patch('src.planning_agent.client.chat.completions.create')
    def test_planner_agent_returns_list(self, mock_create):
        """Test that planner_agent returns a list of steps"""
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            "Research agent: Use Tavily to perform a broad web search",
            "Research agent: For each collected item, search on arXiv",
            "Writer agent: Generate the final comprehensive Markdown report"
        ])
        mock_create.return_value = mock_response

        # Call the function
        result = planner_agent("test topic")

        # Assertions
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(step, str) for step in result)

    @patch('src.planning_agent.client.chat.completions.create')
    def test_planner_agent_enforces_contract(self, mock_create):
        """Test that planner_agent enforces required first and second steps"""
        # Mock response that doesn't follow the required format
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            "Some random step",
            "Another random step"
        ])
        mock_create.return_value = mock_response

        result = planner_agent("test topic")

        # Should enforce required first and second steps
        assert result[0] == "Research agent: Use Tavily to perform a broad web search and collect top relevant items (title, authors, year, venue/source, URL, DOI if available)."
        assert result[1] == "Research agent: For each collected item, search on arXiv to find matching preprints/versions and record arXiv URLs (if they exist)."

    @patch('src.planning_agent.client.chat.completions.create')
    def test_planner_agent_handles_malformed_json(self, mock_create):
        """Test planner_agent handles malformed JSON responses"""
        # Mock response with malformed JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Not valid JSON at all"
        mock_create.return_value = mock_response

        result = planner_agent("test topic")

        # Should return default steps when JSON parsing fails
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0] == "Research agent: Use Tavily to perform a broad web search and collect top relevant items (title, authors, year, venue/source, URL, DOI if available)."

    @patch('src.planning_agent.client.chat.completions.create')
    def test_planner_agent_limits_to_seven_steps(self, mock_create):
        """Test that planner_agent limits output to maximum 7 steps"""
        # Mock response with more than 7 steps
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            "Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6", "Step 7", "Step 8", "Step 9"
        ])
        mock_create.return_value = mock_response

        result = planner_agent("test topic")

        # Should be limited to 7 steps
        assert len(result) <= 7

    @patch('src.planning_agent.client.chat.completions.create')
    def test_planner_agent_includes_final_step(self, mock_create):
        """Test that planner_agent includes required final step"""
        # Mock response without final step
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            "Research agent: Use Tavily to perform a broad web search",
            "Research agent: For each collected item, search on arXiv"
        ])
        mock_create.return_value = mock_response

        result = planner_agent("test topic")

        # Should include final step
        final_step = "Writer agent: Generate the final comprehensive Markdown report with inline citations and a complete References section with clickable links."
        assert final_step in result


class TestExecutorAgentStep:
    """Test cases for the executor_agent_step function"""

    @patch('src.planning_agent.research_agent')
    def test_executor_agent_step_research(self, mock_research):
        """Test executor_agent_step with research step"""
        # Mock research agent response
        mock_research.return_value = ("Research output", [])

        step_title = "Research agent: Use Tavily to search for information"
        history = []
        prompt = "Test prompt"

        result = executor_agent_step(step_title, history, prompt)

        # Should return tuple with step details
        assert len(result) == 3
        assert result[0] == step_title
        assert result[1] == "research_agent"
        assert result[2] == "Research output"
        assert mock_research.called

    @patch('src.planning_agent.writer_agent')
    def test_executor_agent_step_writer(self, mock_writer):
        """Test executor_agent_step with writer step"""
        # Mock writer agent response
        mock_writer.return_value = ("Written output", [])

        step_title = "Writer agent: Draft a report"
        history = []
        prompt = "Test prompt"

        result = executor_agent_step(step_title, history, prompt)

        # Should return tuple with step details
        assert len(result) == 3
        assert result[0] == step_title
        assert result[1] == "writer_agent"
        assert result[2] == "Written output"
        assert mock_writer.called

    @patch('src.planning_agent.editor_agent')
    def test_executor_agent_step_editor(self, mock_editor):
        """Test executor_agent_step with editor step"""
        # Mock editor agent response
        mock_editor.return_value = ("Edited output", [])

        step_title = "Editor agent: Review and improve the draft"
        history = []
        prompt = "Test prompt"

        result = executor_agent_step(step_title, history, prompt)

        # Should return tuple with step details
        assert len(result) == 3
        assert result[0] == step_title
        assert result[1] == "editor_agent"
        assert result[2] == "Edited output"
        assert mock_editor.called

    def test_executor_agent_step_with_history(self,):
        """Test executor_agent_step with execution history"""
        with patch('src.planning_agent.research_agent') as mock_research:
            mock_research.return_value = ("Research output with history", [])

            step_title = "Research agent: Use Tavily to search"
            history = [
                ("Previous step", "writer_agent", "Previous output")
            ]
            prompt = "Test prompt"

            result = executor_agent_step(step_title, history, prompt)

            # Verify that history is included in the enriched task
            assert mock_research.called
            call_args = mock_research.call_args
            enriched_prompt = call_args[1]['prompt']
            assert "Previous step" in enriched_prompt
            assert "Previous output" in enriched_prompt

    def test_executor_agent_step_unknown_type(self):
        """Test executor_agent_step with unknown step type"""
        step_title = "Unknown agent: Do something"
        history = []
        prompt = "Test prompt"

        with pytest.raises(ValueError) as exc_info:
            executor_agent_step(step_title, history, prompt)

        assert "Unknown step type" in str(exc_info.value)

    @patch('src.planning_agent.research_agent')
    def test_executor_agent_step_enriches_context(self, mock_research):
        """Test that executor_agent_step properly enriches context with history"""
        mock_research.return_value = ("Research output", [])

        step_title = "Research agent: Use Tavily to search"
        history = [
            ("Research step", "research_agent", "Research findings"),
            ("Draft step", "writer_agent", "Draft content"),
            ("Edit step", "editor_agent", "Edit feedback")
        ]
        prompt = "Original user prompt"

        executor_agent_step(step_title, history, prompt)

        # Verify the enriched context includes all history items
        call_args = mock_research.call_args
        enriched_prompt = call_args[1]['prompt']

        assert "Original user prompt" in enriched_prompt
        assert "Research findings" in enriched_prompt
        assert "Draft content" in enriched_prompt
        assert "Edit feedback" in enriched_prompt


class TestPlanningIntegration:
    """Integration tests for planning and execution workflow"""

    @patch('src.planning_agent.client.chat.completions.create')
    @patch('src.planning_agent.research_agent')
    @patch('src.planning_agent.writer_agent')
    def test_full_planning_and_execution_workflow(self, mock_writer, mock_research, mock_create):
        """Test complete workflow from planning to execution"""
        # Mock planner response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            "Research agent: Use Tavily to perform a broad web search and collect top relevant items (title, authors, year, venue/source, URL, DOI if available).",
            "Research agent: For each collected item, search on arXiv to find matching preprints/versions and record arXiv URLs (if they exist).",
            "Writer agent: Generate the final comprehensive Markdown report with inline citations and a complete References section with clickable links."
        ])
        mock_create.return_value = mock_response

        # Mock agent responses
        mock_research.return_value = ("Research findings", [])
        mock_writer.return_value = ("Final report", [])

        # Execute planning
        topic = "Artificial Intelligence in Healthcare"
        plan_steps = planner_agent(topic)

        # Execute first step
        history = []
        step_result1 = executor_agent_step(plan_steps[0], history, topic)
        history.append(step_result1)

        # Execute final step
        step_result2 = executor_agent_step(plan_steps[-1], history, topic)

        # Assertions
        assert len(plan_steps) == 3
        assert step_result1[1] == "research_agent"
        assert step_result2[1] == "writer_agent"
        assert mock_research.call_count == 2  # Called for both research steps
        assert mock_writer.call_count == 1