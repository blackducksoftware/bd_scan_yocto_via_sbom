"""
pytest configuration for bd_scan_yocto_via_sbom tests.

Provides shared fixtures and path helpers for all test modules.
Standard library only — no runtime deps beyond pytest itself.
"""
import pathlib
import pytest


# Root of the repository
REPO_ROOT = pathlib.Path(__file__).parent.parent

# Common test-data paths
DATA_DIR = REPO_ROOT / "test" / "data"
VENDORED_DIR = DATA_DIR / "vendored"
BASELINE_DIR = DATA_DIR / "baseline"

RUST_DIR = VENDORED_DIR / "rust"
GO_DIR = VENDORED_DIR / "go"
NEGATIVE_DIR = VENDORED_DIR / "negative"
EXPECTED_DIR = VENDORED_DIR / "expected"


@pytest.fixture(scope="session")
def data_dir() -> pathlib.Path:
    """Path to test/data/."""
    return DATA_DIR


@pytest.fixture(scope="session")
def vendored_dir() -> pathlib.Path:
    """Path to test/data/vendored/."""
    return VENDORED_DIR


@pytest.fixture(scope="session")
def expected_dir() -> pathlib.Path:
    """Path to test/data/vendored/expected/."""
    return EXPECTED_DIR


@pytest.fixture(scope="session")
def pyruvate_crates_inc(rust_dir=RUST_DIR) -> pathlib.Path:
    """Path to python3-pyruvate-crates.inc fixture."""
    return RUST_DIR / "python3-pyruvate-crates.inc"


@pytest.fixture(scope="session")
def pydantic_core_crates_inc() -> pathlib.Path:
    """Path to python3-pydantic-core-crates.inc fixture."""
    return RUST_DIR / "python3-pydantic-core-crates.inc"


@pytest.fixture(scope="session")
def crucible_go_mods_inc() -> pathlib.Path:
    """Path to crucible-go-mods.inc fixture."""
    return GO_DIR / "crucible-go-mods.inc"


@pytest.fixture(scope="session")
def gomodgit_example_inc() -> pathlib.Path:
    """Path to gomodgit-example-synthesised.inc fixture."""
    return GO_DIR / "gomodgit-example-synthesised.inc"


@pytest.fixture(scope="session")
def zlib_bb() -> pathlib.Path:
    """Path to zlib_1.3.1.bb negative-case fixture."""
    return NEGATIVE_DIR / "zlib_1.3.1.bb"


@pytest.fixture(scope="session")
def license_manifest() -> pathlib.Path:
    """Path to the existing license.manifest test fixture."""
    return DATA_DIR / "license.manifest"
