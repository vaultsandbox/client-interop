"""Pytest configuration and fixtures for interop tests."""

import json
import os
import pytest
from datetime import datetime
from dotenv import load_dotenv

from helpers.sdk_runner import get_runners, get_available_sdks, SDK, SDKRunner

# Load environment variables from .env file
load_dotenv()

# Directory for saving inbox exports
EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")

# Reference SDK for smoke tests (must be first in available SDKs priority)
REFERENCE_SDK = "go"


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--keep-inboxes",
        action="store_true",
        default=False,
        help="Don't delete inboxes after tests; save export JSON to ./exports/",
    )
    parser.addoption(
        "--level",
        action="store",
        default="standard",
        choices=["smoke", "standard", "full"],
        help="Test level: smoke (quick), standard (default), full (all permutations)",
    )


@pytest.fixture(scope="session")
def keep_inboxes(request) -> bool:
    """Whether to keep inboxes after tests."""
    return request.config.getoption("--keep-inboxes")


@pytest.fixture(scope="session")
def test_level(request) -> str:
    """Get the configured test level."""
    return request.config.getoption("--level")


def save_export(export_data: dict, test_name: str) -> str:
    """Save export data to a JSON file and return the path."""
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    filepath = os.path.join(EXPORTS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(export_data, f, indent=2)
    return filepath


@pytest.fixture(scope="session")
def runners() -> dict[SDK, SDKRunner]:
    """Get all configured SDK runners."""
    return get_runners()


@pytest.fixture(scope="session")
def available_sdks() -> list[SDK]:
    """Get list of available SDKs."""
    return get_available_sdks()


def _get_cross_sdk_pairs(sdks: list[SDK], level: str) -> list[tuple[SDK, SDK]]:
    """
    Get SDK pairs for cross-SDK tests based on test level.

    smoke:    Reference SDK imports from all others (N-1 tests)
    standard: One direction per pair, no duplicates (N*(N-1)/2 tests)
    full:     All permutations both directions (N*(N-1) tests)
    """
    if level == "smoke":
        # Reference SDK imports from all others
        ref = REFERENCE_SDK if REFERENCE_SDK in sdks else sdks[0]
        return [(creator, ref) for creator in sdks if creator != ref]

    elif level == "standard":
        # One direction per pair (alphabetically first creates)
        pairs = []
        for i, creator in enumerate(sdks):
            for importer in sdks[i + 1:]:
                pairs.append((creator, importer))
        return pairs

    else:  # full
        # All permutations
        return [(c, i) for c in sdks for i in sdks if c != i]


def _get_single_sdk_list(sdks: list[SDK], level: str) -> list[SDK]:
    """
    Get SDK list for single-SDK tests based on test level.

    smoke:    Reference SDK only (1 test)
    standard: All SDKs (N tests)
    full:     All SDKs (N tests)
    """
    if level == "smoke":
        ref = REFERENCE_SDK if REFERENCE_SDK in sdks else sdks[0]
        return [ref]
    return sdks


def pytest_generate_tests(metafunc):
    """
    Dynamically parametrize tests based on available SDKs and test level.

    Test levels control the number of SDK combinations tested:
    - smoke: Quick sanity check with minimal combinations
    - standard: Balanced coverage (default)
    - full: All permutations for comprehensive testing
    """
    sdks = get_available_sdks()
    level = metafunc.config.getoption("--level", "standard")

    # Cross-SDK tests (both creator_sdk and importer_sdk)
    if "creator_sdk" in metafunc.fixturenames and "importer_sdk" in metafunc.fixturenames:
        pairs = _get_cross_sdk_pairs(sdks, level)
        metafunc.parametrize(
            "creator_sdk,importer_sdk",
            pairs,
            ids=[f"{c}->{i}" for c, i in pairs],
            indirect=True,
        )

    # Single-SDK tests (only creator_sdk)
    elif "creator_sdk" in metafunc.fixturenames:
        filtered_sdks = _get_single_sdk_list(sdks, level)
        metafunc.parametrize(
            "creator_sdk",
            filtered_sdks,
            ids=[f"creator={s}" for s in filtered_sdks],
            indirect=True,
        )

    # Legacy: importer_sdk only (shouldn't happen, but handle it)
    elif "importer_sdk" in metafunc.fixturenames:
        filtered_sdks = _get_single_sdk_list(sdks, level)
        metafunc.parametrize(
            "importer_sdk",
            filtered_sdks,
            ids=[f"importer={s}" for s in filtered_sdks],
            indirect=True,
        )


@pytest.fixture
def creator_sdk(request, runners) -> SDKRunner:
    """Fixture for the SDK that creates the inbox."""
    sdk = request.param
    if sdk not in runners:
        pytest.skip(f"SDK {sdk} not configured")
    return runners[sdk]


@pytest.fixture
def importer_sdk(request, runners) -> SDKRunner:
    """Fixture for the SDK that imports the inbox."""
    sdk = request.param
    if sdk not in runners:
        pytest.skip(f"SDK {sdk} not configured")
    return runners[sdk]


@pytest.fixture
def any_sdk(runners) -> SDKRunner:
    """Get any available SDK runner (useful for single-SDK tests)."""
    if not runners:
        pytest.skip("No SDKs configured")
    return next(iter(runners.values()))
