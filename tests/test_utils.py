# tests/test_utils.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from portfolio_agent.utils import call_openai_chat, call_vllm_chat, llm_chat, upsert_vector, nearest_neighbors

class TestLLMFunctions:
    @patch('portfolio_agent.utils.client')
    def test_call_openai_chat_success(self, mock_client):
        """Test successful OpenAI chat completion."""
        messages = [{"role": "user", "content": "Hello"}]
        
        # Mock the new OpenAI response structure
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = call_openai_chat(messages)
        assert result == "Hello! How can I help you?"
        mock_client.chat.completions.create.assert_called_once()

    @patch('portfolio_agent.utils.client')
    def test_call_openai_chat_retry(self, mock_client):
        """Test OpenAI chat with retry logic."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('portfolio_agent.utils.time.sleep'):
            # First call fails, second succeeds
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Success"
            
            mock_client.chat.completions.create.side_effect = [Exception("API Error"), mock_response]
            
            result = call_openai_chat(messages, retries=2)
            assert result == "Success"
            assert mock_client.chat.completions.create.call_count == 2

    @patch('portfolio_agent.utils.client')
    def test_call_openai_chat_max_retries(self, mock_client):
        """Test OpenAI chat with max retries exceeded."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('portfolio_agent.utils.time.sleep'):
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                call_openai_chat(messages, retries=2)
            
            assert mock_client.chat.completions.create.call_count == 2

    def test_call_vllm_chat_success(self):
        """Test successful vLLM chat completion."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('portfolio_agent.utils.requests.post') as mock_post, \
             patch('portfolio_agent.utils.settings') as mock_settings:
            
            mock_settings.VLLM_BASE_URL = 'http://localhost:8000'
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Hello from vLLM!"}}]
            }
            mock_post.return_value = mock_response
            
            result = call_vllm_chat(messages)
            assert result == "Hello from vLLM!"

    def test_call_vllm_chat_no_base_url(self):
        """Test vLLM chat with no base URL configured."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('portfolio_agent.utils.settings') as mock_settings:
            mock_settings.VLLM_BASE_URL = None
            with pytest.raises(RuntimeError):
                call_vllm_chat(messages)

    def test_llm_chat_openai_provider(self):
        """Test llm_chat with OpenAI provider."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('portfolio_agent.utils.settings') as mock_settings, \
             patch('portfolio_agent.utils.call_openai_chat') as mock_openai:
            
            mock_settings.LLM_PROVIDER = 'openai'
            mock_openai.return_value = "OpenAI response"
            result = llm_chat(messages)
            assert result == "OpenAI response"

    def test_llm_chat_vllm_provider(self):
        """Test llm_chat with vLLM provider."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('portfolio_agent.utils.settings') as mock_settings, \
             patch('portfolio_agent.utils.call_vllm_chat') as mock_vllm:
            
            mock_settings.LLM_PROVIDER = 'vllm'
            mock_vllm.return_value = "vLLM response"
            result = llm_chat(messages)
            assert result == "vLLM response"

class TestVectorFunctions:
    @patch('portfolio_agent.utils.engine')
    def test_upsert_vector_success(self, mock_engine):
        """Test successful vector upsert."""
        mock_conn = Mock()
        mock_engine.begin.return_value.__enter__.return_value = mock_conn
        
        upsert_vector("doc1", {"content": "test"}, [0.1, 0.2, 0.3])
        mock_conn.execute.assert_called_once()

    @patch('portfolio_agent.utils.engine')
    def test_upsert_vector_retry(self, mock_engine):
        """Test vector upsert with retry logic."""
        with patch('portfolio_agent.utils.time.sleep'):
            mock_conn = Mock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.side_effect = [Exception("DB Error"), None]
            
            upsert_vector("doc1", {"content": "test"}, [0.1, 0.2, 0.3], retries=2)
            assert mock_conn.execute.call_count == 2

    @patch('portfolio_agent.utils.engine')
    def test_nearest_neighbors_success(self, mock_engine):
        """Test successful vector search."""
        mock_conn = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        # Mock database rows
        mock_row = Mock()
        mock_row.id = "doc1"
        mock_row.content = "test content"
        mock_row.metadata = '{"source": "test.md"}'
        mock_row.distance = 0.1
        
        mock_conn.execute.return_value.fetchall.return_value = [mock_row]
        
        result = nearest_neighbors([0.1, 0.2, 0.3])
        assert len(result) == 1
        assert result[0]["id"] == "doc1"
        assert result[0]["content"] == "test content"

    @patch('portfolio_agent.utils.engine')
    def test_nearest_neighbors_retry(self, mock_engine):
        """Test vector search with retry logic."""
        with patch('portfolio_agent.utils.time.sleep'):
            mock_conn = Mock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            
            # First call fails, second succeeds
            mock_success_result = Mock()
            mock_success_result.fetchall.return_value = []
            mock_conn.execute.side_effect = [Exception("DB Error"), mock_success_result]
            
            result = nearest_neighbors([0.1, 0.2, 0.3], retries=2)
            assert mock_conn.execute.call_count == 2
            assert result == []