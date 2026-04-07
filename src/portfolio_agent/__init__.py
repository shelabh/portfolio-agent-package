__version__ = "0.3.0rc1"

from .sdk import IngestionResult, PortfolioAgent

__all__ = ["PortfolioAgent", "IngestionResult", "create_app", "__version__"]


def __getattr__(name: str):
    if name == "create_app":
        from .api.server import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
