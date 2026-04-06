"""Deprecated graph compatibility helpers."""

import warnings

from .sdk import PortfolioAgent

def build_graph(checkpointer=None):
    """
    Build the canonical LangGraph for backwards compatibility.

    Deprecated: use PortfolioAgent for supported SDK usage.
    """
    warnings.warn(
        "build_graph() is deprecated and will be removed in a future release. "
        "Use PortfolioAgent for the supported public API.",
        DeprecationWarning,
        stacklevel=2,
    )
    agent = PortfolioAgent.from_settings()
    return agent.pipeline.graph

if __name__ == "__main__":
    graph = build_graph()
    print("Portfolio Agent graph built:", graph)
