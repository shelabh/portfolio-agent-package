# tests/test_imports.py
import pytest

def test_imports():
    from portfolio_agent import build_graph, RedisCheckpointer  # noqa: F401
    assert callable(build_graph)
    assert build_graph.__name__ == "build_graph"
