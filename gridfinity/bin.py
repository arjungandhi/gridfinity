import logging
from typing import Optional

import cadquery as cq

from gridfinity.config import GridfinityConfig

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = GridfinityConfig()


def bin(
    x: int = 2,
    y: int = 2,
    z: int = 5,
    lip: bool = True,
    config: Optional[GridfinityConfig] = None,
) -> cq.Workplane:
    """Creates a Gridfinity-compatible storage bin.

    Args:
        x: Number of units in X direction
        y: Number of units in Y direction
        z: Height in units
        lip: Whether to include top lip
        config: Custom configuration (uses defaults if None)

    Returns:
        CadQuery Workplane containing the bin geometry
    """
    if x < 1 or y < 1 or z < 1:
        raise ValueError(f"Dimensions must be positive: x={x}, y={y}, z={z}")

    cfg = config or _DEFAULT_CONFIG
    logger.info(f"Creating Gridfinity bin: {x}x{y}x{z} units")

    bin_width = x * cfg.unit_size - 2 * cfg.tolerance
    bin_depth = y * cfg.unit_size - 2 * cfg.tolerance
    bin_height = z * cfg.height_unit - cfg.base_height

    result = cq.Workplane("XY").box(bin_width, bin_depth, bin_height)
    result = result.edges("+Z").fillet(cfg.outer_fillet - cfg.tolerance)

    if lip:
        lip_geometry = _create_lip(result, cfg)
        result = result.add(lip_geometry)

    base_pattern = _create_base_pattern(x, y, z, cfg)
    result = result.add(base_pattern)

    logger.info("Bin created successfully")
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


def _create_lip(bin: cq.Workplane, config: GridfinityConfig) -> cq.Workplane:
    """Creates lip geometry for a bin."""
    wire = bin.faces(">Z").wires(cq.selectors.LengthNthSelector(-1))
    vertex = wire.vertices(">X").vertices(">Y")
    workplane = cq.Workplane("XZ", origin=vertex.val().toTuple())
    profile = _build_profile(config.lip_steps, workplane)
    return profile.sweep(wire, isFrenet=True)


def _create_base_unit(config: GridfinityConfig) -> cq.Workplane:
    """Creates a single Gridfinity base unit."""
    unit_size = config.unit_size - 2 * config.tolerance

    base = cq.Workplane("XY").box(unit_size, unit_size, config.base_height)
    base = base.edges("+Z").fillet(config.outer_fillet - config.tolerance)

    base_wire = base.faces("<Z").wires(cq.selectors.LengthNthSelector(-1))
    base_vertex = base_wire.vertices(">X").vertices(">Y")
    workplane = cq.Workplane("XZ", origin=base_vertex.val().toTuple())
    profile = _build_profile(config.base_steps, workplane)
    base_cut = profile.sweep(base_wire, isFrenet=True)

    return base.cut(base_cut)


def _create_base_pattern(
    x: int, y: int, z: int, config: GridfinityConfig
) -> cq.Workplane:
    """Creates a pattern of base units."""
    base_unit = _create_base_unit(config)
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

    base_z_offset = (
        -(z * config.height_unit - config.base_height) / 2 - config.base_height / 2
    )
    return base_pattern.translate((0, 0, base_z_offset))


def lip(bin: cq.Workplane) -> cq.Workplane:
    """Adds a lip to an existing Gridfinity-compatible storage bin."""
    return _create_lip(bin, _DEFAULT_CONFIG)


def base() -> cq.Workplane:
    """Returns a single base unit for a Gridfinity-compatible storage bin."""
    return _create_base_unit(_DEFAULT_CONFIG)
