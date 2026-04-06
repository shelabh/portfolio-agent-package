from portfolio_agent import PortfolioAgent, create_app


def test_public_imports():
    assert PortfolioAgent is not None
    assert create_app is not None
