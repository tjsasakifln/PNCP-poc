"""Placeholder test to make pytest pass.

This file ensures CI pipeline passes during initial setup.
Real tests will be implemented in issue #27.
"""



def test_placeholder():
    """Placeholder test - always passes."""
    assert True


def test_structure_exists():
    """Verify basic structure is in place."""
    from pathlib import Path

    backend_dir = Path(__file__).parent.parent
    assert (backend_dir / "main.py").exists()
    assert (backend_dir / "README.md").exists()
