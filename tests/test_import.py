import pytest

from portfolio_agent import PortfolioAgent


def test_portfolio_agent_import():
    assert PortfolioAgent is not None


def test_create_app_import_when_fastapi_available():
    pytest.importorskip("fastapi", reason="FastAPI is required for the API wrapper export")
    from portfolio_agent import create_app

    assert create_app is not None
