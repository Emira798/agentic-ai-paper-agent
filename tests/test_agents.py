"""
Unit tests for the agents module (src/agents.py)
Tests research_agent, writer_agent, and editor_agent functions
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.agents import research_agent, writer_agent, editor_agent


class TestResearchAgent:
    """Test cases for the research_agent function"""

    @patch('src.agents.client.chat.completions.create')
    def test_research_agent_basic_functionality(self, mock_create):
        """Test that research_agent returns expected output structure"""
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Test research content"
        mock_response.choices[0].message.tool_calls = None
        mock_create.return_value = mock_response

        # Call the function
        result, messages = research_agent("test prompt")

        # Assertions
        assert isinstance(result, str)
        assert isinstance(messages, list)
        assert len(messages) > 0

    @patch('src.agents.client.chat.completions.create')
    def test_research_agent_with_tool_calls(self, mock_create):
        """Test research_agent when tool calls are made"""
        # Mock tool call response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "I need to search for information"
        mock_response.choices[0].message.tool_calls = [
            MagicMock(
                id="call_1",
                function=MagicMock(
                    name="tavily_search_tool",
                    arguments=json.dumps({"query": "test query", "max_results": 5})
                )
            )
        ]

        # Mock the second response (after tool execution)
        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message = MagicMock()
        mock_response2.choices[0].message.content = "Here are the research results"
        mock_response2.choices[0].message.tool_calls = None

        mock_create.side_effect = [mock_response, mock_response2]

        with patch('src.agents.tavily_search_tool') as mock_tool:
            mock_tool.return_value = [{"title": "Test", "content": "Test content", "url": "http://test.com"}]

            result, messages = research_agent("test prompt")

            # Assertions
            assert "Here are the research results" in result
            assert mock_tool.called

    def test_research_agent_error_handling(self):
        """Test research_agent error handling"""
        with patch('src.agents.client.chat.completions.create') as mock_create:
            mock_create.side_effect = Exception("API Error")

            result, messages = research_agent("test prompt")

            # Should return error message
            assert "[Model Error:" in result
            assert isinstance(messages, list)


class TestWriterAgent:
    """Test cases for the writer_agent function"""

    @patch('src.agents.client.chat.completions.create')
    def test_writer_agent_basic_functionality(self, mock_create):
        """Test that writer_agent returns expected output"""
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "# Test Report\n\nThis is a test report."
        mock_create.return_value = mock_response

        # Call the function
        result, messages = writer_agent("test prompt")

        # Assertions
        assert isinstance(result, str)
        assert "# Test Report" in result
        assert isinstance(messages, list)
        assert len(messages) >= 2  # system + user message

    @patch('src.agents.client.chat.completions.create')
    def test_writer_agent_word_count(self, mock_create):
        """Test writer_agent with minimum word count requirements"""
        # Mock response with sufficient content
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        # Create a longer response to meet word count
        long_content = " ".join([f"word{i}" for i in range(500)])  # 500 words
        mock_response.choices[0].message.content = f"# Report\n\n{long_content}"
        mock_create.return_value = mock_response

        result, messages = writer_agent("test prompt", min_words_total=200)

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0


class TestEditorAgent:
    """Test cases for the editor_agent function"""

    @patch('src.agents.client.chat.completions.create')
    def test_editor_agent_basic_functionality(self, mock_create):
        """Test that editor_agent returns expected output"""
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "# Edited Report\n\nThis is an edited version."
        mock_create.return_value = mock_response

        # Call the function
        result, messages = editor_agent("test prompt")

        # Assertions
        assert isinstance(result, str)
        assert "# Edited Report" in result
        assert isinstance(messages, list)
        assert len(messages) >= 2  # system + user message

    @patch('src.agents.client.chat.completions.create')
    def test_editor_agent_preserves_structure(self, mock_create):
        """Test that editor_agent preserves markdown structure"""
        # Mock response with markdown formatting
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = (
            "# Main Title\n\n"
            "## Section 1\n\n"
            "Some content with **bold** and *italic* text.\n\n"
            "## Section 2\n\n"
            "More content here."
        )
        mock_create.return_value = mock_response

        result, messages = editor_agent("test prompt")

        # Assertions
        assert "# Main Title" in result
        assert "## Section" in result
        assert "**bold**" in result
        assert "*italic*" in result


class TestAgentIntegration:
    """Integration tests for agent workflow"""

    @patch('src.agents.client.chat.completions.create')
    def test_research_to_writer_workflow(self, mock_create):
        """Test workflow from research to writing"""
        # Mock research response
        research_response = MagicMock()
        research_response.choices = [MagicMock()]
        research_response.choices[0].message = MagicMock()
        research_response.choices[0].message.content = "Research findings: Test data"
        research_response.choices[0].message.tool_calls = None

        # Mock writer response
        writer_response = MagicMock()
        writer_response.choices = [MagicMock()]
        writer_response.choices[0].message = MagicMock()
        writer_response.choices[0].message.content = "# Report based on research\n\nContent here."

        mock_create.side_effect = [research_response, writer_response]

        # Execute research agent
        research_result, _ = research_agent("research prompt")

        # Execute writer agent with research results
        writer_prompt = f"Based on this research: {research_result}\n\nWrite a comprehensive report."
        writer_result, _ = writer_agent(writer_prompt)

        # Assertions
        assert "Research findings" in research_result
        assert "# Report based on research" in writer_result

    def test_agent_error_propagation(self):
        """Test that errors are properly handled and don't crash the system"""
        with patch('src.agents.client.chat.completions.create') as mock_create:
            mock_create.side_effect = Exception("Network error")

            # All agents should handle errors gracefully
            research_result, _ = research_agent("prompt")
            writer_result, _ = writer_agent("prompt")
            editor_result, _ = editor_agent("prompt")

            # All should return error messages, not crash
            assert "[Model Error:" in research_result
            assert "[Model Error:" in writer_result
            assert isinstance(editor_result, str)  # editor doesn't have explicit error handling but should still work