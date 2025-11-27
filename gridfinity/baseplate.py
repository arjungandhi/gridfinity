import logging
from typing import Optional

import cadquery as cq

from gridfinity.config import GridfinityConfig

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = GridfinityConfig()


def baseplate(
    x: int = 2,
    y: int = 2,
    thickness: float = 5.0,
    config: Optional[GridfinityConfig] = None,
) -> cq.Workplane:
    """Creates a Gridfinity-compatible baseplate.

    The baseplate follows the profile of the bin base for each grid position,
    allowing bins to snap securely into place.

    Args:
        x: Number of units in X direction
        y: Number of units in Y direction
        thickness: Thickness of the baseplate in mm (default: 5.0)
        config: Custom configuration (uses defaults if None)

    Returns:
        CadQuery Workplane containing the baseplate geometry
    """
    if x < 1 or y < 1:
        raise ValueError(f"Dimensions must be positive: x={x}, y={y}")
    if thickness <= 0:
        raise ValueError(f"Thickness must be positive: {thickness}")

    cfg = config or _DEFAULT_CONFIG
    logger.info(f"Creating Gridfinity baseplate: {x}x{y} units, {thickness}mm thick")

    # Calculate overall baseplate dimensions - exactly 42mm x 42mm per unit (no tolerance)
    plate_width = x * cfg.unit_size
    plate_depth = y * cfg.unit_size

    # Create the base plate with 8mm corner radius
    result = cq.Workplane("XY").box(plate_width, plate_depth, thickness)
    result = result.edges("|Z").fillet(cfg.outer_fillet)

    # Create the base pattern that will be cut into the top of the baseplate
    base_pattern = _create_baseplate_pattern(x, y, thickness, cfg)
    result = result.cut(base_pattern)

    # Select the bottom faces of the cuts and extrude downward to remove excess material
    # This hollows out the baseplate from below
    cut_bottom_z = thickness / 2 - cfg.base_height
    bottom_faces_list = (
        result.faces()
        .filter(lambda face: abs(face.Center().z - cut_bottom_z) < 0.1)
        .vals()
    )

    # Process each face individually to avoid issues with non-planar faces
    for face in bottom_faces_list:
        result = (
            result.faces(cq.NearestToPointSelector(face.Center()))
            .wires()
            .toPending()
            .workplane()
            .cutThruAll()
        )

    logger.info("Baseplate created successfully")
    return result


def _build_profile(
    steps: tuple[tuple[float, float], ...],
    workplane: cq.Workplane,
) -> cq.Workplane:
    """Builds a 2D profile from step offsets."""
    profile = workplane.moveTo(0, 0)
    x, z = 0.0, 0.0
    for dx, dz in steps:
        x += dx
        z += dz
        profile = profile.lineTo(x, z)
    return profile.close()


def _create_baseplate_unit(thickness: float, config: GridfinityConfig) -> cq.Workplane:
    """Creates a single Gridfinity baseplate unit with the base profile.

    This creates the inverse of the bin base - a raised area that the bin base
    will fit into, following the same profile steps.
    """
    unit_size = config.unit_size - 2 * config.tolerance

    # Create the raised base unit
    base = cq.Workplane("XY").box(unit_size, unit_size, config.base_height)
    base = base.edges("+Z").fillet(config.outer_fillet)

    # Create the profile cut (same as bin base)
    base_wire = base.faces("<Z").wires(cq.selectors.LengthNthSelector(-1))
    base_vertex = base_wire.vertices(">X").vertices(">Y")
    workplane = cq.Workplane("XZ", origin=base_vertex.val().toTuple())
    profile = _build_profile(config.base_steps, workplane)
    base_cut = profile.sweep(base_wire, isFrenet=True)

    return base.cut(base_cut)


def _create_baseplate_pattern(
    x: int, y: int, thickness: float, config: GridfinityConfig
) -> cq.Workplane:
    """Creates a pattern of baseplate units.

    This reuses the same pattern logic as the bin base pattern, positioning
    base units at each grid location.
    """
    base_unit = _create_baseplate_unit(thickness, config)
    base_pattern = None

    for i in range(x):
        for j in range(y):
            x_offset = (i - (x - 1) / 2) * config.unit_size
            y_offset = (j - (y - 1) / 2) * config.unit_size
            translated_base = base_unit.translate((x_offset, y_offset, 0))

            if base_pattern is None:
                base_pattern = translated_base
            else:
                base_pattern = base_pattern.add(translated_base)

    # Position the pattern to cut into the baseplate from the top
    # Top of base units flush with top of baseplate, extending downward into it
    base_z_offset = thickness / 2 - config.base_height / 2
    return base_pattern.translate((0, 0, base_z_offset))
