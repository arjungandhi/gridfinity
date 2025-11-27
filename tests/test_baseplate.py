import cadquery as cq
import pytest

from gridfinity import baseplate


def test_baseplate_creation():
    """Test that a baseplate can be created successfully."""
    plate = baseplate(2, 2)
    assert plate is not None
    assert isinstance(plate, cq.Workplane)


def test_baseplate_custom_thickness():
    """Test that a baseplate can be created with custom thickness."""
    plate = baseplate(1, 1, thickness=10.0)
    assert plate is not None


def test_baseplate_invalid_dimensions():
    """Test that invalid dimensions raise ValueError."""
    with pytest.raises(ValueError):
        baseplate(0, 1)

    with pytest.raises(ValueError):
        baseplate(1, 0)

    with pytest.raises(ValueError):
        baseplate(-1, 1)


def test_baseplate_invalid_thickness():
    """Test that invalid thickness raises ValueError."""
    with pytest.raises(ValueError):
        baseplate(1, 1, thickness=0)

    with pytest.raises(ValueError):
        baseplate(1, 1, thickness=-5)


def test_baseplate_export():
    """Test that a baseplate can be exported to STL."""
    import os

    plate = baseplate(2, 2)
    output_path = "outputs/test_baseplate.stl"

    os.makedirs("outputs", exist_ok=True)
    cq.exporters.export(plate, output_path)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
