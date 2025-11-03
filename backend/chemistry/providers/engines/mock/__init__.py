"""Mock chemistry engine for testing."""

from .engine import MockChemEngine

# Create singleton instance
mock_engine = MockChemEngine()

__all__ = ["MockChemEngine", "mock_engine"]
