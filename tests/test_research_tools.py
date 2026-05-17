"""
Unit tests for the research tools module (src/research_tools.py)
Tests arxiv_search_tool, tavily_search_tool, and wikipedia_search_tool
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from typing import List, Dict
from src.research_tools import (
    arxiv_search_tool, tavily_search_tool, wikipedia_search_tool,
    arxiv_tool_def, tavily_tool_def, wikipedia_tool_def
)


class TestArxivSearchTool:
    """Test cases for the arxiv_search_tool function"""

    @patch('src.research_tools.session.get')
    def test_arxiv_search_tool_basic_functionality(self, mock_get):
        """Test basic arXiv search functionality"""
        # Mock arXiv API response with XML
        mock_response = MagicMock()
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Paper Title</title>
                <summary>Test abstract summary</summary>
                <published>2023-01-01T00:00:00Z</published>
                <id>http://arxiv.org/abs/2301.00001</id>
                <author>
                    <name>John Doe</name>
                </author>
                <link href="http://arxiv.org/pdf/2301.00001.pdf" title="pdf"/>
            </entry>
        </feed>'''
        mock_get.return_value = mock_response

        # Call the function
        result = arxiv_search_tool("test query", max_results=1)

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Test Paper Title"
        assert result[0]["summary"] == "Test abstract summary"
        assert result[0]["authors"] == ["John Doe"]
        assert result[0]["published"] == "2023-01-01"
        assert result[0]["url"] == "http://arxiv.org/abs/2301.00001"
        assert result[0]["link_pdf"] == "http://arxiv.org/pdf/2301.00001.pdf"

    @patch('src.research_tools.session.get')
    def test_arxiv_search_tool_no_pdf_link(self, mock_get):
        """Test arXiv search when no PDF link is provided"""
        # Mock arXiv API response without explicit PDF link
        mock_response = MagicMock()
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Paper Title</title>
                <summary>Test abstract summary</summary>
                <published>2023-01-01T00:00:00Z</published>
                <id>http://arxiv.org/abs/2301.00001</id>
                <author>
                    <name>John Doe</name>
                </author>
            </entry>
        </feed>'''
        mock_get.return_value = mock_response

        result = arxiv_search_tool("test query", max_results=1)

        # Should generate PDF URL from abstract URL
        assert result[0]["link_pdf"] == "http://arxiv.org/pdf/2301.00001.pdf"

    @patch('src.research_tools.session.get')
    def test_arxiv_search_tool_multiple_authors(self, mock_get):
        """Test arXiv search with multiple authors"""
        # Mock arXiv API response with multiple authors
        mock_response = MagicMock()
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Paper Title</title>
                <summary>Test abstract summary</summary>
                <published>2023-01-01T00:00:00Z</published>
                <id>http://arxiv.org/abs/2301.00001</id>
                <author><name>John Doe</name></author>
                <author><name>Jane Smith</name></author>
                <author><name>Bob Johnson</name></author>
            </entry>
        </feed>'''
        mock_get.return_value = mock_response

        result = arxiv_search_tool("test query", max_results=1)

        assert result[0]["authors"] == ["John Doe", "Jane Smith", "Bob Johnson"]

    @patch('src.research_tools.session.get')
    def test_arxiv_search_tool_api_error(self, mock_get):
        """Test arXiv search error handling"""
        mock_get.side_effect = Exception("API Error")

        result = arxiv_search_tool("test query")

        assert len(result) == 1
        assert "error" in result[0]
        assert "API request failed" in result[0]["error"]

    @patch('src.research_tools.session.get')
    def test_arxiv_search_tool_xml_parse_error(self, mock_get):
        """Test arXiv search XML parsing error handling"""
        # Mock invalid XML response
        mock_response = MagicMock()
        mock_response.content = "Invalid XML content"
        mock_get.return_value = mock_response

        result = arxiv_search_tool("test query")

        assert len(result) == 1
        assert "error" in result[0]
        assert "XML parse failed" in result[0]["error"]

    def test_arxiv_search_tool_url_generation(self):
        """Test arXiv URL generation logic"""
        # Test ensure_pdf_url function indirectly through the tool
        with patch('src.research_tools.session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry>
                    <title>Test</title>
                    <summary>Test</summary>
                    <published>2023-01-01T00:00:00Z</published>
                    <id>http://arxiv.org/abs/2301.00001</id>
                </entry>
            </feed>'''
            mock_get.return_value = mock_response

            result = arxiv_search_tool("test")

            # Should convert /abs/ to /pdf/ and add .pdf extension
            assert result[0]["link_pdf"] == "http://arxiv.org/pdf/2301.00001.pdf"


class TestTavilySearchTool:
    """Test cases for the tavily_search_tool function"""

    @patch('src.research_tools.TavilyClient')
    def test_tavily_search_tool_basic_functionality(self, mock_client_class):
        """Test basic Tavily search functionality"""
        # Mock Tavily client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock search response
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Test Result",
                    "content": "Test content",
                    "url": "https://example.com"
                }
            ]
        }

        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            result = tavily_search_tool("test query", max_results=1)

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Test Result"
        assert result[0]["content"] == "Test content"
        assert result[0]["url"] == "https://example.com"
        assert mock_client.search.called

    @patch('src.research_tools.TavilyClient')
    def test_tavily_search_tool_with_images(self, mock_client_class):
        """Test Tavily search with images enabled"""
        # Mock Tavily client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock search response with images
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Test Result",
                    "content": "Test content",
                    "url": "https://example.com"
                }
            ],
            "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
        }

        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            result = tavily_search_tool("test query", include_images=True)

        # Should include both regular results and images
        assert len(result) == 3  # 1 regular result + 2 images
        assert result[1]["image_url"] == "https://example.com/image1.jpg"
        assert result[2]["image_url"] == "https://example.com/image2.jpg"

    def test_tavily_search_tool_missing_api_key(self):
        """Test Tavily search with missing API key"""
        with patch.dict('os.environ', {'TAVILY_API_KEY': ''}):
            with pytest.raises(ValueError) as exc_info:
                tavily_search_tool("test query")

        assert "TAVILY_API_KEY not found" in str(exc_info.value)

    @patch('src.research_tools.TavilyClient')
    def test_tavily_search_tool_api_error(self, mock_client_class):
        """Test Tavily search API error handling"""
        # Mock Tavily client with error
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.search.side_effect = Exception("API Error")

        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            result = tavily_search_tool("test query")

        assert len(result) == 1
        assert "error" in result[0]
        assert "API Error" in result[0]["error"]


class TestWikipediaSearchTool:
    """Test cases for the wikipedia_search_tool function"""

    @patch('src.research_tools.wikipedia.search')
    @patch('src.research_tools.wikipedia.page')
    @patch('src.research_tools.wikipedia.summary')
    def test_wikipedia_search_tool_basic_functionality(self, mock_summary, mock_page, mock_search):
        """Test basic Wikipedia search functionality"""
        # Mock Wikipedia responses
        mock_search.return_value = ["Test Topic"]
        mock_page.return_value = MagicMock()
        mock_page.return_value.title = "Test Topic"
        mock_page.return_value.url = "https://en.wikipedia.org/wiki/Test_Topic"
        mock_summary.return_value = "This is a test summary of the topic."

        result = wikipedia_search_tool("test query", sentences=3)

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Test Topic"
        assert result[0]["summary"] == "This is a test summary of the topic."
        assert result[0]["url"] == "https://en.wikipedia.org/wiki/Test_Topic"

    @patch('src.research_tools.wikipedia.search')
    def test_wikipedia_search_tool_no_results(self, mock_search):
        """Test Wikipedia search with no results"""
        mock_search.return_value = []

        result = wikipedia_search_tool("nonexistent query")

        assert len(result) == 1
        assert "error" in result[0]

    @patch('src.research_tools.wikipedia.search')
    @patch('src.research_tools.wikipedia.page')
    def test_wikipedia_search_tool_page_error(self, mock_page, mock_search):
        """Test Wikipedia search when page retrieval fails"""
        mock_search.return_value = ["Test Topic"]
        mock_page.side_effect = Exception("Page not found")

        result = wikipedia_search_tool("test query")

        assert len(result) == 1
        assert "error" in result[0]

    @patch('src.research_tools.wikipedia.search')
    @patch('src.research_tools.wikipedia.summary')
    def test_wikipedia_search_tool_summary_error(self, mock_summary, mock_search):
        """Test Wikipedia search when summary retrieval fails"""
        mock_search.return_value = ["Test Topic"]
        mock_summary.side_effect = Exception("Summary error")

        result = wikipedia_search_tool("test query")

        assert len(result) == 1
        assert "error" in result[0]


class TestToolDefinitions:
    """Test cases for tool definitions"""

    def test_arxiv_tool_definition(self):
        """Test arXiv tool definition structure"""
        assert arxiv_tool_def["type"] == "function"
        assert arxiv_tool_def["function"]["name"] == "arxiv_search_tool"
        assert "query" in arxiv_tool_def["function"]["parameters"]["properties"]
        assert arxiv_tool_def["function"]["parameters"]["required"] == ["query"]

    def test_tavily_tool_definition(self):
        """Test Tavily tool definition structure"""
        assert tavily_tool_def["type"] == "function"
        assert tavily_tool_def["function"]["name"] == "tavily_search_tool"
        assert "query" in tavily_tool_def["function"]["parameters"]["properties"]
        assert tavily_tool_def["function"]["parameters"]["required"] == ["query"]

    def test_wikipedia_tool_definition(self):
        """Test Wikipedia tool definition structure"""
        assert wikipedia_tool_def["type"] == "function"
        assert wikipedia_tool_def["function"]["name"] == "wikipedia_search_tool"
        assert "query" in wikipedia_tool_def["function"]["parameters"]["properties"]
        assert wikipedia_tool_def["function"]["parameters"]["required"] == ["query"]


class TestResearchToolsIntegration:
    """Integration tests for research tools"""

    def test_tool_consistency(self):
        """Test that all tools return consistent data structures"""
        # Mock all external dependencies
        with patch('src.research_tools.session.get') as mock_arxiv_get, \
             patch('src.research_tools.TavilyClient') as mock_tavily_client, \
             patch('src.research_tools.wikipedia.search') as mock_wiki_search, \
             patch('src.research_tools.wikipedia.page') as mock_wiki_page, \
             patch('src.research_tools.wikipedia.summary') as mock_wiki_summary, \
             patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):

            # Setup mocks
            mock_arxiv_get.return_value.content = '''<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry>
                    <title>Test Paper</title>
                    <summary>Test abstract</summary>
                    <published>2023-01-01T00:00:00Z</published>
                    <id>http://arxiv.org/abs/2301.00001</id>
                    <author><name>Test Author</name></author>
                </entry>
            </feed>'''

            mock_client = MagicMock()
            mock_tavily_client.return_value = mock_client
            mock_client.search.return_value = {
                "results": [{"title": "Web Result", "content": "Content", "url": "https://example.com"}]
            }

            mock_wiki_search.return_value = ["Test Topic"]
            mock_wiki_page.return_value = MagicMock(title="Test Topic", url="https://wikipedia.org/Test")
            mock_wiki_summary.return_value = "Test summary"

            # Test all tools
            arxiv_result = arxiv_search_tool("test")
            tavily_result = tavily_search_tool("test")
            wikipedia_result = wikipedia_search_tool("test")

            # All should return list of dicts
            assert isinstance(arxiv_result, list)
            assert isinstance(tavily_result, list)
            assert isinstance(wikipedia_result, list)

            # All should have at least one result (when successful)
            if arxiv_result and "error" not in arxiv_result[0]:
                assert isinstance(arxiv_result[0], dict)
            if tavily_result and "error" not in tavily_result[0]:
                assert isinstance(tavily_result[0], dict)
            if wikipedia_result and "error" not in wikipedia_result[0]:
                assert isinstance(wikipedia_result[0], dict)