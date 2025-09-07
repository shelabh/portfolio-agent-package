# tests/test_tools.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from portfolio_agent.agents.tools.calendly_agent import calendly_agent
from portfolio_agent.agents.tools.email_agent import email_agent
from portfolio_agent.agents.tools.notes_agent import notes_agent

class TestCalendlyAgent:
    def test_calendly_agent_no_api_key(self):
        """Test calendly agent handles missing API key gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            state = Mock()
            state.messages = [{"role": "user", "content": "Schedule a meeting"}]
            
            result = calendly_agent(state)
            assert result.goto == "end"
            assert "not configured" in result.update["calendly_link"]

    def test_calendly_agent_with_api_key(self):
        """Test calendly agent with valid API key."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{
                "attributes": {
                    "uri": "calendly.com/user/meeting",
                    "scheduling_page_url": "https://calendly.com/user/meeting"
                }
            }]
        }
        
        with patch.dict(os.environ, {"CALENDLY_API_KEY": "test_key"}), \
             patch('portfolio_agent.agents.tools.calendly_agent.requests.get') as mock_get:
            
            mock_get.return_value = mock_response
            
            state = Mock()
            state.messages = [{"role": "user", "content": "Schedule a meeting"}]
            
            result = calendly_agent(state)
            assert result.goto == "end"
            assert "calendly.com" in result.update["calendly_link"]

    def test_calendly_agent_api_error(self):
        """Test calendly agent handles API errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.dict(os.environ, {"CALENDLY_API_KEY": "test_key"}), \
             patch('portfolio_agent.agents.tools.calendly_agent.requests.get') as mock_get:
            
            mock_get.return_value = mock_response
            
            state = Mock()
            state.messages = [{"role": "user", "content": "Schedule a meeting"}]
            
            result = calendly_agent(state)
            assert result.goto == "end"
            assert "error" in result.update["calendly_link"]

class TestEmailAgent:
    def test_email_agent_draft_only(self):
        """Test email agent drafts email without sending."""
        state = Mock()
        state.messages = [{"role": "user", "content": "Draft an email to a recruiter about my Python skills"}]
        state.allow_send = False
        
        with patch('portfolio_agent.agents.tools.email_agent.llm_chat') as mock_llm:
            mock_llm.return_value = "Dear Recruiter,\n\nI have extensive Python programming experience..."
            
            result = email_agent(state)
            assert result.goto == "end"
            assert result.update["email_sent"] == False
            assert "draft" in result.update
            assert "Python" in result.update["draft"]

    def test_email_agent_send_email(self):
        """Test email agent sends email when configured."""
        state = Mock()
        state.messages = [{"role": "user", "content": "Send email to recruiter@company.com"}]
        state.allow_send = True
        state.email_to = "recruiter@company.com"
        state.email_subject = "Job Application"
        
        with patch.dict(os.environ, {
            "EMAIL_FROM": "test@example.com",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user",
            "SMTP_PASS": "pass"
        }), \
        patch('portfolio_agent.agents.tools.email_agent.llm_chat') as mock_llm, \
        patch('portfolio_agent.agents.tools.email_agent.smtplib.SMTP') as mock_smtp:
            
            mock_llm.return_value = "Test email content"
            
            result = email_agent(state)
            assert result.goto == "end"
            assert result.update["email_sent"] == True
            assert "draft" in result.update

    def test_email_agent_no_smtp_config(self):
        """Test email agent handles missing SMTP configuration."""
        state = Mock()
        state.messages = [{"role": "user", "content": "Send email"}]
        state.allow_send = True
        
        with patch.dict(os.environ, {}, clear=True), \
             patch('portfolio_agent.agents.tools.email_agent.llm_chat') as mock_llm:
            
            mock_llm.return_value = "Test email"
            
            result = email_agent(state)
            assert result.goto == "end"
            assert result.update["email_sent"] == False

class TestNotesAgent:
    @patch('portfolio_agent.agents.tools.notes_agent.openai')
    def test_notes_agent_success(self, mock_openai):
        """Test notes agent successfully saves interaction."""
        state = Mock()
        state.__dict__ = {"final_answer": "I have Python programming skills."}
        state.user_id = "user123"
        
        with patch('portfolio_agent.agents.tools.notes_agent.upsert_vector') as mock_upsert:
            mock_openai.Embedding.create.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            
            result = notes_agent(state)
            assert result.goto == "end"
            assert "note_id" in result.update
            mock_upsert.assert_called_once()

    @patch('portfolio_agent.agents.tools.notes_agent.openai')
    def test_notes_agent_fallback_to_candidate(self, mock_openai):
        """Test notes agent uses candidate_answer when final_answer is missing."""
        state = Mock()
        state.__dict__ = {"candidate_answer": "Fallback answer"}
        state.user_id = "user123"
        
        with patch('portfolio_agent.agents.tools.notes_agent.upsert_vector') as mock_upsert:
            mock_openai.Embedding.create.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            
            result = notes_agent(state)
            assert result.goto == "end"
            assert "note_id" in result.update
            mock_upsert.assert_called_once()

    @patch('portfolio_agent.agents.tools.notes_agent.openai')
    def test_notes_agent_anonymous_user(self, mock_openai):
        """Test notes agent handles anonymous users."""
        state = Mock()
        state.__dict__ = {"final_answer": "Test answer"}
        state.user_id = None  # No user_id set
        
        with patch('portfolio_agent.agents.tools.notes_agent.upsert_vector') as mock_upsert:
            mock_openai.Embedding.create.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            
            result = notes_agent(state)
            assert result.goto == "end"
            assert "note_id" in result.update
            
            # Check that user_id defaults to "anon"
            call_args = mock_upsert.call_args
            metadata = call_args[0][1]
            assert metadata["user_id"] == "anon"