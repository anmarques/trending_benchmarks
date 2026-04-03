"""
Pytest configuration and shared fixtures for Benchmark Intelligence System tests.

This module provides common fixtures and configuration for all test suites.
"""

import pytest
import sys
import logging
from pathlib import Path

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root():
    """Return project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def ground_truth_path(project_root):
    """Return path to ground truth data"""
    return project_root / "tests" / "ground_truth" / "ground_truth.yaml"


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Return test data directory"""
    test_dir = project_root / "tests" / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


def pytest_configure(config):
    """Pytest configuration hook"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Mark integration tests
        if "end_to_end" in item.nodeid or "pipeline" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

        # Mark slow tests
        if "discovery" in item.nodeid or "extraction" in item.nodeid:
            item.add_marker(pytest.mark.slow)
