import cadquery as cq
import pytest

from gridfinity import bin


def test_bin_creation():
    """Test that a bin can be created successfully."""
    storage_bin = bin(2, 2, 5)
    assert storage_bin is not None
    assert isinstance(storage_bin, cq.Workplane)


def test_bin_custom_dimensions():
    """Test that a bin can be created with custom dimensions."""
    storage_bin = bin(3, 2, 7)
    assert storage_bin is not None


def test_bin_without_lip():
    """Test that a bin can be created without a lip."""
    storage_bin = bin(1, 1, 3, lip=False)
    assert storage_bin is not None


def test_bin_with_lip():
    """Test that a bin can be created with a lip."""
    storage_bin = bin(1, 1, 3, lip=True)
    assert storage_bin is not None


def test_bin_invalid_x_dimension():
    """Test that invalid x dimension raises ValueError."""
    with pytest.raises(ValueError):
        bin(0, 1, 1)

    with pytest.raises(ValueError):
        bin(-1, 1, 1)


def test_bin_invalid_y_dimension():
    """Test that invalid y dimension raises ValueError."""
    with pytest.raises(ValueError):
        bin(1, 0, 1)

    with pytest.raises(ValueError):
        bin(1, -1, 1)


def test_bin_invalid_z_dimension():
    """Test that invalid z dimension raises ValueError."""
    with pytest.raises(ValueError):
        bin(1, 1, 0)

    with pytest.raises(ValueError):
        bin(1, 1, -5)


def test_bin_export():
    """Test that a bin can be exported to STL."""
    import os

    storage_bin = bin(2, 2, 5)
    output_path = "outputs/test_bin.stl"

    os.makedirs("outputs", exist_ok=True)
    cq.exporters.export(storage_bin, output_path)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
